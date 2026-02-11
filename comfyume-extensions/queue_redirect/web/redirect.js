/**
 * Queue Redirect Extension - ComfyUI v0.11.0
 * Intercepts job submission and redirects to queue-manager
 *
 * v0.11.0 uses Vite-built frontend — app must be imported via shim.
 * The shim at /scripts/app.js reads from window.comfyAPI.app.app
 */
import { app } from "../../scripts/app.js";

// Status banner — shows serverless inference progress in a floating overlay.
// ComfyUI's native progress bar only works with its WebSocket-based local queue,
// which we bypass entirely. This gives the user visual feedback during the
// 1-4 minute serverless inference wait.
function createStatusBanner() {
    const banner = document.createElement('div');
    banner.id = 'comfyume-status-banner';
    banner.style.cssText = `
        position: fixed; top: 12px; left: 50%; transform: translateX(-50%);
        z-index: 99999; padding: 10px 20px; border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px; font-weight: 500; color: #fff;
        background: #1a1a2e; border: 1px solid #333;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        display: none; transition: opacity 0.3s;
    `;
    document.body.appendChild(banner);
    return banner;
}

function showStatus(banner, message, color = '#4fc3f7') {
    banner.textContent = message;
    banner.style.borderColor = color;
    banner.style.display = 'block';
    banner.style.opacity = '1';
}

function hideStatus(banner, delay = 3000) {
    setTimeout(() => {
        banner.style.opacity = '0';
        setTimeout(() => { banner.style.display = 'none'; }, 300);
    }, delay);
}

app.registerExtension({
    name: "comfy.queueRedirect",

    async setup() {
        console.log("[QueueRedirect] Extension loaded (v0.11.0 API)");

        // Check inference mode from QM health endpoint.
        // In serverless mode, the server-side serverless_proxy extension handles
        // execution — we defer to ComfyUI's native queue instead of intercepting.
        let inferenceMode = 'local';
        try {
            const health = await fetch('/api/health');
            if (health.ok) {
                const data = await health.json();
                inferenceMode = data.inference_mode || 'local';
            }
        } catch (e) {
            console.warn("[QueueRedirect] Could not check inference mode:", e);
        }

        if (inferenceMode === 'serverless') {
            console.log("[QueueRedirect] Serverless mode — deferring to native queue + server-side proxy");
            return;
        }

        // Non-serverless mode: intercept queuePrompt and route to QM
        const banner = createStatusBanner();

        // Extract user ID from URL path (e.g. /user001/ → user001)
        // Falls back to window.USER_ID or 'unknown'
        const pathMatch = window.location.pathname.match(/\/(user\d+)\//);
        const USER_ID = (pathMatch && pathMatch[1]) || window.USER_ID || 'unknown';
        console.log(`[QueueRedirect] User ID: ${USER_ID}`);

        // Store original queuePrompt function
        const originalQueuePrompt = app.queuePrompt;

        // Override queuePrompt to redirect to queue-manager
        // Queue manager endpoint: POST /api/jobs (via nginx /api/ → queue-manager:3000/)
        // nginx strips /api/ prefix, so /api/jobs → queue-manager:3000/api/jobs
        app.queuePrompt = async function(number, batchCount = 1) {
            console.log(`[QueueRedirect] Intercepting job submission (${batchCount} jobs)`);

            const startTime = Date.now();
            showStatus(banner, 'Sending to GPU...', '#4fc3f7');

            // Update elapsed time every second during inference
            const timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                showStatus(banner, `Processing on GPU... ${elapsed}s`, '#ffb74d');
            }, 1000);

            try {
                // Convert graph to ComfyUI API prompt format
                // graphToPrompt() returns { output: {nodeId: config}, workflow: graphData }
                // ComfyUI /prompt endpoint expects the "output" dict
                const { output } = await app.graphToPrompt();

                showStatus(banner, 'Submitting to serverless GPU...', '#4fc3f7');

                // Submit each batch item as a separate job
                let lastResult = null;
                for (let i = 0; i < batchCount; i++) {
                    const response = await fetch('/api/jobs', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_id: USER_ID,
                            workflow: output,
                            priority: 1,
                            metadata: { batch_index: i, batch_total: batchCount }
                        })
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Queue submission failed (${response.status}): ${errorText}`);
                    }

                    lastResult = await response.json();
                    console.log(`[QueueRedirect] Job ${i+1}/${batchCount} submitted:`, lastResult);
                    console.log(`[QueueRedirect] Full result:`, JSON.stringify(lastResult, null, 2));
                }

                clearInterval(timer);
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                showStatus(banner, `Inference complete! (${elapsed}s)`, '#66bb6a');
                hideStatus(banner, 4000);

                console.log(`[QueueRedirect] All ${batchCount} job(s) submitted`);
                return lastResult;

            } catch (error) {
                clearInterval(timer);
                console.error("[QueueRedirect] Failed to submit job:", error);

                showStatus(banner, `Error: ${error.message}`, '#ef5350');
                hideStatus(banner, 8000);

                throw error;
            }
        };

        console.log("[QueueRedirect] Queue interception active (non-serverless mode)");
    }
});
