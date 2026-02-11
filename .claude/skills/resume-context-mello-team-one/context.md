# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** Site is LIVE (HTTPS, auth, all containers healthy). Inference pipeline
is almost working but blocked by a bug in our custom extension code.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) - Priority tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## IMMEDIATE NEXT STEPS (IN ORDER)

### 1. Fix default_workflow_loader (PRIORITY — 3 line change)

**File:** `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js`

**Problem:** Uses `app.loadWorkflowFromURL(url)` which doesn't exist in ComfyUI v0.11.0.
This is OUR custom code, not ComfyUI's — a previous Claude wrote it targeting a wrong API.

**Fix:** Replace the `app.loadWorkflowFromURL()` call with:
```javascript
const response = await fetch(apiUrl);
if (!response.ok) throw new Error(`Failed to fetch: ${response.status}`);
const workflowData = await response.json();
await app.loadGraphData(workflowData);
```

**v0.11.0 API reference** (discovered via Chrome DevTools):
- `app.loadGraphData(jsonObject)` — loads workflow graph data
- `app.loadApiJson(apiData, name)` — loads API format
- `app.graphToPrompt()` — converts graph to API format
- `app.queuePrompt` — our queue_redirect overrides this (WORKING)

**Workflow files exist** at `data/user_data/user001/default/workflows/`:
flux2_klein_9b_text_to_image.json, flux2_klein_4b_text_to_image.json, etc.

### 2. Rebuild frontend image + redeploy

Dockerfile has been updated (COPY custom_nodes/ to /build/custom_nodes/) but NOT committed yet.
After fixing loader.js:
```bash
# Commit changes
git add comfyui-frontend/ && git commit

# On server: rebuild and redeploy
ssh root@65.108.33.101
cd /home/dev/comfyume-v1 && git pull
docker build -t comfyume-frontend:v0.11.0 comfyui-frontend/
docker compose restart user001  # test one first
# verify in browser, then restart all
```

### 3. Also rebuild nginx image (dynamic DNS fix from 93bf1a1)
```bash
docker compose build nginx
docker compose --profile container-nginx up -d nginx
```

### 4. Continue app flow doc (#8) and infrastructure map (#9)

### 5. Remaining cleanup
- .env variable warnings (y1w, HUFr7 — #7)
- Old Docker images (~80GB)
- Monitoring stack (setup-monitoring.sh)

---

## WHAT WE DEBUGGED THIS SESSION

**Full inference flow traced via code + Chrome DevTools:**

1. User clicks "Run" in ComfyUI browser UI
2. `queue_redirect/web/redirect.js` intercepts `app.queuePrompt` — **WORKING**
3. Calls `app.graphToPrompt()` → returns `{output: {}}` because canvas is empty
4. POSTs to `/api/jobs` via fetch — **WORKING**
5. Nginx routes `/api/` to queue-manager:3000 — **WORKING**
6. QM `main.py:submit_job()` validates workflow — rejects empty dict with 422
7. In serverless mode: would call `submit_to_serverless()` → POST to DataCrunch endpoint

**Root cause of empty canvas:** `default_workflow_loader` fails because
`app.loadWorkflowFromURL` doesn't exist in v0.11.0. Without a default workflow
loaded, the canvas is empty and Run submits `{}`.

**Also fixed this session:**
- Nginx: dynamic DNS resolution (resolver 127.0.0.11), SSL cert, .htpasswd
- Custom nodes: volume mount gotcha — copied to all 20 user dirs
- Dockerfile: added COPY custom_nodes/ for self-healing entrypoint

---

## KEY FILES

| File | Purpose |
|------|---------|
| `comfyui-frontend/custom_nodes/queue_redirect/web/redirect.js` | JS override of queuePrompt — WORKING |
| `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js` | Auto-loads workflow — BROKEN (needs fix) |
| `comfyui-frontend/Dockerfile` | Build — UPDATED (COPY custom_nodes/) but not committed |
| `comfyui-frontend/docker-entrypoint.sh` | Runtime — UPDATED (improved comments) but not committed |
| `queue-manager/main.py` | FastAPI — submit_job() at line 200, serverless at line 172 |
| `queue-manager/config.py` | Pydantic settings — serverless endpoints, inference_mode |
| `nginx/docker-entrypoint.sh` | Dynamic DNS resolver — committed (93bf1a1) |

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` on both repos
- [ ] Can you SSH to Verda? `ssh root@65.108.33.101`
- [ ] Read `.claude/agent_docs/progress-mello-team-one-dev.md` top section
- [ ] Check container health: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | sort'`
- [ ] Discuss priorities with user
