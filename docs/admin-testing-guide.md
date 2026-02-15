**Project:** ComfyuME
**Project Desc:** ComfyUI Multi-User Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-07
**Doc Updated:** 2026-02-07

---

# Admin Testing Guide

## 1. Overview

ComfyuME uses a split architecture:
- **App server** (Verda CPU): nginx, Redis, queue-manager, admin dashboard, 20 frontend containers
- **Inference**: Serverless containers on Verda (ex. DataCrunch) (H200/B300) via direct HTTP — no local GPU workers

Three test scripts validate different aspects:

| Script | Tests | Runtime | GPU Cost |
|--------|-------|---------|----------|
| `test.sh` | Full integration (10 sections) | ~30s | None |
| `test-serverless.sh` | Serverless inference E2E | ~10s (dry-run) / 30-120s (live) | Only with live test |
| `test-connectivity.sh` | Network paths & SSL | ~20s | None |

All scripts share `test-helpers.sh` for consistent output and helper functions.

## 2. Prerequisites

- Docker and Docker Compose V2 (`docker compose`)
- `curl`, `jq` installed on host
- `.env` file configured (copy from `.env.example`)
- Services running: `docker compose up -d`
- For SSL/domain tests: `openssl` on host, DOMAIN set in .env

## 3. Quick Smoke Test

Run the main integration suite:

```bash
./scripts/test.sh
```

Expected: All 10 sections pass. Exit code 0 = all pass, 1 = failures.

## 4. Integration Tests — `test.sh`

10 sections covering the full platform:

### Section 1: Docker Services
Checks core containers (redis, queue-manager, admin) are running. Detects host vs container nginx based on `USE_HOST_NGINX`. Counts frontend containers against `NUM_USERS`.

### Section 2: Service Health
Parses Queue Manager `/health` JSON for `status`, `inference_mode`, `redis_connected`, `active_gpu`. Checks admin dashboard and nginx health endpoints.

### Section 3: Queue Manager API
Tests `/api/queue/status` JSON validity. Submits a test job via `POST /api/jobs`, retrieves it via `GET /api/jobs/{id}`, lists via `GET /api/jobs`, then cancels via `DELETE /api/jobs/{id}`. In serverless mode, the job may complete immediately (expected).

### Section 4: Redis Queue Operations
Reads queue depths (`queue:pending`, `queue:running`, `queue:completed`) via `docker compose exec redis redis-cli`.

### Section 5: Nginx Routing
Auto-detects best base URL (DOMAIN with HTTPS > DOMAIN with HTTP > localhost). Tests `/admin`, `/api/queue/status`, `/user001/` routes. Accepts 200, 301, 302, 401 as valid (auth-protected routes return 401).

### Section 6: Storage & Volumes
Checks required directories (`data/models/shared`, `data/outputs`, `data/inputs`, `data/workflows`). Counts workflow templates. Checks model subdirectories (checkpoints, text_encoders, vae, loras, latent_upscale_models).

### Section 7: Serverless Inference
Only runs when `INFERENCE_MODE=serverless`. Validates `SERVERLESS_ACTIVE`, `SERVERLESS_API_KEY`, and endpoint visibility in QM health response.

### Section 8: Configuration
Validates required env vars (`REDIS_PASSWORD`, `DOMAIN`, `QUEUE_MODE`). Adds serverless-specific vars when in serverless mode. Validates queue mode is one of: fifo, round_robin, priority.

### Section 9: Frontend Containers
Iterates all user containers (comfy-user001 through comfy-user020). Reports running count and healthy count separately. Lists unhealthy containers by name.

### Section 10: SSL & Domain
Skipped if DOMAIN is not set or is the example value. Tests HTTPS reachability, HTTP→HTTPS redirect (expects 301/308), and SSL certificate expiry (warns at <30 days).

## 5. Serverless Inference Testing — `test-serverless.sh`

Dedicated E2E test for the serverless path.

### Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Config check only, no job submission, no GPU cost |
| `--all` | Test all 4 endpoint configurations, not just active |
| `--timeout N` | Seconds to wait for job completion (default: 120) |

### Examples

```bash
# Config check only (safe, no cost)
./scripts/test-serverless.sh --dry-run

# Full E2E test with active endpoint
./scripts/test-serverless.sh

# Check all endpoints are reachable
./scripts/test-serverless.sh --dry-run --all

# Live test with shorter timeout
./scripts/test-serverless.sh --timeout 60
```

### Sections

1. **Serverless Configuration** — Validates `INFERENCE_MODE`, `SERVERLESS_ACTIVE`, `SERVERLESS_API_KEY`, counts configured endpoints
2. **Queue Manager Serverless Status** — Parses QM health for serverless-specific fields
3. **Endpoint Reachability** — HTTP request to endpoint root with auth header. Expects 200, 404, or 405 (server running). Handles cold start (000 = unreachable/cold)
4. **E2E Job Submission** — Submits test workflow via `/api/jobs`, polls for completion, cancels on timeout to avoid GPU waste

### Cold Start Handling

Serverless containers may be cold (no running instances). The test:
- Uses a generous default timeout (120s) to accommodate cold starts
- Reports unreachable endpoints as warnings, not failures
- Cancels timed-out jobs to prevent GPU credit waste

## 6. Connectivity Testing — `test-connectivity.sh`

Validates network paths between all services.

### Sections

1. **Redis Connectivity** — From host (docker compose exec), from host TCP (redis-cli), from queue-manager container (Python redis client)
2. **Queue Manager Connectivity** — From host (localhost), from user001 container (Docker network), from admin container
3. **Nginx Reverse Proxy Paths** — Admin, API, health, user001, user020 routes via localhost
4. **External Domain & HTTPS** — DNS resolution, HTTPS reachability, SSL certificate chain, SSL expiry, CN/SAN domain match
5. **Docker Network** — comfy-network exists, container count on network, all comfy containers on shared network

## 7. Load Testing

For stress testing the queue under load, use the existing load test framework:

```bash
# Default: 5 jobs per user, 100 total
./scripts/load-test.sh

# Custom configuration
JOBS_PER_USER=10 ./scripts/load-test.sh
NUM_USERS=5 JOBS_PER_USER=3 ./scripts/load-test.sh

# Validate results after load test
./scripts/validate-load-test.sh
```

See [docs/archive/testing-guide-load-test.md](./archive/testing-guide-load-test.md) for detailed load testing procedures.

## 8. Manual Verification Checklist

Browser-based checks to complement automated tests:

- [ ] Open `https://<DOMAIN>/admin` — admin dashboard loads, shows system status
- [ ] Open `https://<DOMAIN>/user001/` — ComfyUI frontend loads
- [ ] Load a workflow from the template menu — templates appear in Load dialog
- [ ] Submit a simple workflow — job appears in queue, completes (if inference available)
- [ ] Check `https://<DOMAIN>/api/queue/status` — returns valid JSON
- [ ] Verify different user sessions are isolated (user001 vs user002 outputs)

## 9. Troubleshooting by Script

### test.sh failures

| Section | Common Fix |
|---------|------------|
| Docker Services | `docker compose up -d` |
| Service Health | Check logs: `docker compose logs queue-manager` |
| Queue Manager API | Restart QM: `docker compose restart queue-manager` |
| Redis Operations | Check Redis logs: `docker compose logs redis` |
| Nginx Routing | Check nginx config: `sudo nginx -t` (host) or container logs |
| Storage & Volumes | Run `./scripts/init-user-data.sh` |
| Serverless Inference | Verify `.env` has INFERENCE_MODE, SERVERLESS_API_KEY |
| Configuration | Compare `.env` against `.env.example` |
| Frontend Containers | Check startup order: `docker compose logs user001` |
| SSL & Domain | Verify cert paths in `.env`, check expiry |

### test-serverless.sh failures

| Issue | Fix |
|-------|-----|
| INFERENCE_MODE not serverless | Set `INFERENCE_MODE=serverless` in `.env`, restart QM |
| API key rejected (401/403) | Verify `SERVERLESS_API_KEY` matches Verda dashboard |
| Endpoint unreachable (000) | Container may be cold — wait and retry, or check Verda console |
| Job timeout | Increase `--timeout`, check Verda deployment status |

### test-connectivity.sh failures

| Issue | Fix |
|-------|-----|
| Redis from host fails | Check `REDIS_BIND_IP` in `.env` |
| QM from container fails | Verify containers on same Docker network: `docker network inspect comfy-network` |
| DNS resolution fails | Check domain DNS records |
| SSL chain invalid | Renew certificate or check cert file paths |

## 10. Script Reference

| Script | Purpose | Cost | Flags |
|--------|---------|------|-------|
| `scripts/test.sh` | Full integration test (10 sections) | Free | — |
| `scripts/test-serverless.sh` | Serverless inference E2E | Free (dry-run) / GPU (live) | `--dry-run`, `--all`, `--timeout N` |
| `scripts/test-connectivity.sh` | Network connectivity | Free | — |
| `scripts/test-helpers.sh` | Shared library (sourced, not run) | — | — |
| `scripts/load-test.sh` | Multi-user load test | Free (queue only) | `NUM_USERS`, `JOBS_PER_USER` |
| `scripts/validate-load-test.sh` | Post-load-test validation | Free | — |
| `scripts/status.sh` | Quick system status | Free | — |

---

**Last Updated:** 2026-02-07
