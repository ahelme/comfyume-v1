#!/bin/bash
# Deployment Test Script for Verda H100 Instance
# Run this on Verda GPU instance to verify worker setup
# Issue: comfyume #6

set -e

echo "=========================================="
echo "ComfyUI v0.11.0 Worker Deployment Test"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test 1: GPU Detection
echo "Test 1: GPU Detection"
echo "----------------------"

if ! command -v nvidia-smi &> /dev/null; then
    fail "nvidia-smi not found - GPU drivers not installed"
fi
pass "nvidia-smi found"

GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n1)
if [ "$GPU_COUNT" -lt 1 ]; then
    fail "No GPUs detected"
fi
pass "GPU detected: $GPU_COUNT GPU(s)"

GPU_MODEL=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
pass "GPU Model: $GPU_MODEL"

CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
pass "CUDA Version: $CUDA_VERSION"

VRAM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
VRAM_FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n1)
pass "VRAM: ${VRAM_FREE}MB free / ${VRAM_TOTAL}MB total"

echo ""

# Test 2: Storage Mounts
echo "Test 2: Storage Mounts"
echo "----------------------"

if [ ! -d "/mnt/sfs/models" ]; then
    fail "SFS models directory not mounted at /mnt/sfs/models"
fi
pass "SFS models directory mounted"

if [ ! -d "/mnt/scratch/outputs" ] || [ ! -d "/mnt/scratch/inputs" ]; then
    warn "Scratch disk not mounted - creating local directories for testing"
    mkdir -p /mnt/scratch/outputs /mnt/scratch/inputs
fi
pass "Scratch disk directories exist"

# Check if models are actually there
MODEL_COUNT=$(find /mnt/sfs/models -name "*.safetensors" 2>/dev/null | wc -l)
if [ "$MODEL_COUNT" -eq 0 ]; then
    warn "No models found in /mnt/sfs/models - models may need to be downloaded"
else
    pass "Models found: $MODEL_COUNT .safetensors files"
fi

echo ""

# Test 3: Tailscale Connection
echo "Test 3: Tailscale VPN Connection"
echo "--------------------------------"

REDIS_HOST=${INFERENCE_SERVER_REDIS_HOST:-100.99.216.71}
REDIS_PORT=${REDIS_PORT:-6379}

if ! timeout 5 bash -c "cat < /dev/null > /dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
    fail "Cannot connect to Redis at $REDIS_HOST:$REDIS_PORT"
fi
pass "Redis reachable at $REDIS_HOST:$REDIS_PORT"

if command -v tailscale &> /dev/null; then
    if tailscale status &> /dev/null; then
        TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "unknown")
        pass "Tailscale active: $TAILSCALE_IP"
    else
        warn "Tailscale installed but not running"
    fi
else
    warn "Tailscale not installed (may use direct connection)"
fi

echo ""

# Test 4: Docker Setup
echo "Test 4: Docker Setup"
echo "--------------------"

if ! command -v docker &> /dev/null; then
    fail "Docker not installed"
fi
pass "Docker found"

# Check nvidia-docker runtime
if docker info 2>/dev/null | grep -q "Runtimes.*nvidia"; then
    pass "nvidia-docker runtime available"
else
    fail "nvidia-docker runtime not configured"
fi

# Test GPU passthrough
if docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi &> /dev/null; then
    pass "Docker GPU passthrough working"
else
    fail "Docker cannot access GPU"
fi

echo ""

# Test 5: Project Structure
echo "Test 5: Project Structure"
echo "------------------------"

if [ ! -d "$HOME/comfyume/comfyui-worker" ]; then
    fail "Project not found at $HOME/comfyume/comfyui-worker"
fi
pass "Project directory exists"

cd $HOME/comfyume/comfyui-worker

if [ ! -f "Dockerfile" ]; then
    fail "Dockerfile not found"
fi
pass "Dockerfile found"

if [ ! -f "docker-compose.yml" ]; then
    fail "docker-compose.yml not found"
fi
pass "docker-compose.yml found"

if [ ! -f "worker.py" ]; then
    fail "worker.py not found"
fi
pass "worker.py found"

if [ ! -f "vram_monitor.py" ]; then
    fail "vram_monitor.py not found"
fi
pass "vram_monitor.py found"

echo ""

# Test 6: Environment Variables
echo "Test 6: Environment Variables"
echo "-----------------------------"

if [ -z "$REDIS_PASSWORD" ]; then
    warn "REDIS_PASSWORD not set - worker auth will fail"
else
    pass "REDIS_PASSWORD set"
fi

if [ -z "$QUEUE_MANAGER_URL" ]; then
    warn "QUEUE_MANAGER_URL not set - using default"
else
    pass "QUEUE_MANAGER_URL set: $QUEUE_MANAGER_URL"
fi

echo ""

# Test 7: VRAM Monitor CLI
echo "Test 7: VRAM Monitor CLI Test"
echo "-----------------------------"

if python3 vram_monitor.py 2>&1 | grep -q "VRAM Status"; then
    pass "VRAM monitor CLI working"
else
    fail "VRAM monitor CLI failed"
fi

echo ""

# Test 8: Docker Build (if requested)
if [ "$1" == "--build" ]; then
    echo "Test 8: Docker Build"
    echo "--------------------"

    if docker build -t comfyume-worker:test . &> /tmp/docker-build.log; then
        pass "Docker build successful"
    else
        fail "Docker build failed - see /tmp/docker-build.log"
    fi

    echo ""
fi

# Summary
echo "=========================================="
echo "Deployment Test Summary"
echo "=========================================="
echo ""
echo "All required tests passed! ✅"
echo ""
echo "Next steps:"
echo "1. Set REDIS_PASSWORD environment variable"
echo "2. Run: docker compose up -d"
echo "3. Check logs: docker compose logs -f worker-1"
echo "4. Monitor: docker compose ps"
echo ""
echo "For full build test, run: $0 --build"
echo ""
