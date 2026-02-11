# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** PRODUCTION LIVE. Full stack running, HTTPS, all containers healthy.
Serverless inference CONFIRMED — QM sends to DataCrunch H200, gets 200 OK.
BUT: default_workflow_loader has a canvas null bug preventing auto-load.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) - Priority tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## IMMEDIATE NEXT STEPS

1. **Commit canvas-wait fix** — `loader.js` has been fixed (polls for `app.canvas` before `loadGraphData`), deployed to user dirs but NOT yet committed. File: `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js`
2. **Test the fix** — User needs to: hard refresh (Cmd+Shift+R), clear localStorage (`localStorage.removeItem('comfy_workflow_loaded')`), reload. Workflow should auto-load.
3. **Test inference end-to-end** — Queue Prompt should POST to /api/jobs → QM → serverless GPU. Check QM logs: `docker logs comfy-queue-manager 2>&1 | grep -v "GET /health" | tail -20`
4. **Factor out comfyume layer (#12)** — Move custom nodes + entrypoint to `comfyui-comfyume-layer/` for clean separation from upstream ComfyUI
5. **Complete app flow doc (#8)** — trace full path from Queue Prompt to serverless inference
6. **Complete infrastructure config map (#9)** — declarative checklist of all server config
7. **Investigate .env variable warnings (#7)** — y1w, HUFr7 etc.
8. **Run setup-monitoring.sh** — Prometheus, Grafana, Loki, Promtail, cAdvisor

---

## KEY FINDINGS THIS SESSION

**Volume mount gotcha (CRITICAL):**
- docker-compose.users.yml mounts host dir over container's custom_nodes/
- Host dir was empty → queue_redirect and default_workflow_loader missing
- Fix: Dockerfile COPY to staging area + entrypoint deploys on every start (self-healing)

**Nginx startup crash (CRITICAL):**
- Static upstream blocks require DNS at startup → crash if users not ready
- Fix: resolver 127.0.0.11 + variables for request-time DNS resolution

**Docker creates directories for missing file mounts:**
- Hit THREE times: redis.conf, SSL certs, .htpasswd
- Fix: ensure files exist before compose up, or use configs/secrets

**Serverless inference works:**
- QM at https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot
- API key configured, H200 spot, 300s timeout
- Confirmed 200 OK response from DataCrunch

---

## KEY FILES

| File | Purpose |
|------|---------|
| `comfyui-frontend/Dockerfile` | Frontend build — includes self-healing custom nodes mechanism |
| `comfyui-frontend/docker-entrypoint.sh` | Two-stage custom nodes: restore defaults + deploy extensions |
| `comfyui-frontend/custom_nodes/queue_redirect/web/redirect.js` | Intercepts Queue Prompt → POST /api/jobs |
| `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js` | Auto-loads Flux2 Klein 9B workflow (canvas-wait fix pending commit) |
| `queue-manager/main.py` | FastAPI app — submit_job() routes to serverless |
| `queue-manager/config.py` | Pydantic settings — serverless endpoint config |
| `nginx/docker-entrypoint.sh` | Dynamic DNS resolver for user containers |

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` on both repos
- [ ] Can you SSH to Verda? `ssh root@65.108.33.101`
- [ ] Read `.claude/agent_docs/progress-mello-team-one-dev.md` top section
- [ ] Check container health: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | sort'`
- [ ] Discuss priorities with user
