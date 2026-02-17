**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / staging.aiworkshop.art / testing.aiworkshop.art
**Doc Created:** 2026-02-17
**Doc Updated:** 2026-02-17

---

# ComfyUI Debugging Reference

All available methods for diagnosing issues in our multi-user serverless deployment.

---

## 1. ComfyUI CLI Flags

Add to container startup command (docker-compose or Verda serverless `cmd`).

### Logging & Verbosity

| Flag | Effect |
|------|--------|
| `--verbose` | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--log-stdout` | Output logs to stdout instead of stderr (useful for Docker log capture) |

### GPU Memory (serverless workers only)

| Flag | Effect |
|------|--------|
| `--highvram` | Load full models into VRAM (~24GB+) |
| `--normalvram` | Default balanced mode |
| `--lowvram` | Optimize for limited VRAM (~6GB), CPU offloading |
| `--novram` | Aggressive CPU offloading, minimal VRAM |
| `--reserve-vram N` | Reserve N GB of VRAM (prevent OOM) |
| `--force-fp16` | Force half-precision (saves VRAM, may affect quality) |

### Paths (relevant to our architecture)

| Flag | Current Usage |
|------|--------------|
| `--extra-model-paths-config` | `/mnt/sfs/extra_model_paths.yaml` (serverless) |
| `--output-directory` | `/mnt/sfs/outputs` (serverless, SFS shared storage) |
| `--user-directory` | `/comfyui/user/default` (frontends) |

### Useful for Debugging

| Flag | When to Use |
|------|------------|
| `--disable-all-custom-nodes` | Isolate whether issue is in custom nodes or core |
| `--cpu` | Already used by frontends (UI-only, no GPU) |
| `--deterministic` | Reproducible results (slower) |

---

## 2. ComfyUI API Endpoints

Accessible on frontend containers (`:8188`) and serverless containers (via Verda endpoint).

### Core

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/system_stats` | GET | Python version, OS, GPU info, memory |
| `/object_info` | GET | All loaded node types and their schemas |
| `/object_info/{node}` | GET | Schema for a specific node |
| `/extensions` | GET | List of loaded extensions |
| `/queue` | GET | `queue_pending` and `queue_running` arrays |
| `/prompt` | POST | Submit workflow, returns `prompt_id` |
| `/history/{prompt_id}` | GET | Execution status, outputs, error messages |
| `/api/userdata?dir=workflows` | GET | Available workflow templates |
| `/embeddings` | GET | Available embeddings/LoRAs |

### Key Fields in `/history/{prompt_id}`

```json
{
  "prompt_id": {
    "status": {
      "completed": true,
      "status_str": "success",
      "messages": [["execution_error", {"message": "..."}]]
    },
    "outputs": { "node_id": { "images": [...] } },
    "execution_time": 45.2
  }
}
```

- `status.completed` = false + `status.status_str` = "error" → execution failed
- `status.messages` contains error details (node name, exception, traceback)
- Empty response (`{}`) → prompt_id not found on this instance

---

## 3. Queue Manager API (ComfyuME-specific)

Port 3000, behind nginx at `/api/`.

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/health` | GET | Redis status, inference mode, active GPU, queue depth, uptime |
| `/api/queue/status` | GET | Pending/running/completed/failed counts |
| `/api/jobs` | GET | List all jobs |
| `/api/jobs/{id}` | GET | Single job status + result |
| `/api/jobs` | POST | Submit job (used by `queue_redirect` extension) |
| `/api/jobs/{id}` | DELETE | Cancel job |
| `/api/jobs/{id}/priority` | PATCH | Change priority |

---

## 4. Browser-Side Debugging

### Chrome DevTools (F12)

**Console tab:**
- Filter by ERROR/WARN
- Watch for CORS errors (red "access denied" messages)
- WebSocket messages from `serverless_proxy` extension
- `queue_redirect` job submission logs

**Network tab:**
- Filter `status:500` for server errors
- Filter `method:POST` for job submissions
- Watch `/api/jobs` (POST) → response should contain `job_id`
- Watch `/history/{prompt_id}` → should eventually return results
- Watch `/view?filename=...` → image download (404 = image not on this instance)

**Application tab:**
- LocalStorage: workflow cache, user preferences
- Check for stale cached data

### Browser Console Log Tracking

See GH #63 — we're tracking browser console outputs to identify frontend issues.

---

## 5. Docker Container Logs

### Commands

```bash
# Real-time follow
docker logs comfy-queue-manager -f
docker logs comfy-nginx -f
docker logs comfy-user001 -f

# Last N lines
docker logs comfy-queue-manager -n 100

# Since time
docker logs comfy-queue-manager --since 5m

# Filter for errors
docker logs comfy-queue-manager 2>&1 | grep -i 'error\|fail\|exception'
```

### What to Look For

| Container | Key Patterns |
|-----------|-------------|
| `comfy-queue-manager` | `Serverless job from`, `History poll`, `status=error`, `timeout` |
| `comfy-nginx` | `502 Bad Gateway`, `504 Gateway Timeout`, `pread() failed` |
| `comfy-user001..020` | `Model not found`, `No such file`, custom node errors |
| `comfy-redis` | `OOM`, `maxmemory`, connection refused |
| `comfy-admin` | API errors, Docker SDK errors |

### Log Level Control

Set `QUEUE_MANAGER_LOG_LEVEL=DEBUG` in `.env` and restart queue-manager for verbose logging.

---

## 6. Monitoring Stack (Verda)

| Tool | Port | Access | Use For |
|------|------|--------|---------|
| Prometheus | :9090 | https://prometheus.aiworkshop.art | Container metrics, resource usage |
| Grafana | :3001 | https://grafana.aiworkshop.art | Dashboards, visual metrics |
| Loki | :3100 | via Grafana or SSH | Log aggregation, search |
| cAdvisor | :8081 | via Prometheus | Per-container resource breakdown |
| Promtail | :9080 | ships to Loki | Docker log collection |
| Portainer | :9443 | https://portainer.aiworkshop.art | Container management UI |
| Dry | CLI | SSH | Docker TUI |

### Useful Prometheus Queries

```promql
# Container restarts
container_start_time_seconds{name=~"comfy-.*"}

# Memory pressure
container_memory_usage_bytes{name=~"comfy-.*"}

# CPU utilization
rate(container_cpu_usage_seconds_total{name=~"comfy-.*"}[5m])
```

### Useful Loki Queries

```logql
# Serverless errors in QM
{container_name="comfy-queue-manager"} |= "error"

# Model loading issues
{container_name=~"comfy-user.*"} |~ "model.*not found|No such file"

# Nginx upstream errors
{container_name="comfy-nginx"} |~ "502|504|upstream"
```

### Skills

12 `/verda-*` skills available: `/verda-status`, `/verda-ssh`, `/verda-loki`, `/verda-prometheus`, `/verda-grafana`, `/verda-monitoring-check`, `/verda-containers`, `/verda-debug-containers`, `/verda-dry`, `/verda-terraform`, `/verda-open-tofu`, `/verda-logs`

---

## 7. Serverless-Specific Debugging

### The Load Balancer Problem

Verda serverless containers are **load-balanced**. Each HTTP request may hit a **different** container instance. This means:

- `POST /prompt` → instance A (accepts, starts executing)
- `GET /history/{prompt_id}` → instance B (never saw this prompt, returns `{}`)

**Symptom:** Prompt accepted (200 OK), but history polling returns empty keys forever until timeout.

**Current workaround:** SFS-based delivery. Images written to shared NFS (`/mnt/sfs/outputs/`), QM copies from SFS to local `/outputs/userXXX/`.

**Diagnosis:** If QM logs show `prompt_id not in history. Keys: []` for 600s → this is the load balancer issue.

### Verda SDK (on Verda server)

```python
from verda import Verda
client = Verda()

# List all deployments
deps = client.containers.get_deployments()
for d in deps:
    print(f"{d.name}: {d.status}, replicas: {d.current_replicas}")

# Get specific deployment
dep = client.containers.get_deployment("comfyume-vca-ftv-h200-spot")
```

**Limitation:** No container logs, no exec/shell into serverless containers via SDK or API.

### Testing Serverless Endpoint Directly

```bash
# Health check
curl -s -H "Authorization: Bearer $SERVERLESS_API_KEY" \
  https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/system_stats

# Check if models are visible
curl -s -H "Authorization: Bearer $SERVERLESS_API_KEY" \
  https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/object_info | jq 'keys | length'

# Submit test prompt directly
curl -s -X POST -H "Authorization: Bearer $SERVERLESS_API_KEY" \
  -H "Content-Type: application/json" \
  https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/prompt \
  -d '{"prompt": {...}}'
```

---

## 8. Common Debugging Workflows

### Job Won't Execute

1. `curl localhost:3000/api/queue/status` — check queue depth
2. `docker logs comfy-queue-manager -f` — watch for job submission
3. Check Redis: `docker exec comfy-redis redis-cli -a $REDIS_PASSWORD ping`
4. Check serverless endpoint: `curl -H "Bearer $KEY" $ENDPOINT/system_stats`

### Job Accepted but No Result (Current Issue — #101)

1. QM logs: `grep 'History poll' logs` — if keys always `[]`, likely load balancer routing issue
2. Check SFS for output files: `ls -la /mnt/sfs/outputs/`
3. Check serverless replica count via Verda SDK
4. Test direct endpoint query: `GET /history/{prompt_id}` with auth header

### Images Not Appearing

1. Check SFS mount: `mount | grep /mnt/sfs`
2. Check permissions: `ls -ld /mnt/sfs/outputs/` (should be `drwxrwxrwt`, 1777)
3. Check QM logs for `fetch_serverless_images`
4. Check if `--output-directory /mnt/sfs/outputs` is in serverless startup command

### Model Loading Fails

1. Check YAML: `cat /mnt/sfs/extra_model_paths.yaml`
2. Verify files exist: `ls -la /mnt/sfs/models/shared/{folder_type}/`
3. Check container mount: `docker inspect comfy-user001 --format='{{range .Mounts}}...'`
4. Remember: YAML key IS the folder type verbatim (no aliasing except `unet`→`diffusion_models`, `clip`→`text_encoders`)

### Server Unresponsive (Emergency)

1. Hard reset via hosting provider dashboard
2. SSH in immediately
3. `sudo docker stop $(sudo docker ps -q --filter "name=comfy")`
4. Start services one at a time

---

## 9. Known Issues & Gaps

| Issue | Status | Notes |
|-------|--------|-------|
| QM doesn't log "prompt never appeared" timeout (#48) | GAP | Only logs `status=error`, not empty history timeout |
| No serverless container logs via API | LIMITATION | Verda SDK has no log/exec access |
| `--output-directory` missing from 3 of 4 deployments (#54) | TODO | Only H200-spot has it; fix via OpenTofu on testing server |
| Load balancer breaks history polling | KNOWN | SFS workaround in place, but polling still fails |
| Browser console errors not tracked | IN PROGRESS | #63 — logging browser console outputs |
| `--verbose` flag not set on any container | OPPORTUNITY | Would give more detailed node execution logs |

---

## 10. Quick Reference

```bash
# Full system health check
ssh dev@100.89.38.43 "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep comfy"

# QM health
curl -s https://aiworkshop.art/api/health | jq

# Queue status
curl -s -u admin:$ADMIN_PASSWORD https://aiworkshop.art/api/queue/status | jq

# Recent QM errors
ssh dev@100.89.38.43 "docker logs comfy-queue-manager 2>&1 | grep -i error | tail -20"

# SFS outputs
ssh dev@100.89.38.43 "ls -la /mnt/sfs/outputs/ | tail -10"

# Monitoring stack health
# Use /verda-monitoring-check skill
```
