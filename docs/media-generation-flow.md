**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-12
**Doc Updated:** 2026-02-12

---

# Media Generation Flow — End-to-End

Every step from pressing "Queue Prompt" in the ComfyUI interface to seeing the generated image in the browser. Traces through all code files, containers, directories, and services.

**Mode documented:** Serverless inference (INFERENCE_MODE=serverless, DataCrunch H200)
**Instance:** quiet-city (65.108.33.101)
**Serverless:** comfyume-vca-ftv-h200-spot

---

## Architecture Diagram

```
User Browser (HTTPS)
    │
    ▼
[comfy-nginx :443] ── SSL termination, /userXXX/ routing
    │
    ├──► /user001/ ──► [comfy-user001 :8188] ── ComfyUI frontend
    │                       │
    │                       ├── serverless_proxy extension
    │                       │   (monkey-patches PromptExecutor)
    │                       │
    │                       └── queue_redirect extension
    │                           (intercepts queuePrompt JS)
    │
    └──► /api/ ──► [comfy-queue-manager :3000] ── FastAPI
                        │
                        ├── POST /prompt to DataCrunch H200
                        ├── Poll /api/history/{prompt_id}
                        ├── Copy images from SFS to /outputs/
                        │
                        └── [comfy-redis :6379] ── job state

[DataCrunch H200 Serverless]
    │
    ├── ComfyUI inference (GPU)
    ├── Saves images to /mnt/sfs/outputs/
    │
    └── [SFS /mnt/sfs] ── shared NFS (models + outputs)
```

---

## Decision Point: Two Execution Paths

ComfyuME has two paths for serverless inference depending on how the request enters.

| Path | Entry | Used When | Key Extension |
|---|---|---|---|
| **Path A: serverless_proxy** | Native ComfyUI "Queue Prompt" button | `INFERENCE_MODE=serverless` AND redirect.js defers | `serverless_proxy/__init__.py` |
| **Path B: queue_redirect** | Intercepted by redirect.js | `INFERENCE_MODE` is NOT serverless, OR redirect.js health check fails | `queue_redirect/web/redirect.js` |

**Current production behavior (serverless mode):**
1. redirect.js checks `/api/health` → detects `inference_mode: serverless`
2. redirect.js defers to native ComfyUI queue (does NOT intercept)
3. ComfyUI's native queue calls `PromptExecutor.execute()`
4. serverless_proxy has monkey-patched `execute()` → proxies to QM
5. QM submits to DataCrunch, polls history, fetches images
6. Proxy sends WebSocket events back to browser

**Both paths converge at step 12** (QM submits to serverless).

---

## Complete Flow Table — Path A (Serverless Proxy, Current Production)

| Step | Action | Code File(s) | Lines | Directory | Container | Service/Port |
|---|---|---|---|---|---|---|
| **1** | **User clicks "Queue Prompt" button** | ComfyUI core `app.js` | — | Browser JS | — | Browser |
| 1.1 | Button click event fires in ComfyUI frontend | `comfyui/web/scripts/app.js` (upstream) | ~1200 | `/comfyui/web/` | comfy-user001 | :8188 |
| 1.2 | `app.queuePrompt()` called | `comfyui/web/scripts/app.js` | ~1210 | `/comfyui/web/` | comfy-user001 | :8188 |
| **2** | **redirect.js health check (defer decision)** | `queue_redirect/web/redirect.js` | 55-67 | `/comfyui/custom_nodes/queue_redirect/web/` | comfy-user001 | :8188 |
| 2.1 | redirect.js `setup()` ran at page load | `redirect.js` | 40-50 | `/comfyui/custom_nodes/queue_redirect/web/` | comfy-user001 | :8188 |
| 2.2 | Fetched `/api/health` from QM via nginx | `redirect.js` | 55 | — | comfy-nginx → comfy-queue-manager | :443 → :3000 |
| 2.3 | QM returns `{"inference_mode": "serverless"}` | `queue-manager/main.py` | `/api/health` route | `/workspace/` | comfy-queue-manager | :3000 |
| 2.4 | redirect.js detects serverless mode | `redirect.js` | 60-65 | Browser JS | — | — |
| 2.5 | redirect.js sets `this.serverlessMode = true` | `redirect.js` | 64 | Browser JS | — | — |
| 2.6 | redirect.js does NOT override `app.queuePrompt()` | `redirect.js` | 67 | Browser JS | — | — |
| **3** | **ComfyUI native queue prompt executes** | ComfyUI core | — | `/comfyui/` | comfy-user001 | :8188 |
| 3.1 | `graphToPrompt()` converts canvas nodes to API format | `app.js` | ~1215 | `/comfyui/web/` | comfy-user001 | :8188 |
| 3.2 | POST to local `/api/prompt` (ComfyUI's native endpoint) | `app.js` | ~1220 | — | comfy-user001 | :8188 |
| 3.3 | ComfyUI server receives prompt | `comfyui/server.py` (upstream) | — | `/comfyui/` | comfy-user001 | :8188 |
| 3.4 | Prompt validated, assigned `prompt_id` | `comfyui/server.py` | — | `/comfyui/` | comfy-user001 | :8188 |
| 3.5 | Prompt added to internal execution queue | `comfyui/server.py` | — | `/comfyui/` | comfy-user001 | :8188 |
| **4** | **Queue Prompt button changes state** | ComfyUI core | — | Browser JS | — | Browser |
| 4.1 | Button text changes to "Cancel" / shows queue count | ComfyUI core `app.js` | — | Browser JS | — | — |
| 4.2 | Queue counter increments in bottom status bar | ComfyUI core `ui.js` | — | Browser JS | — | — |
| **5** | **Job appears in ComfyUI native Job Queue panel** | ComfyUI core | — | Browser JS | — | Browser |
| 5.1 | WebSocket event: `execution_start` sent to browser | `comfyui/server.py` → WS | — | `/comfyui/` | comfy-user001 | :8188 WS |
| 5.2 | Queue panel shows job with prompt_id | ComfyUI core `queue.js` | — | Browser JS | — | — |
| 5.3 | Job status: "Running" in queue panel | ComfyUI core | — | Browser JS | — | — |
| **6** | **PromptExecutor.execute() called (PATCHED)** | `serverless_proxy/__init__.py` | 42-172 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 6.1 | Original `PromptExecutor.execute()` was replaced at import time | `serverless_proxy/__init__.py` | 180-184 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 6.2 | `_apply_execution_patch()` stores original, installs proxy | `serverless_proxy/__init__.py` | 28-40 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 6.3 | `proxy_execute()` begins — receives prompt_id, prompt, extra_data | `serverless_proxy/__init__.py` | 42-50 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| **7** | **Active node highlighting begins (heartbeat)** | `serverless_proxy/__init__.py` | 71-82 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 7.1 | Proxy sends `execution_start` WebSocket | `serverless_proxy/__init__.py` | 56 | `/comfyui/` | comfy-user001 | :8188 WS |
| 7.2 | Heartbeat thread starts: sends `executing` WS every 5s | `serverless_proxy/__init__.py` | 71-82 | `/comfyui/` | comfy-user001 | :8188 WS |
| 7.3 | Each heartbeat cycles through node IDs | `serverless_proxy/__init__.py` | 77 | — | comfy-user001 | :8188 WS |
| 7.4 | Browser receives `executing` → highlights active node on canvas | ComfyUI core `app.js` | — | Browser JS | — | — |
| 7.5 | Green border appears around "active" node in workflow canvas | ComfyUI core CSS | — | Browser JS | — | — |
| **8** | **Proxy builds and sends request to Queue Manager** | `serverless_proxy/__init__.py` | 87-107 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 8.1 | Build JSON payload: `{user_id, workflow, priority, metadata}` | `serverless_proxy/__init__.py` | 87-95 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 8.2 | `user_id` read from `USER_ID` env var (e.g., "user001") | `serverless_proxy/__init__.py` | 22 | — | comfy-user001 | — |
| 8.3 | `QUEUE_MANAGER_URL` = `http://queue-manager:3000` | `serverless_proxy/__init__.py` | 21 | — | comfy-user001 | — |
| 8.4 | `urllib.request.urlopen()` POST to `http://queue-manager:3000/api/jobs` | `serverless_proxy/__init__.py` | 100-107 | — | comfy-user001 → comfy-queue-manager | :3000 |
| 8.5 | Timeout: 600s (cold start + model load + inference) | `serverless_proxy/__init__.py` | 107 | — | — | — |
| **9** | **Queue Manager receives job** | `queue-manager/main.py` | 370-398 | `/workspace/` | comfy-queue-manager | :3000 |
| 9.1 | FastAPI route `POST /api/jobs` receives `JobSubmitRequest` | `queue-manager/main.py` | 370 | `/workspace/` | comfy-queue-manager | :3000 |
| 9.2 | Validate user_id, workflow size, priority | `queue-manager/main.py` | 374-378 | `/workspace/` | comfy-queue-manager | :3000 |
| 9.3 | Create Job object with UUID, store in Redis | `queue-manager/main.py` | 380 | — | comfy-queue-manager → comfy-redis | :3000 → :6379 |
| 9.4 | Detect `settings.inference_mode == "serverless"` | `queue-manager/main.py` | 381 | — | comfy-queue-manager | :3000 |
| 9.5 | Call `submit_to_serverless(workflow, user_id)` | `queue-manager/main.py` | 385 | — | comfy-queue-manager | :3000 |
| **10** | **QM submits workflow to DataCrunch serverless** | `queue-manager/main.py` | 310-340 | `/workspace/` | comfy-queue-manager | :3000 |
| 10.1 | Build `/prompt` payload from workflow JSON | `queue-manager/main.py` | 315-320 | — | comfy-queue-manager | :3000 |
| 10.2 | `serverless_client.post("/prompt")` to DataCrunch H200 | `queue-manager/main.py` | 324 | — | comfy-queue-manager → DataCrunch | :3000 → HTTPS |
| 10.3 | Auth header: `Authorization: Bearer {SERVERLESS_API_KEY}` | `queue-manager/main.py` | 68 (lifespan) | — | comfy-queue-manager | — |
| 10.4 | Endpoint: `https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/prompt` | `queue-manager/config.py` | 51-60 | — | — | HTTPS |
| 10.5 | DataCrunch returns `{prompt_id, number, node_errors}` immediately | — | — | — | DataCrunch H200 | :8188 |
| 10.6 | QM logs: "Serverless prompt accepted: {prompt_id}" | `queue-manager/main.py` | 332 | — | comfy-queue-manager | :3000 |
| **11** | **Model loaded into GPU VRAM on H200** | ComfyUI core (on serverless) | — | `/workspace/ComfyUI/` | DataCrunch H200 | :8188 |
| 11.1 | ComfyUI execution engine begins node-by-node processing | ComfyUI core | — | `/workspace/ComfyUI/` | DataCrunch H200 | :8188 |
| 11.2 | UNETLoader node: loads checkpoint from `/mnt/sfs/models/shared/diffusion_models/` | ComfyUI core | — | `/mnt/sfs/models/shared/diffusion_models/` | DataCrunch H200 | :8188 |
| 11.3 | DualCLIPLoader node: loads text encoders from `/mnt/sfs/models/shared/text_encoders/` | ComfyUI core | — | `/mnt/sfs/models/shared/text_encoders/` | DataCrunch H200 | :8188 |
| 11.4 | VAELoader node: loads VAE from `/mnt/sfs/models/shared/vae/` | ComfyUI core | — | `/mnt/sfs/models/shared/vae/` | DataCrunch H200 | :8188 |
| 11.5 | Model loading takes 2-5 minutes on cold start (H200 141GB VRAM) | — | — | — | DataCrunch H200 | — |
| **12** | **QM polls serverless history** | `queue-manager/main.py` | 200-260 | `/workspace/` | comfy-queue-manager | :3000 |
| 12.1 | `poll_serverless_history(prompt_id)` starts | `queue-manager/main.py` | 200 | — | comfy-queue-manager | :3000 |
| 12.2 | GET `/api/history/{prompt_id}` to DataCrunch | `queue-manager/main.py` | 215 | — | comfy-queue-manager → DataCrunch | HTTPS |
| 12.3 | Poll every 2 seconds, max 600s total (max_wait) | `queue-manager/main.py` | 210, 250 | — | comfy-queue-manager | :3000 |
| 12.4 | Per-request timeout: 10s (fail fast during model load) | `queue-manager/main.py` | 215 | — | comfy-queue-manager | :3000 |
| 12.5 | Logs response structure on first few polls + periodic intervals | `queue-manager/main.py` | 220-230 | — | comfy-queue-manager | :3000 |
| 12.6 | Eventually: history returns `status.completed == True` with outputs | `queue-manager/main.py` | 235-240 | — | comfy-queue-manager | :3000 |
| **13** | **GPU inference executes on serverless** | ComfyUI core (on serverless) | — | `/workspace/ComfyUI/` | DataCrunch H200 | :8188 |
| 13.1 | KSampler node: denoising/diffusion steps (GPU compute) | ComfyUI core | — | — | DataCrunch H200 | :8188 |
| 13.2 | VAEDecode node: latent → pixel space conversion | ComfyUI core | — | — | DataCrunch H200 | :8188 |
| 13.3 | SaveImage node: saves PNG to `--output-directory` | ComfyUI core | — | `/mnt/sfs/outputs/` | DataCrunch H200 | :8188 |
| **14** | **Image saved to SFS by serverless container** | ComfyUI core SaveImage | — | `/mnt/sfs/outputs/` | DataCrunch H200 | — |
| 14.1 | ComfyUI `SaveImage` node writes to `--output-directory` | ComfyUI core | — | `/mnt/sfs/outputs/` | DataCrunch H200 | — |
| 14.2 | File: e.g., `/mnt/sfs/outputs/Flux2-Klein_00001_.png` (2MB) | — | — | `/mnt/sfs/outputs/` | DataCrunch H200 | — |
| 14.3 | File owned by uid 1000 (ComfyUI user inside container) | — | — | `/mnt/sfs/outputs/` | DataCrunch H200 | — |
| 14.4 | SFS permissions `1777` allow write from any uid | — | — | `/mnt/sfs/outputs/` | — | NFS |
| **15** | **QM fetches images from SFS** | `queue-manager/main.py` | 274-298 | `/workspace/` | comfy-queue-manager | :3000 |
| 15.1 | `fetch_serverless_images()` called after poll completes | `queue-manager/main.py` | 274 | — | comfy-queue-manager | :3000 |
| 15.2 | Extract output filenames from history response | `queue-manager/main.py` | 278-282 | — | comfy-queue-manager | :3000 |
| 15.3 | Try SFS path first: `/mnt/sfs/outputs/{subfolder}/{filename}` | `queue-manager/main.py` | 285-290 | `/mnt/sfs/outputs/` | comfy-queue-manager | NFS (ro) |
| 15.4 | File found on SFS → copy to `/outputs/{user_id}/{filename}` | `queue-manager/main.py` | 290-293 | `/mnt/sfs/outputs/` → `/outputs/user001/` | comfy-queue-manager | :3000 |
| 15.5 | Log: "SFS image: {path} → {dest} ({size} bytes)" | `queue-manager/main.py` | 280 | — | comfy-queue-manager | :3000 |
| 15.6 | Fallback: HTTP GET `/view?filename=...` from serverless (if SFS fails) | `queue-manager/main.py` | 294-298 | — | comfy-queue-manager → DataCrunch | HTTPS |
| **16** | **Image arrives in user output directory** | — | — | `/outputs/user001/` | comfy-queue-manager | — |
| 16.1 | File: `/outputs/user001/Flux2-Klein_00001_.png` | — | — | `/outputs/user001/` | comfy-queue-manager | — |
| 16.2 | This directory is volume-mounted into comfy-user001 as `/comfyui/output/` | `docker-compose.users.yml` | — | `/outputs/` ↔ `/comfyui/output/` | comfy-user001 | — |
| 16.3 | Symlink: `/comfyui/output → /outputs` (created by docker-entrypoint.sh) | `docker-entrypoint.sh` | 104-105 | `/comfyui/output/` | comfy-user001 | — |
| **17** | **QM returns result to serverless_proxy** | `queue-manager/main.py` | 394-410 | `/workspace/` | comfy-queue-manager | :3000 |
| 17.1 | QM builds response: `{id, status: completed, result: {outputs: {...}}}` | `queue-manager/main.py` | 394-398 | — | comfy-queue-manager | :3000 |
| 17.2 | Result includes output filenames and subfolder info | `queue-manager/main.py` | 395 | — | comfy-queue-manager | :3000 |
| 17.3 | HTTP response sent back to serverless_proxy (which is waiting) | — | — | — | comfy-queue-manager → comfy-user001 | :3000 → :8188 |
| **18** | **Proxy sends WebSocket events to browser** | `serverless_proxy/__init__.py` | 116-145 | `/comfyui/custom_nodes/serverless_proxy/` | comfy-user001 | :8188 |
| 18.1 | Extract outputs from QM response | `serverless_proxy/__init__.py` | 116-120 | — | comfy-user001 | :8188 |
| 18.2 | For each output node: send `executed` WebSocket message | `serverless_proxy/__init__.py` | 122-129 | — | comfy-user001 | :8188 WS |
| 18.3 | WS message: `{node: node_id, output: {images: [{filename, ...}]}, prompt_id}` | `serverless_proxy/__init__.py` | 124-128 | — | comfy-user001 | :8188 WS |
| 18.4 | Stop heartbeat thread | `serverless_proxy/__init__.py` | 131 | — | comfy-user001 | :8188 |
| 18.5 | Send `executing` with `node: None` (signals completion) | `serverless_proxy/__init__.py` | 133 | — | comfy-user001 | :8188 WS |
| 18.6 | Set `self.history_result = {"outputs": outputs, "meta": {}}` | `serverless_proxy/__init__.py` | 138-139 | — | comfy-user001 | :8188 |
| 18.7 | Set `self.success = True` | `serverless_proxy/__init__.py` | 140 | — | comfy-user001 | :8188 |
| **19** | **Image appears in ComfyUI SaveImage node (main canvas)** | ComfyUI core | — | Browser JS | — | Browser |
| 19.1 | Browser receives `executed` WebSocket message | ComfyUI core `app.js` | — | Browser JS | — | — |
| 19.2 | SaveImage node widget parses output: `{images: [{filename, subfolder, type}]}` | ComfyUI core `widgets.js` | — | Browser JS | — | — |
| 19.3 | Browser requests image: `GET /user001/api/view?filename=Flux2-Klein_00001_.png` | — | — | — | Browser → comfy-nginx | :443 |
| 19.4 | nginx strips `/user001` prefix, proxies to `comfy-user001:8188/api/view?filename=...` | `nginx/nginx.conf` | ~120 | — | comfy-nginx → comfy-user001 | :443 → :8188 |
| 19.5 | ComfyUI `/api/view` serves from `/comfyui/output/` (symlinked to `/outputs/`) | ComfyUI core `server.py` | — | `/comfyui/output/` (→ `/outputs/`) | comfy-user001 | :8188 |
| 19.6 | Image renders in the SaveImage node preview on canvas | ComfyUI core | — | Browser JS | — | — |
| **20** | **Image appears in Media Assets sidebar** | ComfyUI core | — | Browser JS | — | Browser |
| 20.1 | ComfyUI updates internal history with the completed prompt | ComfyUI core `history.js` | — | Browser JS | — | — |
| 20.2 | ComfyUI history stores output references (filename, subfolder, type) | ComfyUI core | — | Browser JS | — | — |
| 20.3 | Media Assets sidebar refreshes — scans history for image outputs | ComfyUI core `sidebar.js` | — | Browser JS | — | — |
| 20.4 | New image thumbnail appears in "Assets" or "Output Images" panel | ComfyUI core | — | Browser JS | — | — |
| 20.5 | Clicking thumbnail opens full-size via `/api/view?filename=...` | — | — | — | Browser → comfy-nginx → comfy-user001 | :443 → :8188 |
| **21** | **Job Queue panel updates** | ComfyUI core | — | Browser JS | — | Browser |
| 21.1 | `executing` with `node: None` signals job complete | ComfyUI core | — | Browser JS | — | — |
| 21.2 | Queue panel moves job to "History" tab | ComfyUI core `queue.js` | — | Browser JS | — | — |
| 21.3 | History entry shows thumbnail preview of output | ComfyUI core | — | Browser JS | — | — |
| 21.4 | "Queue Prompt" button returns to ready state | ComfyUI core `app.js` | — | Browser JS | — | — |

---

## Timing Summary (Typical Serverless Run)

| Phase | Time | What's Happening |
|---|---|---|
| T+0.0s – T+0.5s | Steps 1-9 | Button click → QM receives job |
| T+0.5s – T+1.0s | Step 10 | QM POSTs to DataCrunch, gets prompt_id |
| T+1.0s – T+120s | Steps 11-12 | Model loading (cold start) + QM polling |
| T+120s – T+135s | Step 13 | GPU inference (denoising steps) |
| T+135s – T+136s | Step 14 | Image saved to SFS |
| T+136s – T+137s | Steps 15-16 | QM copies from SFS to user dir |
| T+137s – T+138s | Steps 17-18 | QM responds, proxy sends WebSocket |
| T+138s – T+139s | Steps 19-21 | Browser renders image, updates UI |

**Cold start:** ~120s (model loading). **Warm inference:** ~15s.

---

## Key Files Reference

| File | Role in Flow | Steps |
|---|---|---|
| `comfyume-extensions/queue_redirect/web/redirect.js` | Health check, serverless mode detection, defer decision | 2 |
| `comfyume-extensions/serverless_proxy/__init__.py` | Patches PromptExecutor, proxies to QM, sends WS events | 6-8, 18 |
| `comfyume-extensions/extensions.conf` | Declares which extensions are active | Boot |
| `queue-manager/main.py` | Job routing, serverless submission, history polling, image fetching | 9-10, 12, 15, 17 |
| `queue-manager/config.py` | Endpoint URLs, API keys, inference mode | 10 |
| `queue-manager/redis_client.py` | Job state persistence | 9 |
| `comfyui-frontend/docker-entrypoint.sh` | Extension deploy, output symlink, INFERENCE_MODE export | Boot |
| `comfyui-frontend/Dockerfile` | Build context, install deps, backup custom_nodes | Build |
| `nginx/nginx.conf` | SSL, routing, proxy_pass, timeouts | 2, 19 |
| `docker-compose.yml` | Service definitions, volume mounts, env vars | All |
| `docker-compose.users.yml` | 20 user container definitions (auto-generated) | All |
| `scripts/generate-user-compose.sh` | Generates docker-compose.users.yml | Build |

---

## Volume Mount Map

| Container | Host Path | Container Path | Access | Purpose |
|---|---|---|---|---|
| comfy-user001 | `./data/outputs/` | `/outputs/` | rw | User output images |
| comfy-user001 | (symlink) | `/comfyui/output/ → /outputs/` | rw | ComfyUI native serve path |
| comfy-user001 | `/mnt/sfs/models/shared/` | `/models/shared/` | ro | Model listing |
| comfy-user001 | `./data/user_data/user001/` | `/comfyui/user/` | rw | User preferences |
| comfy-user001 | `./data/user_data/user001/comfyui/custom_nodes/` | `/comfyui/custom_nodes/` | rw | Extensions |
| comfy-queue-manager | `./data/outputs/` | `/outputs/` | rw | Writes fetched images |
| comfy-queue-manager | `/mnt/sfs/outputs/` | `/mnt/sfs/outputs/` | ro | Reads SFS images |
| DataCrunch H200 | SFS | `/mnt/sfs/` | rw | Models (read) + outputs (write) |

---

## Error Handling Summary

| Error | Where Caught | Response | User Sees |
|---|---|---|---|
| Serverless timeout (600s) | `queue-manager/main.py` L364 | HTTP 504 | Error banner or console error |
| Serverless HTTP error | `queue-manager/main.py` L367 | HTTP 502 | Error banner |
| SFS image not found | `queue-manager/main.py` L294 | Falls back to HTTP download | Delayed but works |
| HTTP image download fails | `queue-manager/main.py` L298 | Error logged, empty outputs | No image in UI |
| Proxy exception | `serverless_proxy/__init__.py` L149-172 | `execution_error` WS | Red error in queue panel |
| Missing history_result | `serverless_proxy/__init__.py` L138 | Fixed (PR #25) — always set | N/A (was crash) |
