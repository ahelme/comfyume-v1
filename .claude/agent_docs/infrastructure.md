# Infrastructure & Technology Stack

**Doc Updated:** 2026-02-15

---

## Environments

Three-tier promotion: testing → staging → production. Blue-green deploy via DNS switch (TTL 60s).

| Environment | Domain | Instance | SFS | SSL | Lifecycle |
|---|---|---|---|---|---|
| **Production** | aiworkshop.art | Verda CPU (quiet-city, persistent) | SFS-prod | Namecheap (exp 2026-04-10) | persistent |
| **Staging** | staging.aiworkshop.art | Verda CPU (ephemeral) | SFS-clone | Let's Encrypt | spin up / tear down |
| **Testing** | testing.aiworkshop.art | Verda CPU (ephemeral) | SFS-clone | Let's Encrypt | spin up / tear down |

Each Verda environment runs identical stack: nginx, queue-manager, Redis, admin, 20 user frontends.

## Machines

| Machine | Role | Specs | Notes |
|---|---|---|---|
| **Verda (production)** | Live workshop platform | CPU.8V.32G, Ubuntu 24.04 | quiet-city-purrs-fin-01 (65.108.33.101), Tailscale 100.89.38.43 |
| **Verda (testing)** | Model vault check (#38) | 1x RTX A6000, 10 CPU, 60GB RAM | testing-sharp-book-cracks-fin-01 (135.181.63.140). Spot €0.1446/hr. Ephemeral. |
| **Verda (staging/testing)** | Pre-production validation | CPU instance (ephemeral) | Created as needed, deleted when done |
| **Mello** | Dev machine, user dir, Tailscale node | Hetzner CAX31, 8 vCPU, 16GB, 80GB | comfy.ahelme.net (100.99.216.71). NO containers — dev dirs + scripts only |
| **Verda Serverless** | Serverless GPU inference | H200 141GB / B300 288GB | Spot or on-demand, INFERENCE_MODE=serverless |
| **Local** | Development | MBP M4 Pro 48GB | Aeon's laptop |

## Storage

| Storage | Type | Purpose | Attached to |
|---|---|---|---|
| **SFS-prod** | Verda SFS (NFS) | Models (~172GB), cache, backups — stable, trusted | Production instance only |
| **SFS-clone** | Verda SFS (NFS) | Clone of SFS-prod — safe to experiment, doubles as model backup | Testing + staging instances |
| **Scratch disk** | Verda Block Storage | Ephemeral: user outputs, inputs | One per instance |
| **OS disk** | Verda Block Storage | Ubuntu OS + Docker | One per instance |
| **R2 buckets** | Cloudflare R2 (.eu) | Off-site backups: models, config, worker image, user files | Remote (3 buckets) |
| **Mello** | Hetzner SSD | Git repos, dev scripts | Mello only |

### Resource Naming Convention

All Verda resources use environment prefixes in console names: `PROD_*` (production), `CLONE_*` (cloned from prod, testing+staging shared), `STAG_*` (staging-only), `TEST_*` (testing-only), `UNUSED_*` (orphaned, pending deletion). Full registry in comfymulti-scripts `infrastructure-registry.md`.

## Services (per Verda environment)

| Service | Technology | Port | Container |
|---|---|---|---|
| **Reverse Proxy** | Nginx | 443 (HTTPS), 80 (redirect) | comfy-nginx |
| **Queue Manager** | Python 3.11+ / FastAPI / WebSocket | 3000 | comfy-queue-manager |
| **Redis** | Redis 7+ | 6379 (Tailscale only) | comfy-redis |
| **Admin Dashboard** | HTML/JS | via nginx /admin | comfy-admin |
| **User Frontends** | ComfyUI v0.11.0 (COMFYUI_MODE=frontend-testing) | 8501-8520 | comfy-user001 to comfy-user020 |
| **GPU Workers** | ComfyUI v0.11.0 (serverless) | 8188 | Verda Serverless containers |

Total containers per environment: 24 (nginx + redis + queue-manager + admin + 20 frontends)

**Serverless inference flow:** QM POSTs `/prompt` → polls `/api/history/{prompt_id}` → image saved to SFS by container → QM copies from `/mnt/sfs/outputs/` to `/outputs/userXXX/` → frontend serves locally. No direct HTTP back to containers (load-balanced, different instance each request).

## Dev Directories (Mello — separate clones)

| Directory | Repo | Branch | Purpose |
|---|---|---|---|
| `testing-main` | comfyume-v1 | feature branches | Active development, break things |
| `testing-scripts` | comfymulti-scripts | feature branches | Script development |
| `staging-main` | comfyume-v1 | `staging` | Validated code, pre-production |
| `staging-scripts` | comfymulti-scripts | `staging` | Validated scripts |
| `production-main` | comfyume-v1 | `main` | Production-ready, deployed code |
| `production-scripts` | comfymulti-scripts | `main` | Proven scripts ONLY |

## Blue-Green Deploy Process

1. Build & validate on staging instance (staging.aiworkshop.art)
2. Final check: optionally mount SFS-prod on staging to verify with real models
3. Switch DNS: `aiworkshop.art` A record → staging instance IP
4. Old production stays alive as rollback
5. Once confident → tear down old instance, staging becomes new production

## Environment Variables

See `.env` (gitignored — full of secrets). Option A/B/C pattern for Redis config (see .env comments).
