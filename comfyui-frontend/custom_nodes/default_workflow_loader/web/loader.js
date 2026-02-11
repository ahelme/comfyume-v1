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

            // Build relative URL so it routes through nginx to the correct user container.
            // Browser at /user001/ + relative "api/..." = /user001/api/... → user001:8188
            // Absolute "/api/..." would hit queue-manager instead (wrong!).
            // v0.9.0+ userdata API: slash encoded as %2F in the path component.
            const workflowPath = 'workflows%2Fflux2_klein_9b_text_to_image.json';
            const apiUrl = `api/userdata/${workflowPath}`;

            // v0.11.0 API: fetch JSON then load via app.loadGraphData()
            // (app.loadWorkflowFromURL does not exist in v0.11.0)
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch workflow (HTTP ${response.status})`);
            }
            const workflowData = await response.json();
            await app.loadGraphData(workflowData);

            // Mark as loaded (prevents re-loading on refresh)
            localStorage.setItem('comfy_workflow_loaded', 'true');

            console.log("[DefaultWorkflowLoader] ✅ Flux2 Klein 9B workflow loaded successfully");

        } catch (error) {
            console.error("[DefaultWorkflowLoader] ❌ Failed to load default workflow:", error);
            console.error("[DefaultWorkflowLoader] User can manually load workflow from Load menu");
        }
    }
});
