/**
 * GPU Overlay Extension — ComfyuME
 *
 * Two display modes (set via localStorage):
 *   "user"  — simple progress messages (default)
 *   "admin" — detailed technical info (prompt_id, heartbeats, endpoints, errors)
 *
 * Toggle: localStorage.setItem('gpu_overlay_mode', 'admin')
 *         localStorage.setItem('gpu_overlay_mode', 'user')
 *
 * Listens for WebSocket events from serverless_proxy:
 *   execution_start    → job submitted
 *   comfyume_progress  → detailed phase updates (admin mode)
 *   executed           → output ready
 *   execution_error    → failure details
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

        console.log(`[GPUOverlay] Active — mode: ${mode()}, GPU: ${activeGpu}, endpoint: ${serverlessEndpoint}`);

        // --- execution_start: job submitted ---
        app.api.addEventListener("execution_start", (evt) => {
            startTime = Date.now();
            promptId = evt?.detail?.prompt_id || '';

            if (mode() === 'admin') {
                const short = promptId.slice(0, 8);
                status.show(`GPU [${activeGpu}] Submitting ${short}...`, '#4fc3f7');
            } else {
                status.show('Sending to GPU...', '#4fc3f7');
            }

            timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                if (mode() === 'admin') {
                    const short = promptId.slice(0, 8);
                    status.show(`GPU [${activeGpu}] ${short} polling... ${elapsed}s`, '#ffb74d');
                } else {
                    status.show(`Processing on GPU... ${elapsed}s`, '#ffb74d');
                }
            }, 1000);
        });

        // --- comfyume_progress: detailed phase updates (admin mode) ---
        app.api.addEventListener("comfyume_progress", (evt) => {
            if (mode() !== 'admin') return;

            const d = evt?.detail || {};
            const short = (d.prompt_id || '').slice(0, 8);

            switch (d.phase) {
                case 'submitting':
                    status.show(
                        `GPU [${activeGpu}] ${short} | ${d.node_count} nodes | ${serverlessEndpoint}`,
                        '#4fc3f7'
                    );
                    break;
                case 'polling':
                    status.show(
                        `GPU [${activeGpu}] ${short} | heartbeat #${d.heartbeat} | ${d.elapsed}s`,
                        '#ffb74d'
                    );
                    break;
                case 'complete':
                    const nodes = Object.entries(d.output_nodes || {})
                        .map(([id, count]) => `${id}:${count}img`)
                        .join(', ');
                    const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
                    status.show(
                        `GPU [${activeGpu}] ${short} | done ${elapsed}s | ${nodes}`,
                        '#66bb6a'
                    );
                    break;
            }
        });

        // --- executed: output ready ---
        app.api.addEventListener("executed", () => {
            if (timer) { clearInterval(timer); timer = null; }
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;

            if (mode() !== 'admin') {
                status.show(`Inference complete! (${elapsed}s)`, '#66bb6a');
            }
            // Admin mode shows details via comfyume_progress 'complete' phase
            status.hide(4000);
        });

        // --- execution_error: failure ---
        app.api.addEventListener("execution_error", (evt) => {
            if (timer) { clearInterval(timer); timer = null; }
            const detail = evt?.detail || {};
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;

            if (mode() === 'admin') {
                const short = promptId.slice(0, 8);
                const type = detail.exception_type || 'Unknown';
                const msg = detail.exception_message || '';
                status.show(
                    `GPU ERROR [${activeGpu}] ${short} | ${elapsed}s | ${type}: ${msg}`,
                    '#ef5350'
                );
            } else {
                const msg = detail.exception_message || 'Unknown error';
                status.show(`Error: ${msg}`, '#ef5350');
            }
            status.hide(8000);
        });
    }
});
