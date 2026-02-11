/**
 * Default Workflow Loader - ComfyUI v0.11.0
 * Auto-loads Flux2 Klein 9B workflow on first visit
 *
 * v0.11.0 uses Vite-built frontend — app must be imported via shim.
 * The shim at /scripts/app.js reads from window.comfyAPI.app.app
 */
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfy.defaultWorkflowLoader",

    async setup() {
        console.log("[DefaultWorkflowLoader] Extension loaded (v0.11.0 API)");

        // Check if workflow already loaded (prevent re-loading on every page visit)
        const hasLoaded = localStorage.getItem('comfy_workflow_loaded');

        if (hasLoaded) {
            console.log("[DefaultWorkflowLoader] Workflow already loaded previously, skipping");
            return;
        }

        try {
            console.log("[DefaultWorkflowLoader] Loading default workflow: Flux2 Klein 9B...");

            // URL-encode path for v0.9.0+ userdata API
            // v0.9.0+ requires: workflows%2Ffile.json (slash encoded as %2F)
            // Route: /api/userdata/{file} where {file} = "workflows%2Fflux2_klein_9b_text_to_image.json"
            const workflowPath = 'workflows%2Fflux2_klein_9b_text_to_image.json';
            const apiUrl = `/api/userdata/${workflowPath}`;

            // Load workflow from userdata API
            await app.loadWorkflowFromURL(apiUrl);

            // Mark as loaded (prevents re-loading on refresh)
            localStorage.setItem('comfy_workflow_loaded', 'true');

            console.log("[DefaultWorkflowLoader] ✅ Flux2 Klein 9B workflow loaded successfully");

        } catch (error) {
            console.error("[DefaultWorkflowLoader] ❌ Failed to load default workflow:", error);
            console.error("[DefaultWorkflowLoader] User can manually load workflow from menu");
        }
    }
});
