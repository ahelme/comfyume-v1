# ComfyUMe - ComfyUI v0.11.0 Multi-User Workshop Platform

**Project:** ComfyUMe Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-11
**Doc Updated:** 2026-02-11

---

Multi-user ComfyUI platform for video generation workshops with professional filmmakers.

**Production:** [aiworkshop.art](https://aiworkshop.art) (Verda CPU instance)
**Inference:** Serverless GPU containers on Verda (ex. DataCrunch) — H200/B300

---

## Architecture

```
[Users] --> HTTPS --> [Verda CPU Instance]
                       ├── nginx (SSL, routing)
                       ├── Redis (job queue)
                       ├── queue-manager (FastAPI)
                       ├── admin dashboard
                       └── 20x user frontends (UI only)
                               │
                               ▼ HTTP (serverless)
                      [Verda GPU Containers]
                       ├── H200 141GB (spot/on-demand)
                       └── B300 288GB (spot/on-demand)
```

- **App server** runs on a Verda CPU instance (no GPU needed)
- **Inference** via `INFERENCE_MODE=serverless` — direct HTTP to Verda serverless containers
- **Storage**: SFS for models, block storage for outputs, Cloudflare R2 for backups

---

## Key Features

- 20 isolated ComfyUI web interfaces with HTTP Basic Auth
- Central job queue (FIFO/round-robin/priority)
- Serverless GPU inference (no always-on GPU cost)
- Admin dashboard for instructor
- Monitoring via Grafana, Prometheus, Loki

---

## Structure

```
comfyume-v1/
├── queue-manager/          <- FastAPI job queue + serverless dispatch
├── admin/                  <- Instructor dashboard
├── nginx/                  <- Reverse proxy (SSL, routing, auth)
├── comfyui-frontend/       <- User UI container (v0.11.0)
├── comfyui-worker/         <- GPU worker (local dev/testing only)
├── scripts/                <- Operations & testing scripts
├── data/
│   ├── workflows/          <- 5 templates (Flux2 Klein, LTX-2)
│   ├── models/shared/      <- Model storage (SFS on Verda)
│   ├── user_data/          <- Per-user settings & custom nodes
│   ├── inputs/             <- User uploads
│   └── outputs/            <- Generated files
├── docs/                   <- Admin & testing guides
├── docker-compose.yml      <- Service orchestration
└── .env.example            <- Configuration template
```

---

## Configuration

Uses consolidated `.env` file. See `.env.example` for all variables.

**Key settings:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `INFERENCE_MODE` | `serverless` | Serverless GPU inference (production) |
| `SERVERLESS_ACTIVE` | `h200-spot` | Active GPU endpoint selector |
| `SERVER_MODE` | `dual` | Split app/inference servers |
| `COMFYUI_MODE` | `frontend-testing` | UI only on app server |
| `DOMAIN` | `aiworkshop.art` | Production domain |

For production `.env`, use the consolidated file from [comfymulti-scripts](https://github.com/ahelme/comfymulti-scripts) (private repo).

---

## Documentation

- **Issues:** https://github.com/ahelme/comfyume-v1/issues
- **Master Task List:** [Issue #1](https://github.com/ahelme/comfyume-v1/issues/1)
- **Old Repo:** https://github.com/ahelme/comfyume (advanced but broken — cherry-picking from here)

---

**Main Branch:** main
**Updated:** 2026-02-11
