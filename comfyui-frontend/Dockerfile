# ComfyUI Frontend Container - v0.11.0
# Multi-user workshop platform - COMFYUI_MODE=frontend-testing (UI only, no GPU inference)
# ComfyUI treated as immutable upstream dependency

FROM python:3.11-slim

LABEL maintainer="comfyume"
LABEL description="ComfyUI v0.11.0 frontend for multi-user workshop platform"

# Install system dependencies
# - curl: Health checks
# - git: Clone ComfyUI
# - libgomp1: Required for torchaudio (audio nodes)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 1. Clone ComfyUI v0.11.0 as immutable dependency
# CRITICAL: Use v0.11.0 NOT v0.11.1 (v0.11.1 has critical bugs!)
# - v0.11.0 released Jan 25, 2026 (stable, 4 days old)
# - v0.11.1 released Jan 29, 2026 (2 days old, 3 critical bugs)
RUN git clone --branch v0.11.0 --depth 1 \
    https://github.com/comfyanonymous/ComfyUI.git /comfyui

# 2. Install ComfyUI dependencies
# Install ComfyUI dependencies + requests (needed by frontend_management.py)
WORKDIR /comfyui
RUN pip install --no-cache-dir -r requirements.txt requests

# 3. BACKUP default custom nodes (prevents volume mount trap!)
# Problem: Volume-mounting empty host dir overwrites container's custom_nodes/
# Solution: Backup defaults, restore in entrypoint if volume is empty
RUN cp -r /comfyui/custom_nodes /tmp/custom_nodes_backup

# 4. Copy our custom extensions to build staging area
# These get deployed to the volume-mounted /comfyui/custom_nodes/ on every
# container start (see docker-entrypoint.sh Step 2). This is necessary because
# the volume mount overwrites the container's directory with the host directory.
# Extensions: queue_redirect (redirects jobs to QM), default_workflow_loader
COPY custom_nodes/ /build/custom_nodes/

# 5. Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 6. Health check
# ComfyUI server exposes /system_stats endpoint for health
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/system_stats || exit 1

# 7. Expose ComfyUI port
EXPOSE 8188

# 8. Set deployment mode (for clarity in orchestration)
# COMFYUI_MODE=frontend-testing indicates this container is UI-only
ENV COMFYUI_MODE=frontend-testing

# 9. Set entrypoint and default command
# Entrypoint handles:
# - Restoring custom nodes backup (volume mount fix)
# - Installing our extensions
# - Version-aware workflow setup (v0.11.0 paths)
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run ComfyUI in frontend-testing mode
# Uses --cpu flag (ComfyUI built-in) to disable GPU inference
# Each frontend container shows UI only - GPU inference happens on workers
CMD ["python", "/comfyui/main.py", "--listen", "0.0.0.0", "--port", "8188", "--cpu"]
