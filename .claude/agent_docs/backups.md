# Backup & Restore

**Doc Updated:** 2026-02-16

**Source:** Adapted from `comfyume/docs/admin-backup-restore.md` (original repo)

---

## CRITICAL: Object Storage Is Append-Only

**NEVER delete backups from R2 or Hetzner Object Storage.** Only add new dated files alongside existing ones. Old backups stay untouched indefinitely. Rotation policies below apply to SFS cache only.

---

## Storage Strategy

| Storage | Purpose | Persistence | Check Order |
|---------|---------|-------------|-------------|
| **SFS** (PROD or CLONE) | Models, cache, config backups | Persistent (NFS) | 1st — fast, local |
| **Cloudflare R2** (.eu) | Complete off-site backup | Permanent, append-only | 2nd — fallback |
| **Hetzner Object Storage** | Finland-local backup (TBC, #42) | Permanent, append-only | TBC |
| **Mello VPS** | Working backups, scripts source | Permanent | 3rd — scripts |
| **Block vol backup** | DR snapshot of PROD OS | Cold storage | Emergency only |

### Model Source Priority

| Environment | Primary | Fallback |
|-------------|---------|----------|
| **Production** | PROD_SFS | R2 |
| **Testing/Staging** | CLONE_SFS | R2 |

---

## R2 Buckets — Backup Schedule & Retention

**Endpoint:** `https://f1d627b48ef7a4f687d6ac469c8f1dea.eu.r2.cloudflarestorage.com` (note `.eu`!)

### 1. `comfyume-cache-backups`

Config tarballs: /home/dev, /root, nginx, tailscale, SSL, SSH keys (~6.5GB)

| | SFS | R2 |
|---|---|---|
| **Naming** | `config/<name>-<YYYY-MM-DD>.tar.gz` | `config/<name>-<YYYY-MM-DD>.tar.gz` |
| **Schedule** | Hourly | 4x daily: 2am, 6am, 2pm, 6pm |
| **Retention** | 5 daily, 3 weekly, 3 monthly, rotate | 5 daily, 3 weekly, 3 monthly, rotate |

### 2. `comfyume-model-vault-backups`

Models: checkpoints, diffusion_models, controlnet, loras, text_encoders, vae (~192GB, 28 files)

| | R2 |
|---|---|
| **Naming** | Retain original filenames (`<model_type>/<filename>.safetensors`) |
| **Schedule** | New models only (on addition) |
| **Retention** | Flat, matches SFS folder structure, never deleted |

### 3. `comfyume-worker-container-backups`

Container images: frontend (1x shared), worker, queue-manager, nginx, admin (~20GB)

| | SFS | R2 |
|---|---|---|
| **Naming** | `<image-name>-<YYYY-MM-DD>.tar.gz` | `<image-name>-<YYYY-MM-DD>.tar.gz` |
| **Schedule** | Daily at 3am | Daily at 4am |
| **Retention** | 1 daily, 1 monthly, rotate | 1 daily, 3 weekly, 3 monthly, rotate |

### 4. `comfyume-user-files-backups`

User workflows, custom nodes, etc. (variable size)

| | R2 |
|---|---|
| **Naming** | `user-data-<YYYY-MM-DD-HH>.tar.gz` |
| **Schedule** | Hourly |
| **Retention** | 5 daily, 3 weekly, 3 monthly, rotate |

---

## Backup Scripts

**NOTE: All three scripts need updating to match the schedule and retention policies above.** Current scripts use `-latest.tar.gz` naming (overwrite) instead of dated filenames, and have no rotation logic. See comfymulti-scripts #45.

| Script | Runs From | Destination | When | Status |
|--------|-----------|-------------|------|--------|
| `backup-cron.sh` | Verda (cron) | SFS cache | Hourly | Needs update: dated naming, rotation |
| `backup-verda.sh` | Mello (SSH) | Mello + R2 | Before shutdown | Needs update: dated naming, rotation, all 4 buckets |
| `backup-mello.sh` | Mello | R2 | Before shutdown | Needs update: dated naming, rotation |

**Location:** `ahelme/comfymulti-scripts` (private repo)

### What Gets Backed Up

| Data | `backup-cron.sh` | `backup-verda.sh` | `backup-mello.sh` | Destination |
|------|:-:|:-:|:-:|-----------|
| Tailscale identity | Yes | Yes | - | SFS / Mello |
| SSH host keys | Yes | Yes | - | SFS / Mello |
| Fail2ban, UFW configs | Yes | Yes | - | SFS / Mello |
| Project .env | Yes | Yes | - | SFS / Mello |
| /home/dev/ | - | Yes | - | Mello + R2 |
| Container images | - | Yes | - | Mello + R2 |
| Models (.safetensors) | - | Yes | - | R2 |
| User workflows/outputs | - | - | Yes | R2 |
| User credentials | - | - | Yes | Private repo |

---

## Restore Priority

When restoring to a new instance, the restore script checks sources in this order:

| File Type | Check Order | Rationale |
|-----------|-------------|-----------|
| **Models** (~192GB) | SFS → R2 | Large, live on SFS |
| **Config, identity, container** | /root/ → SFS → R2 | Extracted to instance |
| **Scripts** | /root/ → SFS → GitHub | Small, versioned |

### SFS Requirement

SFS must be explicitly shared with each instance via Verda console "share settings" before mounting. Being in the same location is not enough.

### Tailscale Identity

Must be restored BEFORE starting Tailscale — otherwise gets a new IP. Expected IP: **100.89.38.43**

---

## Disaster Recovery

| Asset | Backup | Location |
|-------|--------|----------|
| **PROD_OS** | `BACKUP_2026-02-16-PROD_OS-hiq7F8JM` (block-vol 009) | FIN-01, 100GB, detached |
| **Models** | PROD_SFS + CLONE_SFS + R2 | 3 copies |
| **Config** | SFS cache + R2 + Mello | 3 copies |
| **Code** | GitHub (comfyume-v1 + comfymulti-scripts) | Cloud |

---

## Quick Commands

```bash
# Check R2 bucket contents
ENDPOINT="https://f1d627b48ef7a4f687d6ac469c8f1dea.eu.r2.cloudflarestorage.com"
aws --endpoint-url $ENDPOINT s3 ls s3://comfyume-model-vault-backups/ --recursive --human-readable
aws --endpoint-url $ENDPOINT s3 ls s3://comfyume-cache-backups/ --recursive --human-readable
aws --endpoint-url $ENDPOINT s3 ls s3://comfyume-worker-container-backups/ --recursive --human-readable
aws --endpoint-url $ENDPOINT s3 ls s3://comfyume-user-files-backups/ --recursive --human-readable

# Run manual backup from Mello
cd ~/projects/comfymulti-scripts
./backup-verda.sh        # Verda → Mello + R2
./backup-mello.sh        # Mello → R2

# SFS-prod auto-mounts on reboot (fstab entry added 2026-02-16)
```

---

## Related

- [admin-backup-restore.md](../../docs/admin-backup-restore.md) — Original detailed guide (comfyume repo)
- [gotchas.md](./gotchas.md) — SFS pseudopath risk, share settings requirement
- [infrastructure.md](./infrastructure.md) — SFS volumes, instances, storage
- comfymulti-scripts #45 — Restore script updates needed
- comfyume-v1 #42 — Hetzner Object Storage backup (pending)
