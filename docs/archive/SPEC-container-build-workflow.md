# SPEC: Container Build Workflow & CPU-Only Infrastructure

**Project:** ComfyUI Multi-User Workshop Platform
**Author:** Claude + User
**Created:** 2026-02-05
**Status:** DRAFT - Awaiting Review

---

## Overview

With serverless inference working well, we can eliminate the expensive RTX 6000 Ada GPU instance (~€0.70/hr = €16.80/day) and move to a cheaper CPU-only infrastructure for:
- App hosting (already on Mello)
- Container building & testing
- Backup orchestration
- Model management

## Current State

| Server | Purpose | Cost |
|--------|---------|------|
| Mello (Hetzner CAX31) | App hosting, Redis, frontends | €12.49/mo |
| Verda RTX 6000 Ada | GPU worker (mostly idle) | ~€500/mo if 24/7 |
| Serverless H200/B300 | Inference (pay-per-use) | ~€0.97-4.63/hr when active |

**Problem:** Paying for GPU instance that's mostly idle now that serverless works.

## Proposed Architecture

### Option A: Mello-Only (Simplest)

```
┌─────────────────────────────────────────────────────────┐
│ Mello VPS (comfy.ahelme.net) - €12.49/mo               │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Nginx     │  │   Redis     │  │ Queue Mgr   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Frontend Containers x20 (user001-user020)      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐                      │
│  │ Admin v2    │  │ Build Jobs  │ ← Container builds   │
│  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
                         │
                         │ HTTPS API calls
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Serverless Containers (DataCrunch)                      │
│  - H200 Spot €0.97/hr                                   │
│  - B300 Spot €1.61/hr                                   │
│  - Auto-scale 0→20 replicas                             │
└─────────────────────────────────────────────────────────┘
                         │
                         │ NFS mount
                         ▼
┌─────────────────────────────────────────────────────────┐
│ SFS Storage (Verda) - €0.01168/hr (~€8.50/mo)          │
│  /mnt/sfs/models/ - 77GB                                │
│  /mnt/sfs/cache/  - Container images, configs           │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- Simplest setup
- Lowest cost (~€21/mo base)
- Already have Mello

**Cons:**
- Mello has limited resources (8 vCPU, 16GB RAM)
- Container builds compete with user frontends
- No dedicated build environment

### Option B: Mello + Cheap CPU Instance (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│ Mello VPS - €12.49/mo                                   │
│  App hosting only (nginx, redis, queue-mgr, frontends)  │
└─────────────────────────────────────────────────────────┘
                         │
                         │ Tailscale VPN
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Verda CPU Instance - ~€0.05-0.10/hr (~€36-72/mo)       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Container Build Environment                      │   │
│  │  - Docker BuildKit                               │   │
│  │  - GHCR push access                              │   │
│  │  - Test containers (CPU-only validation)         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Backup Orchestration                             │   │
│  │  - SFS ↔ R2 sync                                 │   │
│  │  - Model management                              │   │
│  │  - Cron jobs                                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Mount: /mnt/sfs (shared storage)                       │
└─────────────────────────────────────────────────────────┘
```

**Verda CPU Instance Options:**
| Type | vCPU | RAM | Price/hr | Price/mo |
|------|------|-----|----------|----------|
| CPU.4V.16G | 4 | 16GB | €0.044 | ~€32 |
| CPU.8V.32G | 8 | 32GB | €0.088 | ~€64 |
| CPU.16V.64G | 16 | 64GB | €0.176 | ~€128 |

**Recommendation:** CPU.8V.32G (€0.088/hr) - enough for builds

### Option C: Serverless Build Container

```
┌─────────────────────────────────────────────────────────┐
│ Mello VPS - €12.49/mo                                   │
│  App hosting + build triggers                           │
└─────────────────────────────────────────────────────────┘
                         │
                         │ API trigger
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Serverless Build Container (DataCrunch)                 │
│                                                         │
│  Image: ghcr.io/ahelme/comfyume-builder:latest         │
│  GPU: None (CPU container)                              │
│  Trigger: On-demand via API                             │
│                                                         │
│  Tasks:                                                 │
│  - docker build                                         │
│  - docker push to GHCR                                  │
│  - Basic tests                                          │
│                                                         │
│  Mount: SFS for build cache                             │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- Pay only when building
- No idle costs
- Isolated environment

**Cons:**
- Cold start for builds
- Need to create builder container
- More complex workflow

---

## Container Build Without GPU

### The Challenge

GPU containers (ComfyUI worker) need CUDA libraries but we want to build on CPU-only machines.

### Solutions

#### 1. Multi-stage Build with Runtime Selection

```dockerfile
# Dockerfile.worker
FROM nvidia/cuda:12.4-runtime-ubuntu22.04 AS base

# Install Python, dependencies (no GPU needed for this)
RUN apt-get update && apt-get install -y python3 python3-pip git

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI /workspace/ComfyUI

# Install Python deps (CPU versions work on build machine)
WORKDIR /workspace/ComfyUI
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt

# At runtime, NVIDIA driver provides GPU support
# Build machine doesn't need GPU - just the base image layers
```

#### 2. BuildKit with Platform Targeting

```bash
# Build on CPU machine, target GPU runtime
docker buildx build \
  --platform linux/amd64 \
  --build-arg CUDA_VERSION=12.4 \
  -t ghcr.io/ahelme/comfyume-worker:v0.11.0 \
  -f Dockerfile.worker \
  --push .
```

#### 3. Separate Build and Runtime Images

```yaml
# docker-compose.build.yml (run on CPU machine)
services:
  builder:
    image: docker:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./:/workspace
    command: |
      docker build -t ghcr.io/ahelme/comfyume-worker:v0.11.0 \
        -f Dockerfile.worker .
      docker push ghcr.io/ahelme/comfyume-worker:v0.11.0
```

### Testing Without GPU

```bash
# Test container starts (won't run inference, but validates structure)
docker run --rm \
  -e CUDA_VISIBLE_DEVICES="" \
  ghcr.io/ahelme/comfyume-worker:v0.11.0 \
  python -c "import torch; print('PyTorch:', torch.__version__)"

# Test ComfyUI imports (no GPU needed)
docker run --rm \
  -e CUDA_VISIBLE_DEVICES="" \
  ghcr.io/ahelme/comfyume-worker:v0.11.0 \
  python -c "from comfy import model_management; print('ComfyUI imports OK')"

# Full GPU test happens on serverless (real inference)
```

---

## Updated restore-verda-instance.sh (was setup-verda-solo-script.sh)

### Changes for CPU-Only Instance

```bash
#!/bin/bash
# setup-verda-cpu-instance.sh
# For CPU-only build/backup instance (no GPU)

set -e

echo "=== ComfyuME CPU Instance Setup ==="
echo "Purpose: Container builds, backups, model management"
echo "NOT for GPU inference (use serverless for that)"

# Detect if GPU is present
if nvidia-smi &>/dev/null; then
    echo "WARNING: GPU detected. This script is for CPU-only instances."
    echo "For GPU worker setup, use restore-verda-instance.sh"
    read -p "Continue anyway? (y/N) " -n 1 -r
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# === PHASE 1: System Setup ===
apt-get update
apt-get install -y docker.io docker-compose-v2 git awscli

# === PHASE 2: Mount SFS ===
mkdir -p /mnt/sfs
mount -t nfs ${SFS_ENDPOINT}:/share /mnt/sfs
echo "${SFS_ENDPOINT}:/share /mnt/sfs nfs defaults 0 0" >> /etc/fstab

# === PHASE 3: Tailscale ===
curl -fsSL https://tailscale.com/install.sh | sh
# Restore identity if available
if [ -f /mnt/sfs/cache/tailscale-backup.tar.gz ]; then
    tar -xzf /mnt/sfs/cache/tailscale-backup.tar.gz -C /
fi
tailscale up --ssh=false

# === PHASE 4: Clone Repos ===
git clone https://github.com/ahelme/comfyume /root/comfyume
git clone https://github.com/ahelme/comfymulti-scripts /root/comfymulti-scripts

# Restore .env files from SFS
cp /mnt/sfs/cache/.env.comfyume /root/comfyume/.env
cp /mnt/sfs/cache/.env.scripts /root/comfymulti-scripts/.env

# === PHASE 5: Docker Login (for GHCR push) ===
echo "${GHCR_TOKEN}" | docker login ghcr.io -u ahelme --password-stdin

# === PHASE 6: Setup Build Environment ===
# Install BuildKit for efficient multi-platform builds
docker buildx create --name builder --use
docker buildx inspect --bootstrap

# === PHASE 7: Setup Cron Jobs ===
# Hourly backup: models SFS → R2 (if changed)
# Daily: Sync configs to SFS
cat > /etc/cron.d/comfyume-backups << 'CRON'
0 * * * * root /root/comfymulti-scripts/backup-cron.sh >> /var/log/backup-cron.log 2>&1
0 4 * * * root /root/comfymulti-scripts/upload-models-to-r2.sh >> /var/log/models-sync.log 2>&1
CRON

echo "=== CPU Instance Setup Complete ==="
echo "Build containers with: cd /root/comfyume && docker buildx build ..."
echo "Push to GHCR with: docker push ghcr.io/ahelme/comfyume-worker:tag"
```

### Script Variants

| Script | Purpose | GPU Required |
|--------|---------|--------------|
| `restore-verda-instance.sh` | Full app server restore (v0.4.0) | No |
| `setup-verda-cpu-instance.sh` | Build/backup instance | No |
| `setup-serverless-builder.sh` | Serverless build container | No |

---

## Migration Plan

### Step 1: Verify Serverless Works (DONE ✅)
- All 4 deployments created
- Queue manager routes to serverless
- Jobs execute successfully

### Step 2: Create CPU Instance
```bash
# On Verda Console:
# 1. Create new instance: CPU.8V.32G
# 2. Add SSH keys (mello + mac)
# 3. Attach to existing SFS
# 4. Run setup-verda-cpu-instance.sh
```

### Step 3: Test Container Builds
```bash
# On CPU instance:
cd /root/comfyume/comfyui-worker
docker buildx build -t ghcr.io/ahelme/comfyume-worker:test .
docker push ghcr.io/ahelme/comfyume-worker:test

# Verify on serverless:
# Update deployment to use :test tag
# Run test inference
```

### Step 4: Delete GPU Instance
```bash
# Final backup
/root/comfymulti-scripts/backup-verda.sh

# Delete via Verda Console
# Or API: DELETE /instances/{id}
```

### Step 5: Update Documentation
- CLAUDE.md: Remove GPU instance references
- README.md: Update architecture diagram
- setup scripts: Add CPU variant

---

## Cost Comparison

| Configuration | Monthly Cost |
|---------------|--------------|
| **Current:** Mello + RTX 6000 Ada 24/7 | €12 + €504 = **€516** |
| **Option A:** Mello only | €12 + €8 (SFS) = **€20** |
| **Option B:** Mello + CPU instance | €12 + €64 + €8 = **€84** |
| **Option C:** Mello + Serverless builder | €12 + €8 + ~€5 = **€25** |

Plus serverless inference costs (pay-per-use):
- Workshop day (4 hrs): ~€4-20 depending on GPU choice
- Idle time: €0

**Savings: €432-496/month** 🎉

---

## Open Questions

1. **SFS Access:** Can serverless containers mount SFS? (Need to verify)
2. **Build Frequency:** How often do we rebuild containers? (Weekly? On demand?)
3. **GHCR Auth:** Store token in SFS or use GitHub Actions?
4. **Spot vs On-Demand:** Use spot for CPU instance? (Cheaper but can be preempted)

---

## Related

- GitHub Issue: TBD (create after spec approval)
- Current restore script: `comfymulti-scripts/restore-verda-instance.sh` (v0.4.0)
- Serverless deployments: Issue #62 (COMPLETE)
