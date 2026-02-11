# Backup Checklist for Issue #40
**Purpose:** Create backups for R2 to enable restore-verda-instance.sh restore
**Created:** 2026-02-02
**Target:** Phase 11 - Test Single GPU Instance deployment

---

## Quick Reference: What Goes Where

| Backup Item | Source Location | R2 Destination | Size | Priority |
|-------------|----------------|----------------|------|----------|
| Worker container | Docker build | `comfyume-worker-container-backups/` | ~2.5GB | 🔴 HIGH |
| Tailscale identity | `/var/lib/tailscale/` | `comfyume-cache-backups/` | <1MB | 🔴 CRITICAL |
| SSH host keys | `/etc/ssh/ssh_host_*` | `comfyume-cache-backups/` | <1KB | 🟡 MEDIUM |
| .env secrets | `/home/dev/comfyume/.env` | `comfyume-cache-backups/` | ~13KB | 🔴 HIGH |
| Models | `/mnt/sfs/models/` | `comfyume-model-vault-backups/` | ~45GB | 🟡 MEDIUM |

**Total R2 Storage:** ~48GB

---

## 1. Worker Container Backup

### Build & Export
```bash
# On Verda CPU instance
cd /home/dev/comfyume/comfyui-worker

# Build v0.11.0 worker
sudo docker compose build worker-1

# Export to tarball
sudo docker save comfyui-worker-worker-1:latest | gzip -9 > /tmp/worker-image.tar.gz

# Verify size & integrity
ls -lh /tmp/worker-image.tar.gz  # Should be ~2.5GB
gunzip -t /tmp/worker-image.tar.gz  # Test integrity
md5sum /tmp/worker-image.tar.gz > /tmp/worker-image.tar.gz.md5
```

### Upload to R2
```bash
# Load R2 credentials from .env
source /home/dev/comfyume/.env

# Upload worker image
aws s3 cp /tmp/worker-image.tar.gz \
  s3://comfyume-worker-container-backups/worker-image.tar.gz \
  --endpoint-url=$R2_ENDPOINT

# Upload checksum
aws s3 cp /tmp/worker-image.tar.gz.md5 \
  s3://comfyume-worker-container-backups/worker-image.tar.gz.md5 \
  --endpoint-url=$R2_ENDPOINT

# Verify upload
aws s3 ls s3://comfyume-worker-container-backups/ --endpoint-url=$R2_ENDPOINT
```

---

## 2. Config Backup (verda-config-backup.tar.gz)

### What to Include
- **Tailscale identity** (`/var/lib/tailscale/`) - Preserves IP 100.89.38.43 ⚠️ CRITICAL
- **SSH host keys** (`/etc/ssh/ssh_host_*`) - Server identity
- **Project .env** (`/home/dev/comfyume/.env`) - Secrets
- **Shell config** (`/home/dev/.zshrc`) - Optional convenience

### Create Tarball
```bash
# On Verda
cd /tmp

# Create config backup
sudo tar -czf verda-config-backup.tar.gz \
  -C /var/lib tailscale \
  -C /etc/ssh $(ls /etc/ssh/ssh_host_* | xargs -n1 basename) \
  -C /home/dev comfyume/.env \
  -C /home/dev .zshrc

# Verify contents
tar -tzf verda-config-backup.tar.gz | head -20

# Calculate checksum
md5sum verda-config-backup.tar.gz > verda-config-backup.tar.gz.md5
```

### Upload to R2
```bash
source /home/dev/comfyume/.env

aws s3 cp /tmp/verda-config-backup.tar.gz \
  s3://comfyume-cache-backups/verda-config-backup.tar.gz \
  --endpoint-url=$R2_ENDPOINT

aws s3 cp /tmp/verda-config-backup.tar.gz.md5 \
  s3://comfyume-cache-backups/verda-config-backup.tar.gz.md5 \
  --endpoint-url=$R2_ENDPOINT

# Verify
aws s3 ls s3://comfyume-cache-backups/ --endpoint-url=$R2_ENDPOINT
```

---

## 3. Models Backup

### Option A: Copy from SFS (if mounted)
```bash
# Check if SFS is mounted
ls /mnt/sfs/models/

# Sync to R2
source /home/dev/comfyume/.env
cd /mnt/sfs/models

aws s3 sync . s3://comfyume-model-vault-backups/ \
  --endpoint-url=$R2_ENDPOINT \
  --exclude "*.git/*" \
  --size-only
```

### Option B: Reuse Legacy Models (Compatible!)
```bash
# Models from comfy-multi v0.9.2 work with comfyume v0.11.0
# Copy from old bucket to new bucket (if needed)

aws s3 sync s3://comfy-multi-model-vault-backup/ \
  s3://comfyume-model-vault-backups/ \
  --endpoint-url=$R2_ENDPOINT
```

### Required Models for Workshop
- `checkpoints/flux2_klein_9b.safetensors` (~18GB)
- `checkpoints/flux2_klein_4b.safetensors` (~8GB)
- `checkpoints/ltx-2-19b-dev-fp8.safetensors` (~25GB)
- `text_encoders/gemma_3_12B_it.safetensors` (~20GB)
- `latent_upscale_models/ltx-2-spatial-upscaler-x2-1.0.safetensors` (~2GB)

---

## 4. User Files Backup (Optional - From Mello)

This is backed up from Mello, not Verda. Skip for Verda deployment.

```bash
# Run on Mello VPS (not Verda)
cd /home/dev/projects/comfymulti-scripts
./backup-mello.sh
```

---

## Verification Checklist

After completing backups, verify all R2 buckets:

```bash
source /home/dev/comfyume/.env

echo "=== Worker Container Bucket ==="
aws s3 ls s3://comfyume-worker-container-backups/ --endpoint-url=$R2_ENDPOINT

echo -e "\n=== Cache Bucket (Configs) ==="
aws s3 ls s3://comfyume-cache-backups/ --endpoint-url=$R2_ENDPOINT

echo -e "\n=== Models Bucket ==="
aws s3 ls s3://comfyume-model-vault-backups/ --endpoint-url=$R2_ENDPOINT --recursive | grep -E "checkpoints|text_encoders"

echo -e "\n=== User Files Bucket ==="
aws s3 ls s3://comfyume-user-files-backups/ --endpoint-url=$R2_ENDPOINT
```

### Expected Output
```
comfyume-worker-container-backups/
  ✓ worker-image.tar.gz (~2.5GB)
  ✓ worker-image.tar.gz.md5

comfyume-cache-backups/
  ✓ verda-config-backup.tar.gz (~14MB)
  ✓ verda-config-backup.tar.gz.md5

comfyume-model-vault-backups/
  ✓ checkpoints/ (~51GB total)
  ✓ text_encoders/ (~20GB)
  ✓ latent_upscale_models/ (~2GB)

comfyume-user-files-backups/
  (empty - populated by Mello backups)
```

---

## Next Steps After Backups Complete

1. **Delete Verda CPU instance** (save costs)
2. **Provision Verda H100 GPU instance** (fresh, empty)
3. **Run restore-verda-instance.sh** (restores from R2)
4. **Test worker deployment** (Phase 11)
5. **Integration testing** (Issue #18 - end-to-end workflow)

---

## Troubleshooting

### Worker image too large
- Check layer sizes: `sudo docker history comfyui-worker-worker-1:latest`
- Use multi-stage build if needed
- Compress with `gzip -9` for maximum compression

### Tailscale backup fails
- Must use sudo: `sudo tar -czf ... -C /var/lib tailscale`
- Verify directory exists: `sudo ls /var/lib/tailscale/`
- Check permissions after restore

### R2 upload fails
- Verify AWS CLI configured: `aws configure list`
- Check .env has R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
- Test connection: `aws s3 ls --endpoint-url=$R2_ENDPOINT`

### Models not found
- Check SFS mount: `mount | grep sfs`
- Verify paths: `ls /mnt/sfs/models/checkpoints/`
- Use legacy bucket if SFS empty

---

**Status:** Ready for execution once Docker build completes
**Issue:** #40
**Phase:** Phase 11 preparation
