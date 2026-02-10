**IMPORTANT: FILE REQUIRES REVIEW AFTER VERDA'S TEMP CPU INSTANCE IS CREATED — new services such as Prometheus, Grafana etc. may not be covered here.**

# Infrastructure & Technology Stack

## Servers

- **'verda' (production app server)**: Verda CPU instance (aiworkshop.art)
  - Runs: nginx, queue-manager, Redis, admin, 20 user frontends
  - Inference: serverless containers on DataCrunch (H200/B300)
- **'mello' (staging/backup)**: Hetzner VPS CAX31 - Ubuntu
  - Ampere 8 vCPU, 16GB RAM, 80GB SSD (pending downgrade -- #71)
  - Runs: backup scripts, Tailscale, git repos (containers removed)
- **Local dev machine**: MBP M4 Pro 48GB RAM

## Backups

- **Cloud storage**: Cloudflare R2 (.eu) - 3x buckets (v. cheap)
- **Local storage**: 'verda' SFS (network drive) & block storage + 'mello'
- **Hetzner Object Storage**: TBC

## Infrastructure

- **Container Runtime:** Docker + Docker Compose
- **Reverse Proxy:** Nginx (SSL termination, routing)
- **Queue:** Redis 7+ (job queue, pub/sub)
- **SSL:** Existing ahelme.net certificate via Namecheap

## Services

- **Queue Manager:** Python 3.11+ with FastAPI + WebSocket
- **Workers:** ComfyUI v0.11.0 with GPU support (serverless containers)
- **Frontends:** ComfyUI v0.11.0 web UI (COMFYUI_MODE=frontend-testing)
- **Admin:** HTML/JS dashboard

## Environment Variables

See `.env` (gitignored -- full of secrets)
