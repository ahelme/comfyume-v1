#!/bin/bash
# ComfyUI Frontend Entrypoint - v0.11.0
# Handles version-aware initialization for multi-user workshop platform

set -e

echo "🚀 Starting ComfyUI v0.11.0 frontend initialization..."

# 1. Restore ComfyUI's default custom nodes from backup (fixes volume mount trap!)
# Problem: docker-compose.users.yml volume-mounts host dir over /comfyui/custom_nodes/
#   ./data/user_data/userXXX/comfyui/custom_nodes:/comfyui/custom_nodes
# This OVERWRITES the container's directory. If host dir is empty, everything is gone.
# Solution: Backup defaults during build (Dockerfile Step 3), restore here if missing.
echo "📦 Checking custom nodes..."
if [ ! -f "/comfyui/custom_nodes/websocket_image_save.py" ]; then
    echo "⚠️  Custom nodes empty - restoring ComfyUI defaults from backup..."
    cp -r /tmp/custom_nodes_backup/* /comfyui/custom_nodes/
    echo "✅ ComfyUI default custom nodes restored"
else
    echo "✅ ComfyUI default custom nodes already present"
fi

# 2. Deploy our workshop extensions (from /build/custom_nodes/ → mounted volume)
# Dockerfile Step 4 copies queue_redirect + default_workflow_loader into /build/custom_nodes/
# This step copies them into the volume-mounted directory on EVERY start (idempotent).
# This is how our extensions survive the volume mount overwrite.
echo "🔧 Installing workshop extensions..."
if [ -d "/build/custom_nodes" ] && [ "$(ls -A /build/custom_nodes 2>/dev/null)" ]; then
    cp -r /build/custom_nodes/* /comfyui/custom_nodes/
    echo "✅ Workshop extensions installed: $(ls -d /build/custom_nodes/*/ 2>/dev/null | xargs -I{} basename {} | tr '\n' ' ')"
else
    echo "⚠️  No workshop extensions found in /build/custom_nodes/"
fi

# 3. Version-aware workflow setup (v0.11.0 uses /comfyui/user/default/workflows/)
# v0.8.2 path: /comfyui/input/templates/ (OLD - BROKEN)
# v0.9.0+ path: /comfyui/user/default/workflows/ (NEW - STABLE)
echo "📂 Setting up workflows for v0.11.0..."
WORKFLOW_PATH="/comfyui/user/default/workflows"
mkdir -p "$WORKFLOW_PATH"

# Copy workflow templates from mounted volume (if available)
if [ -d "/workflows" ] && [ "$(ls -A /workflows/*.json 2>/dev/null)" ]; then
    cp /workflows/*.json "$WORKFLOW_PATH/"
    echo "✅ Workflows copied: $(ls -1 $WORKFLOW_PATH/*.json 2>/dev/null | wc -l) templates"
else
    echo "⚠️  No workflows found in /workflows/ (will mount later)"
fi

# 4. Create workflow index for userdata API (v0.11.0 compatibility)
# ComfyUI v0.11.0 userdata API serves workflows from this location
# Browser requests: GET /api/userdata?dir=workflows
echo "📝 Creating workflow index..."
cat > "$WORKFLOW_PATH/.index.json" <<EOF
{
  "templates": [
    "flux2_klein_9b_text_to_image.json",
    "flux2_klein_4b_text_to_image.json",
    "ltx2_text_to_video.json",
    "ltx2_text_to_video_distilled.json",
    "example_workflow.json"
  ]
}
EOF
echo "✅ Workflow index created"

# 5. Set up user data directory (for settings, preferences)
# v0.11.0 expects /comfyui/user/default/ for user-specific data
mkdir -p /comfyui/user/default

# 6. Set up extra model paths (models mounted at /models/shared/)
# Frontend needs model listings for prompt validation before sending to worker queue
echo "📂 Setting up model paths..."
cat > /comfyui/extra_model_paths.yaml <<EOF
comfyume:
    base_path: /models/shared/
    checkpoints: checkpoints/
    diffusion_models: diffusion_models/
    text_encoders: text_encoders/
    vae: vae/
    loras: loras/
    latent_upscale_models: latent_upscale_models/
EOF
echo "✅ Model paths configured"

# 7. Ready to start ComfyUI!
echo ""
echo "✨ ComfyUI v0.11.0 frontend ready!"
echo "   - Workflows: $WORKFLOW_PATH"
echo "   - Custom nodes: /comfyui/custom_nodes"
echo "   - Mode: CPU only (--cpu flag)"
echo ""

# 8. Start ComfyUI with arguments passed to container
# CMD from Dockerfile: ["python", "/comfyui/main.py", "--listen", "0.0.0.0", "--port", "8188", "--cpu"]
exec "$@"
