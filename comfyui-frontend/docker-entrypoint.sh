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

# 2. Deploy ComfyuME extensions (config-driven, from /build/comfyume-extensions/)
# extensions.conf controls which extensions are deployed. Only uncommented lines are installed.
# This runs on EVERY container start (idempotent) — extensions survive volume mount overwrite.
echo "🔧 Installing ComfyuME extensions..."
CUSTOMISATIONS_DIR="/build/comfyume-extensions"
EXTENSIONS_CONF="$CUSTOMISATIONS_DIR/extensions.conf"

if [ -f "$EXTENSIONS_CONF" ]; then
    enabled_count=0
    while IFS= read -r ext || [ -n "$ext" ]; do
        # Skip comments and empty lines
        case "$ext" in \#*|"") continue ;; esac
        ext=$(echo "$ext" | tr -d '[:space:]')  # trim whitespace
        if [ -d "$CUSTOMISATIONS_DIR/$ext" ]; then
            cp -r "$CUSTOMISATIONS_DIR/$ext" /comfyui/custom_nodes/
            echo "   ✅ Enabled: $ext"
            enabled_count=$((enabled_count + 1))
        else
            echo "   ⚠️  Not found: $ext"
        fi
    done < "$EXTENSIONS_CONF"
    echo "✅ $enabled_count extension(s) installed"
else
    echo "⚠️  No extensions.conf found — no ComfyuME extensions installed"
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
