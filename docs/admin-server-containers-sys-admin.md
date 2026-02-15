**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-12
**Doc Updated:** 2026-02-12

---

# Server & Container Administration Guide

Crucial server-side changes made to get ComfyuME running on quiet-city (65.108.33.101). These are changes applied directly on the production server or via Verda API, NOT committed to git. They must be codified in restore scripts for reproducibility.

---

## Instance Overview

| Property | Value |
|---|---|
| Instance | quiet-city-purrs-fin-01 |
| IP | 65.108.33.101 |
| Tailscale IP | 100.89.38.43 |
| Type | CPU.8V.32G (8 vCPU, 32GB RAM) |
| OS | Ubuntu 24.04 |
| Provider | Verda |
| Docker | Pre-installed (containerd-based, do NOT install docker.io) |
| SFS Mount | /mnt/sfs (NFS, shared with serverless containers) |

---

## 1. SFS Output Directory Permissions (BUG-002)

### Problem

Serverless containers run ComfyUI as uid 1000 (non-root). The output directory `/mnt/sfs/outputs/` was created with default permissions `755 root:root`. ComfyUI could not write generated images.

### Symptoms

- QM logs: `poll_serverless_history` completes successfully
- Serverless container: inference completes (HTTP 200)
- But no images appear in `/mnt/sfs/outputs/`
- QM: `fetch_serverless_images()` finds nothing to copy

### Fix Applied

```bash
# On quiet-city (65.108.33.101):
sudo chmod 1777 /mnt/sfs/outputs/
```

**Sticky bit (1)** prevents users from deleting each other's files. **World-writable (777)** allows any uid to create files. Same pattern as `/tmp`.

### Verification

```bash
ls -ld /mnt/sfs/outputs/
# drwxrwxrwt 2 root root 4096 Feb 12 05:50 /mnt/sfs/outputs/
#                    ^ sticky bit

# After a successful generation:
ls -la /mnt/sfs/outputs/
# -rw-r--r-- 1 1000 1000 2097152 Feb 12 05:50 Flux2-Klein_00001_.png
```

### Codify In

**File:** `comfymulti-scripts/restore-verda-instance.sh`
**Add after SFS mount step:**
```bash
mkdir -p /mnt/sfs/outputs
chmod 1777 /mnt/sfs/outputs
```

---

## 2. DataCrunch Container Start Command (BUG-003)

### Problem

The DataCrunch serverless container was configured via Verda Console with start command:
```bash
python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --extra-model-paths-config /mnt/sfs/extra_model_paths.yaml
```

Missing `--output-directory /mnt/sfs/outputs` flag meant ComfyUI saved images to `/workspace/ComfyUI/output/` (container-local, ephemeral). Images were lost when the container scaled down.

### Symptoms

- QM logs: inference completes, `prompt_id` received
- QM: `poll_serverless_history()` returns outputs with filenames
- QM: `fetch_serverless_images()` finds nothing on SFS
- Images exist inside serverless container but not on shared storage

### Fix Applied

Updated via Verda Python SDK:

```python
from verda import Verda

client = Verda()
client.containers.update_deployment(
    'comfyume-vca-ftv-h200-spot',
    cmd=[
        'python3', '/workspace/ComfyUI/main.py',
        '--listen', '0.0.0.0',
        '--port', '8188',
        '--extra-model-paths-config', '/mnt/sfs/extra_model_paths.yaml',
        '--output-directory', '/mnt/sfs/outputs'
    ]
)
```

### Correct Start Command

```bash
python3 /workspace/ComfyUI/main.py \
  --listen 0.0.0.0 \
  --port 8188 \
  --extra-model-paths-config /mnt/sfs/extra_model_paths.yaml \
  --output-directory /mnt/sfs/outputs
```

### Verification

After applying the fix and triggering a new serverless inference:
```bash
# Check SFS for generated images:
ls -la /mnt/sfs/outputs/
# Should show new .png files with recent timestamps
```

### Codify In

**Option A:** Verda deployment automation script (Python SDK)
**Option B:** Verda Terraform/OpenTofu config
**Option C:** Document in SERVERLESS_UPDATE.md (done — see line 98)

---

## 3. SFS Wrapper Script

### What It Is

A startup wrapper script stored on SFS that sets correct permissions before starting ComfyUI.

**Location:** `/mnt/sfs/start-comfyui-wrapper.sh`

### Contents

```bash
#!/bin/bash
# Ensure output directory exists and is writable
mkdir -p /mnt/sfs/outputs
chmod 1777 /mnt/sfs/outputs 2>/dev/null || true

# Start ComfyUI with output directory pointing to SFS
exec python3 /workspace/ComfyUI/main.py \
  --listen 0.0.0.0 \
  --port 8188 \
  --extra-model-paths-config /mnt/sfs/extra_model_paths.yaml \
  --output-directory /mnt/sfs/outputs \
  "$@"
```

### Purpose

Used as the DataCrunch container start command instead of raw `python3 ...`. Ensures SFS permissions are correct on every container boot. This is important because:

1. Serverless containers are ephemeral (scale 0-10)
2. SFS permissions might be reset by maintenance operations
3. The wrapper is self-healing — creates `/mnt/sfs/outputs/` if missing

### Codify In

Already on SFS. Document in restore scripts that this file must exist.

---

## 4. Docker Compose Volume Mounts

### Queue Manager SFS Mount (PR #28)

Added to `docker-compose.yml` (committed to git):
```yaml
queue-manager:
  volumes:
    - /mnt/sfs/outputs:/mnt/sfs/outputs:ro
```

This gives the queue-manager container read-only access to SFS outputs so it can copy serverless-generated images to user output directories.

### Image Delivery Flow

```
Serverless Container          SFS (shared NFS)           Queue Manager         Frontend
   ComfyUI saves →     /mnt/sfs/outputs/image.png   ← QM reads (ro mount)
                                                      QM copies to →        /outputs/user001/
                                                                            ComfyUI serves via
                                                                            /api/view?filename=
```

---

## 5. Container Health Status

### Expected State (24 healthy)

```
CONTAINER              STATUS
comfy-nginx            Up, healthy
comfy-redis            Up, healthy
comfy-queue-manager    Up, healthy
comfy-admin            Up, healthy
comfy-user001-020      Up, healthy (x20)
```

### Check Commands

```bash
# Count healthy containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy

# List all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep comfy

# Queue manager health
curl -s http://localhost:3000/health | jq

# Full system status
./scripts/status.sh
```

### Worker Container (NOT running on CPU instance)

The `comfy-worker-1` container has `profiles: [gpu]` in `docker-compose.yml`. It only starts when explicitly invoked with `--profile gpu`. This prevents nvidia driver errors on CPU-only instances.

---

## 6. SSL Certificate

| Property | Value |
|---|---|
| Domain | aiworkshop.art |
| Issuer | Namecheap / Sectigo |
| Cert location | `/etc/ssl/certs/fullchain.pem` |
| Key location | `/etc/ssl/private/privkey.pem` |
| Expiry | 2026-05-12 (approx) |
| Renewal | Manual (Namecheap dashboard) |

### Verify

```bash
openssl x509 -in /etc/ssl/certs/fullchain.pem -noout -dates
```

---

## 7. Nginx Configuration

### Key Fixes Applied (committed to git)

1. **Dynamic DNS resolution** (`93bf1a1`): Added `resolver 127.0.0.11` to use Docker internal DNS. Prevents nginx crash when upstream containers aren't ready.

2. **Variable-based proxy_pass**: Changed from `proxy_pass http://user001:8188` to:
   ```nginx
   set $upstream_user001 http://user001:8188;
   proxy_pass $upstream_user001;
   ```
   Variables are resolved at request time (not startup time).

3. **Timeout for serverless**: `proxy_read_timeout 600s` to accommodate cold start + model load + inference.

### Host Nginx Conflict

Ubuntu 24.04 ships with nginx installed and running on port 80. Container nginx cannot bind port 80 while host nginx is running.

**Fix (applied during restore):**
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

---

## 8. Redis Configuration

### Current Setup (Option C — Serverless)

```
REDIS_HOST=redis           # Docker service name (internal DNS)
REDIS_BIND_IP=127.0.0.1   # Bind to localhost only
REDIS_PASSWORD=<from .env>
```

Redis runs inside `comfy-redis` container on Docker network. Queue manager connects via Docker internal DNS (`redis:6379`). No external access needed in serverless mode (workers connect via HTTP to QM, not Redis).

### Password

Set via `redis-server --requirepass ${REDIS_PASSWORD}` in docker-compose.yml. All clients (QM, admin) must provide password.

---

## 9. Tailscale VPN

### Identity Preservation

Tailscale identity files in `/var/lib/tailscale/` must be restored BEFORE running `tailscale up`. Otherwise Tailscale registers a new device with a new IP.

**Expected IP:** 100.89.38.43

**Restore order:**
1. Restore `/var/lib/tailscale/` from backup
2. `systemctl start tailscaled`
3. `tailscale up` (reuses existing identity)

---

## 10. Disk Space Monitoring

### Current Usage

```bash
df -h /tmp /mnt/sfs
```

### Automated Checks

`scripts/disk-check.sh --block` runs before:
- `scripts/start.sh`
- Docker build operations
- Backup scripts
- Restore scripts

Aborts if >90% full.

### Docker Image Cleanup

Old Docker images consume ~80GB. Clean up with:
```bash
docker system prune -a --volumes  # CAUTION: removes all unused
docker image prune -a             # Safer: only images
```

---

## Quick Reference: What Goes Where

| Change Type | Where to Apply | How to Codify |
|---|---|---|
| Code changes | Git repo → deploy.sh | Commit, push, `./scripts/deploy.sh` |
| SFS file/permissions | SSH to quiet-city | Add to `restore-verda-instance.sh` |
| DataCrunch container config | Verda SDK or Console | Add to deployment automation |
| SSL certificate | Upload to `/etc/ssl/` | Add to restore script |
| DNS records | Domain registrar | Document in admin-backup-restore.md |
| Docker volumes | docker-compose.yml | Commit to git |
| Environment variables | `.env` | Update in private scripts repo |
