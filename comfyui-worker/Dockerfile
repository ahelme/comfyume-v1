# ComfyUI v0.11.0 Worker Container
# Copied from comfy-multi/comfyui-worker/Dockerfile and updated for v0.11.0
# Issue: comfyume #2

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    COMFYUI_VERSION=v0.11.0

# Install system dependencies
# Added: curl (health checks), libgomp1 (audio nodes)
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /workspace

# Clone ComfyUI v0.11.0 (updated from v0.9.2)
RUN git clone --branch v0.11.0 --depth 1 https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI

# Install ComfyUI dependencies
WORKDIR /workspace/ComfyUI
RUN pip3 install --no-cache-dir -r requirements.txt

# Install missing dependencies (not in ComfyUI requirements.txt)
# requests: Used by health checks and worker
RUN pip3 install --no-cache-dir requests

# Install worker dependencies
COPY requirements.txt /workspace/worker-requirements.txt
RUN pip3 install --no-cache-dir -r /workspace/worker-requirements.txt

# Copy worker scripts (Issue #3, #4)
COPY worker.py /workspace/worker.py
COPY vram_monitor.py /workspace/vram_monitor.py
COPY start-worker.sh /workspace/start-worker.sh
RUN chmod +x /workspace/start-worker.sh /workspace/worker.py /workspace/vram_monitor.py

# Create directories for models and outputs
RUN mkdir -p /workspace/ComfyUI/models \
    /workspace/ComfyUI/output \
    /workspace/ComfyUI/input \
    /outputs \
    /inputs

# Add extra model paths config (handles /models/ mount from restored containers)
COPY extra_model_paths.yaml /workspace/ComfyUI/extra_model_paths.yaml

# Create non-root user
RUN useradd -m -u 1000 comfyuser && \
    chown -R comfyuser:comfyuser /workspace /outputs /inputs

USER comfyuser

# Expose ComfyUI port
EXPOSE 8188

# Health check (updated to use curl instead of Python requests)
# curl is more reliable and lighter than Python for health checks
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

# Start worker
CMD ["/workspace/start-worker.sh"]
