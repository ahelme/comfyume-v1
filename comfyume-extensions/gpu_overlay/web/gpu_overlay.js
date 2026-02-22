/**
 * GPU Overlay Extension — ComfyuME
 *
 * Floating status banner for serverless GPU inference progress.
 * Listens for WebSocket events from serverless_proxy:
 *   execution_start → "Sending to GPU..."
 *   executing       → "Processing on GPU... Ns" (elapsed timer)
 *   executed        → "Inference complete! (Ns)"
 *   execution_error → "Error: {message}"
 *
 * Only active in serverless mode. In non-serverless modes,
 * queue_redirect handles its own progress banner.
 */
import { app } from "../../scripts/app.js";

function createBanner() {
    const el = document.createElement('div');
    el.id = 'comfyume-gpu-overlay';
    el.style.cssText = `
        position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
        z-index: 99999; padding: 10px 20px; border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px; font-weight: 500; color: #fff;
        background: #1a1a2e; border: 1px solid #333;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        display: none; transition: opacity 0.3s;
    `;
    document.body.appendChild(el);
    return el;
}

function show(banner, message, color = '#4fc3f7') {
    banner.textContent = message;
    banner.style.borderColor = color;
    banner.style.display = 'block';
    banner.style.opacity = '1';
}

function hide(banner, delay = 3000) {
    setTimeout(() => {
        banner.style.opacity = '0';
        setTimeout(() => { banner.style.display = 'none'; }, 300);
    }, delay);
}

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

        console.log("[GPUOverlay] Active — listening for GPU inference events");
        const banner = createBanner();
        let timer = null;
        let startTime = null;

        app.api.addEventListener("execution_start", () => {
            startTime = Date.now();
            show(banner, 'Sending to GPU...', '#4fc3f7');
            timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                show(banner, `Processing on GPU... ${elapsed}s`, '#ffb74d');
            }, 1000);
        });

        app.api.addEventListener("executed", () => {
            if (timer) { clearInterval(timer); timer = null; }
            const elapsed = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
            show(banner, `Inference complete! (${elapsed}s)`, '#66bb6a');
            hide(banner, 4000);
        });

        app.api.addEventListener("execution_error", (evt) => {
            if (timer) { clearInterval(timer); timer = null; }
            const detail = evt?.detail || {};
            const msg = detail.exception_message || 'Unknown error';
            show(banner, `Error: ${msg}`, '#ef5350');
            hide(banner, 8000);
        });
    }
});
