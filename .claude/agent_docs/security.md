# Security & Firewall Configuration

## VPS Firewall (UFW)

Current firewall rules lock down all ports except essential services.

**Allowed Ports:**
- **22/tcp** - SSH (rate limited)
- **80/tcp, 443/tcp** - HTTP/HTTPS (Nginx Full)
- **Mello only: 21115-21119/tcp** - RustDesk remote desktop
- **Mello only: 21116/udp** - RustDesk UDP

**Redis Security:**
- **Port 6379** - NOT exposed to public internet
- **Access:** Only via Tailscale VPN (100.99.216.71:6379)
- **Auth:** Password protected (REDIS_PASSWORD)

## User Authentication

- **Method:** HTTP Basic Auth (nginx)
- **Users:** 20 users (user001-user020)
- **Credentials:** Stored in `.env` (USER_CREDENTIALS_USER001-020)
- **htpasswd File:** `/etc/nginx/comfyui-users.htpasswd`
- **Encryption:** bcrypt (cost 10)

## Tailscale VPN

- **VPS Tailscale IP:** 100.99.216.71
- **GPU (Verda) Tailscale IP:** 100.89.38.43
- **Purpose:** Secure encrypted tunnel for Redis access between VPS and GPU workers
- **Protocol:** WireGuard (modern, fast, secure)
- **Authentication:** Run `sudo tailscale up --ssh=false`, visit the URL shown in browser to authenticate
- **Note:** Use `--ssh=false` to disable Tailscale SSH (we use regular SSH)

## SSL/TLS

- **Provider:** Existing ahelme.net certificate via Namecheap
- **Domain:** aiworkshop.art (production), comfy.ahelme.net (staging)
- **Expiry:** 2026-04-10
- **Protocols:** TLSv1.2, TLSv1.3

## Cloudflare R2 Buckets

- **Provider:** Cloudflare R2 (S3-compatible)
- **Endpoint:** `https://f1d627b48ef7a4f687d6ac469c8f1dea.r2.cloudflarestorage.com.eu`
- **Cost:** ~$3/month total (no egress fees)
- **Access:** Via AWS CLI with R2 API credentials

**Current .eu R2 Buckets (comfyume v0.11.0):**
- `comfyume-model-vault-backups` - Models (~45GB, EU)
- `comfyume-cache-backups` - Container + configs (~3GB, EU)
- `comfyume-user-files-backups` - User data from mello (~1GB, EU)
- `comfyume-worker-container-backups` - Worker images (~2.5GB, EU)

**Legacy Archive Buckets (KEEP - comfy-multi v0.9.2):**
- `comfy-multi-model-vault-backup` - Models archive
- `comfy-multi-cache` - Cache archive
- `comfy-multi-user-files` - User files archive

## Restore Scripts (Private GitHub Repo)

- **Repo:** `ahelme/comfymulti-scripts` (private)
- **URL:** https://github.com/ahelme/comfymulti-scripts
- **Local path on mello:** `/home/dev/comfymulti-scripts/`
- **Purpose:** Version-controlled setup/restore scripts for Verda instances
- **Contents:**
  - `restore-verda-instance.sh` - Production app server restore script (v0.4.0)
  - `setup-verda-solo-script.sh` - Legacy GPU worker setup (v0.3.3, archived)
  - `backup-cron.sh`, `backup-mello.sh`, `backup-verda.sh` - Backup scripts
  - `README-RESTORE.md` - Quick reference for restore scenarios
  - `archive/` - Legacy scripts (quick-start.sh, RESTORE-SFS.sh, etc.)
- **Note:** Script downloads binary files (models, container) from R2 or SFS cache
