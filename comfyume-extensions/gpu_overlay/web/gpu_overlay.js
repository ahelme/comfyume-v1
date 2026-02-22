/**
 * GPU Overlay Extension — ComfyuME
 *
 * Listens for serverless inference WebSocket events and shows progress
 * via the status_banner extension (window.comfyumeStatus).
 *
 * Events from serverless_proxy:
 *   execution_start → "Sending to GPU..."
 *   executing       → "Processing on GPU... Ns"
 *   executed        → "Inference complete! (Ns)"
 *   execution_error → "Error: {message}"
 *
 * Only active in serverless mode.
 * Requires: status_banner extension.
 */
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfy.gpuOverlay",

    async setup() {
        // Only activate in serverless mode
        let inferenceMode = 'local';
        try {
            const health = await fetch('/api/health');
            if (health.ok) {
                const data = await health.json();
                inferenceMode = data.inference_mode || 'local';
            }
        } catch (e) {
            // Can't reach QM — not serverless
        }

        if (inferenceMode !== 'serverless') {
            console.log("[GPUOverlay] Inactive (non-serverless mode)");
            return;
        }

        // Wait for status_banner to initialize
        if (!window.comfyumeStatus) {
            console.warn("[GPUOverlay] status_banner not loaded — banner will not show");
            return;
        }

        console.log("[GPUOverlay] Active — listening for GPU inference events");
        const status = window.comfyumeStatus;
        let timer = null;
        let startTime = null;

        app.api.addEventListener("execution_start", () => {
            startTime = Date.now();
            status.show('Sending to GPU...', '#4fc3f7');
            timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                status.show(`Processing on GPU... ${elapsed}s`, '#ffb74d');
            }, 1000);
        });

        app.api.addEventListener("executed", () => {
            if (timer) { clearInterval(timer); timer = null; }
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
            status.show(`Inference complete! (${elapsed}s)`, '#66bb6a');
            status.hide(4000);
        });

        app.api.addEventListener("execution_error", (evt) => {
            if (timer) { clearInterval(timer); timer = null; }
            const detail = evt?.detail || {};
            const msg = detail.exception_message || 'Unknown error';
            status.show(`Error: ${msg}`, '#ef5350');
            status.hide(8000);
        });
    }
});
