"""
Serverless Proxy Extension — ComfyuME

Patches ComfyUI's PromptExecutor.execute() to proxy workflow execution to
a serverless GPU via the Queue Manager, instead of executing locally on CPU.

This gives users the native ComfyUI experience (queue, progress, history,
output sidebar) while actual GPU work happens on remote serverless containers.

Activated only when INFERENCE_MODE=serverless (checked at import time).
In local/redis modes, this extension is a no-op.
"""
import os
import json
import logging
import urllib.request
import urllib.error
import threading
import time

logger = logging.getLogger("comfyume.serverless_proxy")

INFERENCE_MODE = os.environ.get("INFERENCE_MODE", "local")
QUEUE_MANAGER_URL = os.environ.get("QUEUE_MANAGER_URL", "http://queue-manager:3000")
USER_ID = os.environ.get("USER_ID", "unknown")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def _apply_execution_patch():
    """Monkey-patch PromptExecutor.execute() to proxy to serverless via QM."""
    try:
        import execution
        import server
    except ImportError:
        logger.error("Cannot import execution/server modules — patch not applied")
        return

    _original_execute = execution.PromptExecutor.execute

    def proxy_execute(self, prompt, prompt_id, extra_data={}, execute_outputs=[]):
        """
        Replace local execution with serverless proxy via Queue Manager.

        Flow:
        1. Send execution_start WebSocket message (native queue UI responds)
        2. POST workflow to QM /api/jobs (QM forwards to serverless, polls, fetches images)
        3. Parse response for output image metadata
        4. Send executed/execution_complete WebSocket messages
        5. Register outputs in ComfyUI's internal state
        """
        prompt_server = server.PromptServer.instance

        # Notify frontend: execution starting
        prompt_server.send_sync("execution_start", {"prompt_id": prompt_id})

        # Send "executing" for the first node (UI shows activity)
        node_ids = list(prompt.keys())
        if node_ids:
            prompt_server.send_sync("executing", {
                "node": node_ids[0],
                "prompt_id": prompt_id,
            })

        # Periodic heartbeat: send "executing" messages every 5s to keep the UI alive
        # while the QM blocks waiting for serverless inference (30-120s).
        heartbeat_active = threading.Event()
        heartbeat_active.set()

        def heartbeat():
            idx = 0
            while heartbeat_active.is_set():
                time.sleep(5)
                if heartbeat_active.is_set() and node_ids:
                    prompt_server.send_sync("executing", {
                        "node": node_ids[idx % len(node_ids)],
                        "prompt_id": prompt_id,
                    })
                    idx += 1

        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()

        try:
            # Submit workflow to QM (blocks until serverless returns with images)
            payload = json.dumps({
                "user_id": USER_ID,
                "workflow": prompt,
                "priority": 1,
                "metadata": {
                    "prompt_id": prompt_id,
                    "source": "serverless_proxy",
                },
            }).encode()

            req = urllib.request.Request(
                f"{QUEUE_MANAGER_URL}/api/jobs",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            logger.info(f"Proxying execution to QM: {prompt_id} ({len(prompt)} nodes)")
            # 600s timeout: cold start (60-210s) + model load (60-180s) + inference (10-60s)
            response = urllib.request.urlopen(req, timeout=600)
            result = json.loads(response.read())
            logger.info(f"QM response: status={result.get('status')}, has_result={bool(result.get('result'))}")
            if result.get("result"):
                qm_outputs = result["result"].get("outputs", {})
                logger.info(f"QM result: execution_status={result['result'].get('execution_status')}, output_nodes={list(qm_outputs.keys())}")

            # Stop heartbeat
            heartbeat_active.clear()

            # Extract outputs from QM response
            # QM returns JobResponse with result.outputs containing saved image metadata
            qm_result = result.get("result", {})

            # Check for execution errors from QM (serverless worker failed)
            if isinstance(qm_result, dict) and qm_result.get("execution_error"):
                error_messages = qm_result["execution_error"]
                error_str = str(error_messages)[:500]
                logger.error(f"Serverless execution error for {prompt_id}: {error_str}")

                prompt_server.send_sync("execution_error", {
                    "prompt_id": prompt_id,
                    "node_id": "",
                    "node_type": "ServerlessWorker",
                    "exception_type": "ServerlessExecutionError",
                    "exception_message": f"GPU worker failed: {error_str}",
                    "traceback": [f"GPU worker execution error: {error_str}"],
                })
                prompt_server.send_sync("executing", {
                    "node": None,
                    "prompt_id": prompt_id,
                })

                self.outputs_ui = {}
                self.history_result = {"outputs": {}, "meta": {}}
                self.success = False
                self.status_messages = [
                    ("execution_start", {"prompt_id": prompt_id}),
                    ("execution_error", {
                        "exception_type": "ServerlessExecutionError",
                        "exception_message": error_str,
                    }),
                ]
                return

            outputs = {}
            if isinstance(qm_result, dict):
                outputs = qm_result.get("outputs", {})

            # Send "executed" for each output node (triggers image preview in UI)
            for node_id, node_output in outputs.items():
                prompt_server.send_sync("executed", {
                    "node": node_id,
                    "output": node_output,
                    "prompt_id": prompt_id,
                })

            # Signal execution finished (node=None means "done")
            prompt_server.send_sync("executing", {
                "node": None,
                "prompt_id": prompt_id,
            })

            # Set internal state for ComfyUI's post-execution handling
            # history_result is read by prompt_worker in main.py after execute() returns
            self.outputs_ui = outputs
            self.history_result = {"outputs": outputs, "meta": {}}
            self.success = True
            self.status_messages = [
                ("execution_start", {"prompt_id": prompt_id}),
                ("execution_complete", {}),
            ]

            logger.info(f"Proxy execution complete: {prompt_id}, {len(outputs)} output node(s)")

        except Exception as e:
            heartbeat_active.clear()
            logger.error(f"Proxy execution failed: {prompt_id}: {e}")

            prompt_server.send_sync("execution_error", {
                "prompt_id": prompt_id,
                "node_id": "",
                "node_type": "ServerlessProxy",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "traceback": [str(e)],
            })
            prompt_server.send_sync("executing", {
                "node": None,
                "prompt_id": prompt_id,
            })

            self.outputs_ui = {}
            self.history_result = {"outputs": {}, "meta": {}}
            self.success = False
            self.status_messages = [
                ("execution_start", {"prompt_id": prompt_id}),
                ("execution_error", {
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                }),
            ]

    # Apply the patch
    execution.PromptExecutor.execute = proxy_execute
    logger.info("PromptExecutor.execute() patched for serverless proxy")


# Only activate in serverless mode
if INFERENCE_MODE == "serverless":
    logger.info(f"Serverless proxy activating (QM: {QUEUE_MANAGER_URL}, user: {USER_ID})")
    _apply_execution_patch()
else:
    logger.info(f"Serverless proxy inactive (INFERENCE_MODE={INFERENCE_MODE})")
