# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** PRODUCTION LIVE. Full stack running, HTTPS, all 24 containers healthy.
Serverless inference CONFIRMED — QM sends to DataCrunch H200, gets 200 OK.
BUT: Output images stay on serverless container — they never reach the user's browser.
default_workflow_loader: DISABLED on server (canvas null errors, non-blocking).
redirect.js: Has floating status banner showing GPU progress (deployed to server, not yet committed).

**DEPLOYMENT DRIFT WARNING:** Several files were SCP'd directly to server without going through git.
See Progress Report 46 in `progress-mello-team-one-dev.md` for full deployment inventory.
Key drift: redirect.js (status banner) and main.py (response logging) are on server + local dev but NOT in git.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) - Priority tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## IMMEDIATE NEXT STEPS

1. **Commit + sync deployment** — redirect.js and main.py have uncommitted changes. Commit, push, pull on server. See Progress Report 46 for full drift map.
2. **Solve image delivery** — THE BIG GAP: serverless GPU generates images but they're saved to the serverless container's local filesystem. ComfyUI's /prompt endpoint returns `{prompt_id, number}`, not images. Images normally come via WebSocket, but QM is the HTTP client, not the user's browser. Need to figure out how DataCrunch returns results and pipe them to the user.
3. **Test redirect.js banner** — User needs: hard refresh (Cmd+Shift+R), click Queue Prompt. Should see floating dark banner: "Sending to GPU..." → "Processing on GPU... 45s" → "Inference complete! (72s)"
4. **Check QM response logging** — After a job completes, check `docker logs comfy-queue-manager 2>&1 | grep "response keys"` to see what DataCrunch returns. This tells us if image data is in the response.
5. **Factor out comfyume layer (#12)** — Move custom nodes + entrypoint to `comfyui-comfyume-layer/`
6. **Complete app flow doc (#8)** and infrastructure config map (#9)
7. **Investigate .env variable warnings (#7)** — y1w, HUFr7 etc.
8. **Run setup-monitoring.sh** — Prometheus, Grafana, Loki, Promtail, cAdvisor

---

## KEY FINDINGS THIS SESSION

**Image delivery gap (CURRENT BLOCKER):**
- Serverless inference completes (HTTP 200 OK from DataCrunch), QM returns `status: completed`
- But ComfyUI on the serverless container saves images to its LOCAL filesystem
- The `/prompt` API returns only `{prompt_id, number}` — no image data
- ComfyUI normally delivers images via WebSocket to the connected client
- In our architecture, QM is the "client" talking to serverless, not the user's browser
- The user's browser never connects to the serverless container's WebSocket
- Possible solutions: output in HTTP response, shared storage, S3/R2 upload, WebSocket relay

**Volume mount gotcha (SOLVED):**
- docker-compose.users.yml mounts host dir over container's custom_nodes/
- Fix: Dockerfile COPY to staging area + entrypoint deploys on every start (self-healing)
- CAUTION: Container recreation will re-enable default_workflow_loader (currently .disabled)

**Deployment drift:**
- Files SCP'd directly to server bypass git → unreproducible state
- If server dies, docker compose up uses stale images
- Need: commit → push → pull on server → rebuild → recreate

---

## KEY FILES

| File | Purpose | Deployment Status |
|------|---------|-------------------|
| `comfyui-frontend/custom_nodes/queue_redirect/web/redirect.js` | Intercepts Queue Prompt → POST /api/jobs + status banner | **DRIFTED** — server has new version, git has old |
| `queue-manager/main.py` | FastAPI app — submit_job() routes to serverless | **DRIFTED** — server has response logging, git has old |
| `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js` | Auto-loads workflow (canvas-wait fix) | **DISABLED** on server (.disabled), committed in git |
| `comfyui-frontend/Dockerfile` | Frontend build — self-healing custom nodes | Committed ✅ (c613a06) |
| `comfyui-frontend/docker-entrypoint.sh` | Two-stage custom nodes deployment | Committed ✅ (c613a06) |
| `queue-manager/config.py` | Pydantic settings — serverless endpoint config | In sync ✅ |
| `nginx/docker-entrypoint.sh` | Dynamic DNS resolver for user containers | Committed ✅ (93bf1a1) |

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` on both repos — **expect 2 modified files (redirect.js, main.py)**
- [ ] Can you SSH to Verda? `ssh root@65.108.33.101`
- [ ] Read `.claude/agent_docs/progress-mello-team-one-dev.md` top section
- [ ] Check container health: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | sort'`
- [ ] Discuss priorities with user — image delivery is the big unsolved problem
