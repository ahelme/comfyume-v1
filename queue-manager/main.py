"""
Queue Manager - FastAPI Application
Main entrypoint for the job queue management service

Supports three inference modes:
- local: GPU on same machine, workers poll Redis queue
- redis: Remote GPU via Tailscale, workers poll Redis queue
- serverless: Direct HTTP to Verda Serverless (auto-scaling)
"""
import logging
import asyncio
import copy
import time
import uuid
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    Job, JobSubmitRequest, JobCompletionRequest, JobFailureRequest,
    JobResponse, QueueStatus, HealthCheck, JobStatus, QueueMode, JobPriority
)
from config import settings
from redis_client import RedisClient
from websocket_manager import WebSocketManager

# HTTP client for serverless mode
serverless_client: Optional[httpx.AsyncClient] = None

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
redis_client: Optional[RedisClient] = None
ws_manager: Optional[WebSocketManager] = None
app_start_time: datetime = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, ws_manager, serverless_client

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Inference mode: {settings.inference_mode}")

    redis_client = RedisClient()
    ws_manager = WebSocketManager(redis_client)

    # Initialize serverless client if needed
    if settings.inference_mode == "serverless":
        endpoint = settings.active_serverless_endpoint
        if not endpoint:
            logger.warning("No serverless endpoint configured - serverless mode will fail!")
            logger.warning("Set SERVERLESS_ENDPOINT or SERVERLESS_ENDPOINT_H200/B300 with SERVERLESS_ACTIVE")
        else:
            # Build headers with API key if configured
            headers = {}
            if settings.serverless_api_key:
                headers["Authorization"] = f"Bearer {settings.serverless_api_key}"
                logger.info("Serverless API key configured")
            else:
                logger.warning("No SERVERLESS_API_KEY configured - requests may fail!")

            serverless_client = httpx.AsyncClient(
                base_url=endpoint,
                timeout=httpx.Timeout(300.0),  # 5 min timeout for inference
                headers=headers
            )
            logger.info(f"Serverless client initialized: {endpoint}")
            logger.info(f"Active GPU: {settings.active_gpu_type}")
            delivery = "SFS (prefix injection)" if settings.sfs_delivery_enabled else "HTTP (history polling)"
            logger.info(f"Delivery mode: {delivery}")

    # Start background tasks
    asyncio.create_task(cleanup_task())

    logger.info("Queue Manager started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Queue Manager")
    if serverless_client:
        await serverless_client.aclose()


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS middleware - Security: Only allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aiworkshop.art",
        "https://staging.aiworkshop.art",
        "https://testing.aiworkshop.art",
        "https://anegg.app",  # Testing instance 009 (harmless in prod — CORS only allows, never blocks)
        "http://localhost:8080",  # Local admin dashboard testing
    ],
    allow_credentials=False,  # Disabled for security - no cookies needed
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheck)
@app.get("/api/health", response_model=HealthCheck, include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now(timezone.utc) - app_start_time).total_seconds()

    # Get active endpoint for serverless mode (redact full URL for security)
    endpoint_display = None
    if settings.inference_mode == "serverless" and settings.active_serverless_endpoint:
        # Show just the deployment name, not full URL
        endpoint = settings.active_serverless_endpoint
        endpoint_display = endpoint.split("//")[-1].split(".")[0] if "//" in endpoint else endpoint

    return HealthCheck(
        status="healthy" if redis_client.ping() else "unhealthy",
        version=settings.app_version,
        inference_mode=settings.inference_mode,
        active_gpu=settings.active_gpu_type,
        serverless_endpoint=endpoint_display,
        redis_connected=redis_client.ping(),
        workers_active=0,  # TODO: Track active workers
        queue_depth=redis_client.get_queue_depth(),
        uptime_seconds=int(uptime)
    )


@app.get("/api/queue/status", response_model=QueueStatus)
async def get_queue_status():
    """Get overall queue status - optimized with batched Redis calls"""
    try:
        # Performance: Get all queue stats in single pipeline call (4→1 Redis commands)
        stats = redis_client.get_all_queue_stats()

        return QueueStatus(
            mode=QueueMode(settings.queue_mode),
            pending_jobs=stats["pending"],
            running_jobs=stats["running"],
            completed_jobs=stats["completed"],
            failed_jobs=stats["failed"],
            total_workers=settings.num_workers,
            active_workers=0,  # TODO: Implement worker tracking
            queue_depth=stats["pending"]
        )
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Job Management Endpoints
# ============================================================================

# Output node types whose filename_prefix we inject for SFS-based delivery.
# All of these store results via ComfyUI's get_save_image_path() in folder_paths.py.
OUTPUT_NODE_TYPES = {"SaveImage", "SaveAnimatedWEBP", "SaveAnimatedPNG", "SaveVideo", "VHS_VideoCombine"}


def extract_save_node_ids(workflow: dict) -> list:
    """Extract node IDs that have output-type class_type (SaveImage, SaveVideo, etc.)"""
    save_ids = []
    for node_id, node_data in workflow.items():
        class_type = node_data.get("class_type", "")
        if class_type in OUTPUT_NODE_TYPES:
            save_ids.append(node_id)
    return save_ids


def inject_output_prefix(workflow: dict, prefix: str) -> dict:
    """Deep-copy workflow and inject filename_prefix into all output nodes.

    Strips directory component from original prefix (e.g. "video/LTX-2" → prefix)
    so all outputs land in SFS root. QM scans one flat directory.
    """
    modified = copy.deepcopy(workflow)
    for node_id, node_data in modified.items():
        class_type = node_data.get("class_type", "")
        if class_type in OUTPUT_NODE_TYPES:
            if "inputs" not in node_data:
                node_data["inputs"] = {}
            node_data["inputs"]["filename_prefix"] = prefix
    return modified


def snapshot_sfs_directory(sfs_dir: Path) -> set:
    """Return set of filenames currently in SFS output directory.

    NFS-safe: uses Path.iterdir() which maps to readdir(), not inotify.
    Propagates OSError so callers can handle retries.
    """
    return {f.name for f in sfs_dir.iterdir() if f.is_file()}


async def watch_sfs_for_outputs(
    prefix: str,
    save_node_ids: list,
    user_id: str,
    baseline: set,
    sfs_dir: Path,
    max_wait: int,
    poll_interval: float,
    settle_time: float,
) -> dict:
    """Poll SFS directory for files matching our injected prefix.

    Returns synthetic history entry compatible with fetch_serverless_images().
    """
    start = time.monotonic()
    poll_count = 0
    first_match_time = None
    matched_files = set()

    while (time.monotonic() - start) < max_wait:
        poll_count += 1
        elapsed = time.monotonic() - start

        try:
            current = snapshot_sfs_directory(sfs_dir)
        except Exception as e:
            if poll_count <= 10:
                logger.warning(f"SFS scan error (attempt {poll_count}): {e}")
                await asyncio.sleep(poll_interval)
                continue
            raise HTTPException(
                status_code=503,
                detail=f"SFS inaccessible after {poll_count} retries: {e}",
            )

        new_files = current - baseline
        prefix_matches = {f for f in new_files if f.startswith(prefix)}

        if prefix_matches:
            matched_files = prefix_matches
            if first_match_time is None:
                first_match_time = time.monotonic()
                logger.info(
                    f"SFS watch: first match after {elapsed:.0f}s ({poll_count} polls): "
                    f"{sorted(prefix_matches)[:5]}"
                )

            # Settle: wait for additional files (multi-image workflows)
            if (time.monotonic() - first_match_time) >= settle_time:
                logger.info(
                    f"SFS watch: settled with {len(matched_files)} file(s) after "
                    f"{elapsed:.0f}s ({poll_count} polls)"
                )
                return build_synthetic_outputs(sorted(matched_files), save_node_ids)

        # Log periodically
        if poll_count <= 3 or poll_count % 20 == 0:
            logger.info(
                f"SFS watch #{poll_count} ({elapsed:.0f}s): "
                f"{len(new_files)} new files, {len(matched_files)} matched"
            )

        await asyncio.sleep(poll_interval)

    # Timeout
    elapsed = time.monotonic() - start
    if matched_files:
        # Got some files but settle didn't complete — use what we have
        logger.warning(
            f"SFS watch: timeout with {len(matched_files)} partial file(s) after {elapsed:.0f}s"
        )
        return build_synthetic_outputs(sorted(matched_files), save_node_ids)

    raise HTTPException(
        status_code=504,
        detail=f"No output files found on SFS after {max_wait}s ({poll_count} polls). "
        f"Prefix: {prefix}",
    )


def build_synthetic_outputs(new_files: list, save_node_ids: list) -> dict:
    """Build ComfyUI-compatible output metadata from SFS filenames.

    Maps files to node IDs. Single save node (common case): all files go to it.
    Multiple save nodes: round-robin assignment.
    """
    outputs = {}

    if not save_node_ids:
        save_node_ids = ["output_0"]

    for i, filename in enumerate(new_files):
        node_id = save_node_ids[i % len(save_node_ids)]
        if node_id not in outputs:
            outputs[node_id] = {"images": []}
        outputs[node_id]["images"].append({
            "filename": filename,
            "subfolder": "",
            "type": "output",
        })

    return {
        "outputs": outputs,
        "status": {"status_str": "success", "completed": True},
    }


async def poll_serverless_history(prompt_id: str, max_wait: int = 600, poll_interval: float = 2.0) -> dict:
    """Poll serverless /api/history/{prompt_id} until execution completes.

    HTTP fallback — used only when SFS_DELIVERY_ENABLED=false.

    Serverless cold start + model loading can block HTTP for 200+ seconds.
    With 10s per-poll timeout, we fail fast and retry often.
    max_wait=600 covers worst case: cold start + model load + inference.

    Early bail: if the server is responding (HTTP 200) but prompt_id never
    appears in history after 120s, it's likely a load balancer routing issue
    (GETs hitting a different container than the POST). Bail early instead
    of waiting the full 600s.
    """
    if not serverless_client:
        raise HTTPException(status_code=503, detail="Serverless client not initialized")

    start_time = time.monotonic()
    poll_count = 0
    empty_200_count = 0  # HTTP 200 responses where prompt_id not in history
    MAX_EMPTY_200 = 60   # ~120s at 2s interval — bail if prompt never appears

    while (time.monotonic() - start_time) < max_wait:
        poll_count += 1
        elapsed = time.monotonic() - start_time
        try:
            # 10s timeout: fail fast when server is blocked by model loading
            response = await serverless_client.get(
                f"/history/{prompt_id}",
                timeout=httpx.Timeout(10.0),
            )
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    # Found — reset empty counter, process result
                    empty_200_count = 0
                    entry = history[prompt_id]
                    status = entry.get("status", {})
                    completed = status.get("completed", False)
                    status_str = status.get("status_str", "unknown")

                    # Always log when found in history (important for debugging)
                    if poll_count <= 5 or poll_count % 15 == 0 or completed:
                        outputs = entry.get("outputs", {})
                        output_summary = {
                            nid: list(nout.keys()) for nid, nout in outputs.items()
                        }
                        logger.info(
                            f"History poll #{poll_count} ({elapsed:.0f}s): "
                            f"completed={completed}, status={status_str}, "
                            f"outputs={output_summary}"
                        )
                    elif poll_count % 10 == 0:
                        logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): completed={completed}, status={status_str}")

                    if status_str == "error":
                        import json
                        messages = status.get("messages", [])
                        logger.error(
                            f"Serverless execution FAILED for {prompt_id} after {elapsed:.0f}s ({poll_count} polls): "
                            f"status={json.dumps(status, default=str)[:1000]}"
                        )
                        for msg in messages:
                            logger.error(f"  Error message: {json.dumps(msg, default=str)[:500]}")
                        return entry

                    if completed:
                        logger.info(f"Execution completed after {elapsed:.0f}s ({poll_count} polls)")
                        return entry
                else:
                    empty_200_count += 1
                    if poll_count <= 3 or poll_count % 30 == 0:
                        logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): prompt_id not in history. Keys: {list(history.keys())[:5]}")

                    # Early bail: server is responding but prompt never appeared
                    if empty_200_count >= MAX_EMPTY_200:
                        logger.error(
                            f"Early bail: {empty_200_count} consecutive HTTP 200 responses with empty history "
                            f"after {elapsed:.0f}s ({poll_count} polls). "
                            f"Likely load balancer routing issue — GET /history hitting different container than POST /prompt."
                        )
                        raise HTTPException(
                            status_code=502,
                            detail=f"Serverless routing error: prompt accepted but never appeared in history after {elapsed:.0f}s. "
                            f"Load balancer may be routing requests to different container instances."
                        )
            else:
                logger.warning(f"History poll #{poll_count} ({elapsed:.0f}s): HTTP {response.status_code}")
        except httpx.TimeoutException:
            # Only log periodically — timeout is expected during model loading
            if poll_count <= 2 or poll_count % 10 == 0:
                logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): timeout (server busy, likely loading model)")
        except HTTPException:
            raise  # Re-raise early bail
        except Exception as e:
            logger.warning(f"History poll #{poll_count} ({elapsed:.0f}s): error: {type(e).__name__}: {e}")

        await asyncio.sleep(poll_interval)

    raise HTTPException(status_code=504, detail=f"Serverless execution timed out after {max_wait}s ({poll_count} polls)")


async def fetch_serverless_images(history_entry: dict, user_id: str) -> dict:
    """Copy output images from SFS to user's local output directory.

    Reads files from /mnt/sfs/outputs/ (shared NFS mount) and copies them
    to /outputs/{user_id}/ where the frontend serves them.

    Returns ComfyUI-compatible output metadata: {node_id: {images: [...]}}
    """
    import shutil

    outputs = history_entry.get("outputs", {})

    if not outputs:
        logger.warning(f"History entry has no outputs. Top-level keys: {list(history_entry.keys())}")
        return {}

    # Prepare local output directory for this user
    local_output_dir = Path(settings.outputs_path) / user_id
    local_output_dir.mkdir(parents=True, exist_ok=True)

    saved_outputs = {}
    sfs_output_dir = Path(settings.sfs_output_dir)

    for node_id, node_output in outputs.items():
        img_list = node_output.get("images", [])
        logger.info(f"Output node {node_id}: {len(img_list)} image(s), keys={list(node_output.keys())}")

        for img_info in img_list:
            filename = img_info.get("filename")
            subfolder = img_info.get("subfolder", "")
            if not filename:
                continue

            # Read from SFS (shared NFS between serverless + app server)
            sfs_path = sfs_output_dir / subfolder / filename if subfolder else sfs_output_dir / filename
            if sfs_path.exists():
                dest = local_output_dir / filename
                shutil.copy2(str(sfs_path), str(dest))
                logger.info(f"SFS copy: {sfs_path} -> {dest} ({dest.stat().st_size} bytes)")

                if node_id not in saved_outputs:
                    saved_outputs[node_id] = {"images": []}
                saved_outputs[node_id]["images"].append({
                    "filename": filename,
                    "subfolder": user_id,
                    "type": "output",
                })
            else:
                logger.error(f"SFS file not found: {sfs_path}")

    return saved_outputs


async def submit_to_serverless(workflow: dict, user_id: str) -> dict:
    """Submit workflow to serverless, wait for completion, fetch and save output images.

    Two delivery modes controlled by SFS_DELIVERY_ENABLED:
    - SFS (default): inject unique prefix, POST, poll SFS for matching files.
      Fixes load-balancer routing issue (#66, #74, #82).
    - HTTP (fallback): POST, poll /history, copy from SFS. Broken with
      load-balanced serverless but kept for debugging/local testing.
    """
    if not serverless_client:
        raise HTTPException(
            status_code=503,
            detail="Serverless client not initialized. Check SERVERLESS_ENDPOINT."
        )

    try:
        if settings.sfs_delivery_enabled:
            return await _submit_with_sfs_delivery(workflow, user_id)
        return await _submit_with_http_delivery(workflow, user_id)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Serverless inference timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"Serverless response body: {e.response.text[:500]}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Serverless submission failed: {e}")
        raise HTTPException(status_code=502, detail=f"Serverless error: {e}")


async def _submit_with_sfs_delivery(workflow: dict, user_id: str) -> dict:
    """SFS-based delivery: inject prefix, POST, poll SFS for output files."""
    sfs_dir = Path(settings.sfs_output_dir)

    # Verify SFS is accessible
    if not sfs_dir.is_dir():
        logger.error(f"SFS output directory not accessible: {sfs_dir}")
        raise HTTPException(
            status_code=503,
            detail=f"SFS output directory not accessible: {sfs_dir}",
        )

    # 1. Generate unique job prefix
    job_id = uuid.uuid4().hex[:8]
    prefix = f"comfyume_{job_id}"

    # 2. Extract save node IDs and inject prefix into workflow copy
    save_node_ids = extract_save_node_ids(workflow)
    modified_workflow = inject_output_prefix(workflow, prefix)
    logger.info(f"SFS delivery: job={job_id}, prefix={prefix}, save_nodes={save_node_ids}")

    # 3. Snapshot SFS before submission (baseline for diff)
    baseline = snapshot_sfs_directory(sfs_dir)

    # 4. POST modified workflow to serverless
    logger.info(f"Sending to serverless: {len(workflow)} nodes (SFS delivery)")
    response = await serverless_client.post(
        "/prompt",
        json={"prompt": modified_workflow, "client_id": user_id},
    )
    response.raise_for_status()
    result = response.json()
    prompt_id = result.get("prompt_id")
    logger.info(f"Serverless prompt accepted: {prompt_id} (prefix: {prefix})")

    if not prompt_id:
        logger.error(f"No prompt_id in serverless response: {result}")
        return result

    # Check for immediate node errors in POST response
    if result.get("node_errors"):
        logger.error(f"Serverless node errors: {result['node_errors']}")
        result["execution_error"] = result["node_errors"]
        return result

    # 5. Watch SFS for output files matching our prefix
    history_entry = await watch_sfs_for_outputs(
        prefix=prefix,
        save_node_ids=save_node_ids,
        user_id=user_id,
        baseline=baseline,
        sfs_dir=sfs_dir,
        max_wait=settings.sfs_max_wait,
        poll_interval=settings.sfs_poll_interval,
        settle_time=settings.sfs_settle_time,
    )

    # 6. Copy files from SFS to user's local output directory
    saved_outputs = await fetch_serverless_images(history_entry, user_id)

    if not saved_outputs:
        logger.warning(f"No images saved for {prompt_id} (prefix: {prefix})")
        result["outputs"] = history_entry.get("outputs", {})
        return result

    logger.info(f"SFS delivery complete: {len(saved_outputs)} node(s), job={job_id}")
    result["outputs"] = saved_outputs
    result["execution_status"] = "success"
    return result


async def _submit_with_http_delivery(workflow: dict, user_id: str) -> dict:
    """HTTP-based delivery (fallback): POST, poll /history, copy from SFS.

    Known limitation: load-balanced serverless routes GET /history to different
    container than POST /prompt, causing early bail. Use SFS delivery instead.
    """
    # 1. Submit prompt to serverless ComfyUI
    logger.info(f"Sending to serverless: {len(workflow)} nodes (HTTP delivery)")
    response = await serverless_client.post(
        "/prompt",
        json={"prompt": workflow, "client_id": user_id},
    )
    response.raise_for_status()
    result = response.json()
    prompt_id = result.get("prompt_id")
    logger.info(f"Serverless prompt accepted: {prompt_id}")

    if not prompt_id:
        logger.error(f"No prompt_id in serverless response: {result}")
        return result

    # 2. Poll history until execution completes
    logger.info(f"Polling for execution completion: {prompt_id}")
    history_entry = await poll_serverless_history(prompt_id)

    status = history_entry.get("status", {})
    if status.get("status_str") != "success":
        messages = status.get("messages", [])
        logger.error(f"Execution failed: {messages}")
        result["execution_error"] = messages
        return result

    logger.info(f"Execution completed successfully: {prompt_id}")

    # 3. Copy output images from SFS
    saved_outputs = await fetch_serverless_images(history_entry, user_id)

    if not saved_outputs:
        logger.warning(f"No images saved for {prompt_id}")
        result["outputs"] = history_entry.get("outputs", {})
        return result

    logger.info(f"Saved outputs for {len(saved_outputs)} node(s)")
    result["outputs"] = saved_outputs
    result["execution_status"] = "success"
    return result


@app.post("/api/jobs", response_model=JobResponse, status_code=201)
async def submit_job(request: JobSubmitRequest):
    """Submit a new job - routes based on INFERENCE_MODE"""
    try:
        # SERVERLESS MODE: Direct HTTP to serverless endpoint (no queue)
        if settings.inference_mode == "serverless":
            logger.info(f"Serverless job from user {request.user_id}")

            # Submit directly to serverless
            result = await submit_to_serverless(request.workflow, request.user_id)

            # Create a completed job record
            job = Job(
                user_id=request.user_id,
                workflow=request.workflow,
                priority=request.priority,
                metadata=request.metadata
            )
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now(timezone.utc)

            return JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                priority=job.priority,
                created_at=job.created_at,
                started_at=job.created_at,
                completed_at=job.completed_at,
                worker_id="serverless",
                result=result,
                error=None,
                position_in_queue=None
            )

        # LOCAL/REDIS MODE: Queue-based (workers poll for jobs)
        # Check queue depth limit
        if settings.max_queue_depth > 0:
            current_depth = redis_client.get_queue_depth()
            if current_depth >= settings.max_queue_depth:
                raise HTTPException(
                    status_code=429,
                    detail=f"Queue is full (max depth: {settings.max_queue_depth})"
                )

        # Create job
        job = Job(
            user_id=request.user_id,
            workflow=request.workflow,
            priority=request.priority,
            metadata=request.metadata
        )

        # Save to Redis
        if not redis_client.create_job(job):
            raise HTTPException(status_code=500, detail="Failed to create job")

        # Get queue position
        pending_jobs = redis_client.get_pending_jobs()
        position = next((i for i, j in enumerate(pending_jobs) if j.id == job.id), None)

        logger.info(f"Job {job.id} submitted by user {job.user_id} (mode: {settings.inference_mode})")

        return JobResponse(
            id=job.id,
            user_id=job.user_id,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            started_at=None,
            completed_at=None,
            worker_id=None,
            result=None,
            error=None,
            position_in_queue=position
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status by ID"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Calculate position in queue if pending
        position = None
        if job.status == JobStatus.PENDING:
            pending_jobs = redis_client.get_pending_jobs()
            position = next((i for i, j in enumerate(pending_jobs) if j.id == job_id), None)

        return JobResponse(
            id=job.id,
            user_id=job.user_id,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            worker_id=job.worker_id,
            result=job.result,
            error=job.error,
            position_in_queue=position
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    user_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    limit: int = 100
):
    """List jobs with optional filters"""
    try:
        if user_id:
            jobs = redis_client.get_user_jobs(user_id)
        else:
            # Get from all queues
            jobs = redis_client.get_pending_jobs(limit)
            # TODO: Add running, completed, failed

        # Filter by status if specified
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Performance: Cache position lookup to avoid O(n²) - fetch once, not per job
        pending_jobs = redis_client.get_pending_jobs()
        job_positions = {j.id: i for i, j in enumerate(pending_jobs)}

        # Convert to response models
        responses = []
        for job in jobs[:limit]:
            # O(1) lookup instead of O(n) search
            position = job_positions.get(job.id) if job.status == JobStatus.PENDING else None

            responses.append(JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                priority=job.priority,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                worker_id=job.worker_id,
                result=job.result,
                error=job.error,
                position_in_queue=position
            ))

        return responses

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    """Cancel a job"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status == JobStatus.RUNNING:
            # Mark as cancelled, worker will handle cleanup
            job.status = JobStatus.CANCELLED
            redis_client.update_job(job)
            logger.info(f"Job {job_id} marked for cancellation")
        elif job.status == JobStatus.PENDING:
            # Remove from queue
            redis_client.delete_job(job_id)
            logger.info(f"Job {job_id} cancelled and removed from queue")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job in {job.status} state"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.patch("/api/jobs/{job_id}/priority")
async def update_job_priority(job_id: str, priority: JobPriority):
    """Update job priority (admin/instructor only)"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change priority of {job.status} job"
            )

        # Update priority
        job.priority = priority
        redis_client.update_job(job)

        # Re-score in queue
        score = redis_client._get_priority_score(job)
        redis_client.redis.zadd(redis_client.QUEUE_PENDING, {job_id: score})

        logger.info(f"Updated job {job_id} priority to {priority}")

        return {"status": "success", "job_id": job_id, "priority": priority}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id} priority: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# Worker Endpoints
# ============================================================================

@app.get("/api/workers/next-job")
async def get_next_job(worker_id: str):
    """Get next job for worker to process"""
    try:
        # Update worker heartbeat
        redis_client.update_worker_heartbeat(worker_id)

        # Get next job based on queue mode
        queue_mode = QueueMode(settings.queue_mode)
        job = redis_client.get_next_job(queue_mode)

        if not job:
            return {"job": None}

        # Move to running
        redis_client.move_job_to_running(job.id, worker_id)

        logger.info(f"Assigned job {job.id} to worker {worker_id}")

        return {
            "job": {
                "id": job.id,
                "workflow": job.workflow,
                "user_id": job.user_id,
                "metadata": job.metadata
            }
        }

    except Exception as e:
        logger.error(f"Failed to get next job for worker {worker_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/workers/complete-job")
async def complete_job(job_id: str, request: JobCompletionRequest):
    """Mark job as completed - with validated result payload"""
    try:
        # Validation happens automatically via Pydantic model
        if not redis_client.move_job_to_completed(job_id, request.result):
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Job {job_id} completed successfully")
        return {"status": "success", "job_id": job_id}

    except HTTPException:
        raise
    except ValueError as e:
        # Pydantic validation error
        logger.warning(f"Invalid result payload for job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/workers/fail-job")
async def fail_job(job_id: str, request: JobFailureRequest):
    """Mark job as failed - with validated error message"""
    try:
        # Validation happens automatically via Pydantic model
        if not redis_client.move_job_to_failed(job_id, request.error):
            raise HTTPException(status_code=404, detail="Job not found")

        logger.error(f"Job {job_id} failed: {request.error}")
        return {"status": "success", "job_id": job_id}

    except HTTPException:
        raise
    except ValueError as e:
        # Pydantic validation error
        logger.warning(f"Invalid error message for job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(f"pong: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


# ============================================================================
# Background Tasks
# ============================================================================

async def cleanup_task():
    """Background task to cleanup stale jobs"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            redis_client.cleanup_stale_jobs(settings.job_timeout)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Log full traceback with request context for debugging
    logger.exception(
        f"Unhandled exception in {request.method} {request.url.path}: {exc}"
    )

    # Show detailed error in development mode for faster debugging
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method
            }
        )

    # Generic response in production (security best practice)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
