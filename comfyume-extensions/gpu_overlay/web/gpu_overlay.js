/**
 * GPU Overlay Extension — ComfyuME
 *
 * Two display modes (set via localStorage):
 *   "user"  — simple progress messages (default)
 *   "admin" — detailed technical info (prompt_id, heartbeats, errors)
 *
 * Toggle: localStorage.setItem('gpu_overlay_mode', 'admin')
 *         localStorage.setItem('gpu_overlay_mode', 'user')
 *
 * Listens for WebSocket events from serverless_proxy:
 *   execution_start    → job submitted
 *   comfyume_progress  → detailed phase updates
 *   executed           → output ready
 *   execution_error    → failure details (shown in overlay, not just dialog)
 *
 * Only active in serverless mode.
 * Requires: status_banner extension (window.comfyumeStatus).
 */
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfy.gpuOverlay",

    async setup() {
        // Only activate in serverless mode
        let inferenceMode = 'local';
        let activeGpu = '';
        let serverlessEndpoint = '';
        try {
            const health = await fetch('/api/health');
            if (health.ok) {
                const data = await health.json();
                inferenceMode = data.inference_mode || 'local';
                activeGpu = data.active_gpu || '';
                serverlessEndpoint = data.serverless_endpoint || '';
            }
        } catch (e) {
            // Can't reach QM
        }

        if (inferenceMode !== 'serverless') {
            console.log("[GPUOverlay] Inactive (non-serverless mode)");
            return;
        }

        if (!window.comfyumeStatus) {
            console.warn("[GPUOverlay] status_banner not loaded — banner will not show");
            return;
        }

        const mode = () => localStorage.getItem('gpu_overlay_mode') || 'user';
        const status = window.comfyumeStatus;
        let timer = null;
        let startTime = null;
        let promptId = '';
        let lastHeartbeat = 0;

        console.log(`[GPUOverlay] Active — mode: ${mode()}, GPU: ${activeGpu}, endpoint: ${serverlessEndpoint}`);

        // --- execution_start: job submitted ---
        app.api.addEventListener("execution_start", (evt) => {
            startTime = Date.now();
            promptId = evt?.detail?.prompt_id || '';
            lastHeartbeat = 0;

            if (mode() === 'admin') {
                const short = promptId.slice(0, 8);
                status.show(`GPU [${activeGpu}] ${short} | submitted`, '#4fc3f7');
            } else {
                status.show('Sending to GPU...', '#4fc3f7');
            }

            timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                if (mode() === 'admin') {
                    const short = promptId.slice(0, 8);
                    const hb = lastHeartbeat ? ` | hb #${lastHeartbeat}` : '';
                    status.show(
                        `GPU [${activeGpu}] ${short} | waiting${hb} | ${elapsed}s`,
                        '#ffb74d'
                    );
                } else {
                    status.show(`Processing on GPU... ${elapsed}s`, '#ffb74d');
                }
            }, 1000);
        });

        // --- comfyume_progress: detailed phase updates ---
        app.api.addEventListener("comfyume_progress", (evt) => {
            const d = evt?.detail || {};
            const short = (d.prompt_id || '').slice(0, 8);

            switch (d.phase) {
                case 'submitting':
                    if (mode() === 'admin') {
                        status.show(
                            `GPU [${activeGpu}] ${short} | ${d.node_count} nodes | ${serverlessEndpoint}`,
                            '#4fc3f7'
                        );
                    }
                    break;
                case 'polling':
                    lastHeartbeat = d.heartbeat || 0;
                    break;
                case 'complete': {
                    const nodes = Object.entries(d.output_nodes || {})
                        .map(([id, count]) => `${id}:${count}img`)
                        .join(', ');
                    const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
                    if (mode() === 'admin') {
                        status.show(
                            `GPU [${activeGpu}] ${short} | done ${elapsed}s | ${nodes}`,
                            '#66bb6a'
                        );
                    }
                    break;
                }
            }
        });

        // --- executed: output ready ---
        app.api.addEventListener("executed", () => {
            if (timer) { clearInterval(timer); timer = null; }
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;

            if (mode() === 'admin') {
                const short = promptId.slice(0, 8);
                status.show(`GPU [${activeGpu}] ${short} | complete | ${elapsed}s`, '#66bb6a');
            } else {
                status.show(`Inference complete! (${elapsed}s)`, '#66bb6a');
            }
            status.hide(4000);
        });

        // --- execution_error: failure details shown in overlay ---
        app.api.addEventListener("execution_error", (evt) => {
            if (timer) { clearInterval(timer); timer = null; }
            const detail = evt?.detail || {};
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
            const errType = detail.exception_type || 'Unknown';
            const errMsg = detail.exception_message || 'Unknown error';

            if (mode() === 'admin') {
                const short = promptId.slice(0, 8);
                status.show(
                    `GPU ERROR [${activeGpu}] ${short} | ${elapsed}s | ${errType}: ${errMsg}`,
                    '#ef5350'
                );
            } else {
                let userMsg = errMsg;
                if (errMsg.includes('routing error') || errMsg.includes('never appeared in history')) {
                    userMsg = 'GPU routing error — please try again';
                } else if (errMsg.includes('timed out')) {
                    userMsg = 'GPU timed out — please try again';
                }
                status.show(`Error: ${userMsg}`, '#ef5350');
            }
            status.hide(10000);
        });
    }
});
