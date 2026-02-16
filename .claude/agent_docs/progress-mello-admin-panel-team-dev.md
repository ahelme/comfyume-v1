**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume
**Domain:** comfy.ahelme.net (staging) / aiworkshop.art (production)
**Doc Created:** 2026-02-06
**Doc Updated:** 2026-02-16

---
# Project Progress Tracker
**Target:** Workshop Feb 25 2026
### Implementation Phase
**MAIN Repo:** comfyume (https://github.com/ahelme/comfyume)
**Branch:** mello-admin-panel-team-*
**Phase:** Admin Dashboard V2
---
## 0. Update Instructions

   RE: PRIORITY TASKS
   **UPDATE:**
     - WHEN NEW TASKS EMERGE
     - AT END OF SESSION - YOU MUST UPDATE/CULL TASKS - carefully!!!

   **ALWAYS reference issues in our TWO  Github Issue Trackers**
      - MAIN COMFYUME REPO:   github.com/ahelme/comfyume/issues/
      - PRIVATE SCRIPTS REPO: github.com/ahelme/comfymulti-scripts/issues/

   **FORMAT:**
          [icon] [PRIORITY] [GH#s] [SHORT DESC.]
             - [DATE-CREATED] [DATE-UPDATED]
               - CONCISE NOTES INC. RELATED [GH#] (IF ANY)
   **BE CONCISE**
     - DETAIL BELONGS IN GH ISSUE! and in PROGRESS REPORT BELOW !!!

   RE: Progress Reports (NEWEST AT TOP!)
     **CRITICAL DETAIL - NO FLUFF**
     **UPDATE OFTEN e.g. after RESEARCH, COMMITS, DECISIONS**
      - concise notes, refer to GH issues
      - new blockers / tasks / completed tasks
      - investigations needed
      - research found
      - solutions formulated
      - decisions made
---
## 1. PRIORITY TASKS

✅ **(COMPLETE) - comfyume #65 - Admin Dashboard Phase 1: Core Dashboard MVP**
    - Created: 2026-02-06 | Updated: 2026-02-06
    - System status cards (Redis, Queue Manager, Serverless GPU, Disk Usage)
    - Container list with restart/stop/start actions + log viewer
    - Dark ComfyUI-themed UI with 4-tab navigation

✅ **(COMPLETE) - comfyume #66 - Admin Dashboard Phase 2: GPU Deployment Switching**
    - Created: 2026-02-06 | Updated: 2026-02-06
    - One-click switching between H200/B300 spot/on-demand
    - Reads/writes .env via mounted volume, restarts queue-manager via Docker SDK
    - Confirmation dialog before switching

✅ **(COMPLETE) - comfyume #67 - Admin Dashboard Phase 3: Storage & R2 Management**
    - Created: 2026-02-06 | Updated: 2026-02-06
    - Disk usage breakdown with per-directory sizes
    - R2 bucket overview (objects count + sizes via boto3)
    - Directory browser with breadcrumb navigation (restricted to /outputs, /inputs, /models, /workflows)

✅ **(COMPLETE - ALL MODELS ON DISK) - comfyume #88 - Templates & Models Management (Phase 4)**
    - Created: 2026-02-08 | Updated: 2026-02-08
    - Templates tab: scan workflow JSONs, extract model deps, show on-disk status
    - Check Models view: gated detection, download engine (testing team #93), orphan detection + delete
    - All 22 models downloaded (172GB), disk cleaned to 68% (removed 3 legacy files ~34GB)
    - Deployed to Verda, all 20 frontends verified with /mnt/sfs/models mount

✅ **(COMPLETE) - comfyume-v1 #43 - NFS Model Visibility Fix**
    - Created: 2026-02-16 | Updated: 2026-02-16
    - LTX-2 "Missing Models" popup — Docker bind mount cached stale NFS dir listing
    - Fixed by batched restart of all 20 frontend containers (no code changes)
    - All models visible inside containers after restart

🚨 **CRITICAL - comfyume-v1 #101, #103 - Serverless Inference BROKEN**
    - Created: 2026-02-09 | Updated: 2026-02-16
    - Yaml key on SFS confirmed CORRECT as of Feb 16 (latent_upscale_models)
    - Flux Klein WAS working (113s execution confirmed Feb 10)
    - **NOW BROKEN** (reported Feb 16) — even Flux Klein no longer works
    - Likely caused by container restart (Feb 16 #43 fix) or other recent server changes
    - NEXT: investigate carefully what changed — compare container state before/after

🔲 **NEW - comfyume-v1 #44 - GPU Progress Banner for Serverless Mode**
    - Created: 2026-02-16
    - redirect.js exits early in serverless mode (line 64-67), banner never created
    - serverless_proxy sends WebSocket events but no browser-side listener
    - Fix: listen to WebSocket events in redirect.js, show progress banner

🔲 **NEW - comfyume-v1 #45 - Cookie-Based Auth Persistence**
    - Created: 2026-02-16
    - HTTP Basic Auth re-prompts too often, especially on mobile
    - Fix: nginx map + Set-Cookie — cookie bypasses auth for 24h

🔲 **NEW - comfyume-v1 #46 - Cold Start Silent Failure UX**
    - Created: 2026-02-16
    - No feedback during 5+ minute serverless cold start, silently fails
    - Full timeout chain: urllib 600s → QM polling 10s/poll 600s max → cold start 30-300s
    - Coupled with #44 (same file) but separate concern

✅ **(COMPLETE) - comfyume #106 - Monitoring & Management Stack**
    - Created: 2026-02-09 | Updated: 2026-02-09
    - Installed on Verda: Prometheus v3.9.1 (:9090), Grafana v12.3.2 (:3001), Loki v3.6.5 (:3100), cAdvisor (:8081), Promtail, Dry v0.11.2, Verda SDK v1.20.0, OpenTofu v1.11.4
    - 12 custom skills created + user guide (docs/verda-skills-guide.md)
    - 2 Grafana dashboards imported: Docker Container (15331), Container Resources (14678)

✅ **(COMPLETE) - comfyume #109 - SSL Certs for New Subdomains**
    - Created: 2026-02-09 | Updated: 2026-02-09
    - Let's Encrypt cert for 5 subdomains: portainer, grafana, prometheus, docs, upload
    - All reverse-proxied through Mello nginx → Verda via Tailscale
    - Grafana password changed from default to match .env ADMIN_PASSWORD

---

# Progress Reports

---
## Progress Report 11 - 2026-02-16 - NFS Fix, 3 New Issues, Inference Regression (#43, #44, #45, #46)

**Date:** 2026-02-16 | **Issues:** #43, #44, #45, #46

**Done:**
- Diagnosed #43: LTX-2 "Missing Models" popup — `/models/shared/` empty inside all 20 containers despite host seeing all files. Docker bind mount cached stale NFS directory listing.
- Fixed #43: batched restart of all 20 frontend containers (user020 test, then 4 batches of 5). All models visible. No code changes needed.
- Investigated GPU progress banner: `redirect.js` line 64-67 exits early in serverless mode, banner never created. `serverless_proxy` sends WebSocket events but nothing listens browser-side.
- Investigated auth persistence: HTTP Basic Auth has no cookie/session support, re-prompts frequently on mobile.
- Investigated cold start UX: full timeout chain traced (urllib 600s → QM 600s → cold start 30-300s), no user feedback.
- Created GH issues #44 (GPU banner), #45 (cookie auth), #46 (cold start UX).
- SSH access updated: Tailscale IP `100.89.38.43` as `dev` user (root on public IP no longer works after reprovision).
- SFS confirmed mounted on instance (was not accessible Feb 10).
- `extra_model_paths.yaml` on SFS has correct keys.

**Key findings:**
- ComfyUI v0.11.0 (not v0.10.0)
- Flux Klein `UNETLoader` doesn't declare `properties.models` → no "Missing Models" popup
- LTX-2 nodes DO declare `properties.models` → popup triggered when models not visible

**REGRESSION (reported end of session):**
- Inference now broken for ALL workflows including Flux Klein (was working before container restarts)
- Needs careful investigation — may be related to #43 container restart or other recent changes

**Handover interrupted — context ran out before completing file updates.**

---
## Progress Report 10 - 2026-02-09 - Monitoring Fixes, SSL Certs, Verda SDK (#106, #109)

**Date:** 2026-02-09 | **Issues:** #106, #109

**Done:**
- Fixed Promtail: added `promtail` user to `docker` group — was unable to read Docker socket, zero log ingestion. Now shipping logs from all 26 containers to Loki
- Fixed Loki queries: labels are `container_name`/`service_name`/`stream` (no `job` label). Updated 4 skill files
- Fixed Verda SDK: correct method is `get_deployments()` not `get()`, env vars need `source /root/.bashrc`. Added to `/etc/environment` for reliability
- Discovered h200-spot deployment has diagnostic startup command (not ComfyUI) from last session's debugging
- Created `docs/verda-skills-guide.md` — 153-line user-friendly guide to all 12 skills
- SSL certs (#109): Let's Encrypt cert for portainer, grafana, prometheus, docs, upload (.aiworkshop.art)
  - All 5 subdomains DNS → Mello public IP (157.180.76.189)
  - Mello nginx reverse proxies grafana/prometheus to Verda via Tailscale
  - Grafana admin password changed to match .env
  - Prometheus protected with basic auth (same .env credentials)
  - Removed stale comfy.ahelme.net.bak from Mello nginx sites-enabled
  - Backed up Mello nginx configs before changes

**Key finding — Verda serverless deployments:**
- h200-spot: DIAGNOSTIC cmd (cat yaml + ls) — needs restoring to ComfyUI startup
- h200-on-demand, b300-spot, b300-on-demand: correct ComfyUI startup cmd

---
## Progress Report 9 - 2026-02-09 - Monitoring Stack Installed (#106)

**Date:** 2026-02-09 | **Issue:** #106

**Done:**
- Installed full monitoring stack on Verda via SSH:
  - Prometheus v3.9.1 (systemd, 7-day retention, scrapes self + cAdvisor)
  - Grafana v12.3.2 (port 3001, Prometheus + Loki data sources configured)
  - Loki v3.6.5 (systemd, 7-day retention)
  - Promtail v3.6.5 (systemd, scraping Docker container logs)
  - cAdvisor (Docker container, port 8081 — 8080 taken by comfy-admin)
  - Dry v0.11.2 (Docker TUI)
  - Verda SDK v1.20.0 (pip install verda, env vars in /root/.bashrc)
  - OpenTofu v1.11.4 (snap, /root/tofu/ dir created)
- Imported 2 Grafana dashboards: Docker Container Dashboard (15331), Container Resources (14678)
- Created 12 custom skills for Verda management in `.claude/commands/`
- Updated CLAUDE.md with monitoring section
- Cleaned PR #104: removed non-working favicon, kept valid JS/nginx/QM fixes

---
## Progress Report 8 - 2026-02-09 - Serverless Inference Debugging (#101, #103)

**Date:** 2026-02-09 | **Issues:** #101, #102, #103

**Done:**
- Fixed redirect.js: `import { app }`, endpoint `/api/jobs`, field `user_id`, priority `1`, `graphToPrompt()`
- Fixed loader.js: same import fix
- Fixed nginx.conf: `auth_basic off` on `/api/` and `/favicon.ico`, removed trailing slash, 600s proxy timeouts
- Added debug logging to queue-manager `submit_to_serverless()` — captures response body on error
- Added favicon.ico to nginx container
- Merged PR #100 (testing-scripts-team fixes for redirect.js and nginx)
- Deployed all fixes to Verda: SCP'd nginx.conf, copied redirect.js/loader.js to all 20 user dirs
- Investigated old GPU instance OS drive — confirmed serverless was added in commits d53b548, 55337d8 (#62)
- Discovered two-SFS confusion: REAL SFS (Verda NFS) still connected to serverless container, block storage ("fake SFS") renamed to `/mnt/models-block-storage`
- Created issues #101 (yaml key mapping), #102 (General Storage), #103 (architecture decision)
- Updated SSH config: Verda IP 95.216.229.236, User root
- Verda gateway only routes `/prompt` — cannot query `/system_stats`, `/internal/folder_paths` etc. remotely

**Root cause identified:**
- Container logs show `Adding extra search path upscale_models /mnt/sfs/models/shared/latent_upscale_models`
- yaml key maps to `upscale_models` folder type, but `LatentUpscaleModelLoader` needs `latent_upscale_models`
- Likely the yaml on the REAL SFS has key `upscale_models` (from SERVERLESS_UPDATE.md template)

**Pending:**
- Run diagnostic startup command to see REAL SFS yaml content (#103 Option 1)
- Fix yaml key on REAL SFS via one-time startup command
- Test inference end-to-end

---
## Progress Report 7 - 2026-02-08 - Download Engine Live, Orphan Detection, Inference Fix (#88, #93)

**Date:** 2026-02-08 | **Issues:** #88, #93

**Done:**
- Deployed testing team's model download engine (#93) to Verda
  - Rebuilt admin container with `sse-starlette`, added `NTFY_TOPIC` to .env
  - Rebuilt nginx container with `proxy_buffering off` for SSE streaming
  - Fixed SSL certs: copied from `/mnt/scratch/backup-from-old-os/letsencrypt/` to `/etc/letsencrypt/`
- Fixed `HF_TOKEN` ReferenceError bug in download engine frontend (JS referenced server-side var)
- Patched `flux2_klein_9b_text_to_image.json` workflow: added HF download URLs to UNETLoader nodes (had empty `properties.models`)
- Downloaded last missing model `flux-2-klein-9b-fp8.safetensors` (distilled 9B) via admin panel download engine
- **All 22 models now on disk** - 5/5 workflows at 100% coverage
- Disk cleanup: removed 3 legacy files (~34GB): `flux2_klein_9b.safetensors`, `flux2_klein_4b.safetensors`, `gemma_3_12B_it.safetensors` → 85% → 68% usage
- Added orphaned model detection to Check Models page (scans disk, compares to workflow refs, shows with amber badges + sizes)
- Added DELETE endpoint + button for orphaned models with confirmation dialog
- Created PR #94 (admin-panel-team → main)
- Fixed inference pipeline: `queue_redirect` custom node was missing from all 20 user `custom_nodes` dirs (volume mount overwrites). Copied and restarted all containers.

**Commits this session:**
- `e924010` fix: resolve HF_TOKEN ReferenceError in check downloads UI (#93)
- `9f0aa61` feat: add orphaned model detection to check downloads page (#88)
- `4341cc6` fix: always show Check Models button after scan (#88)
- `9132eaf` feat: add delete button for orphaned models (#88)

**Pending:**
- Test serverless inference end-to-end (user002 → queue-manager → GPU)
- Verify queue_redirect routes jobs correctly
- Check if `/api/queue/submit` endpoint exists in queue-manager

---
## Progress Report 6 - 2026-02-08 - Models Connected, All Camera LoRAs Downloaded (#88)

**Date:** 2026-02-08 | **Issue:** #88

**Done:**
- Fixed storage architecture: replaced symlinks with direct .env paths
  - `MODELS_PATH=/mnt/sfs/models`, `OUTPUTS_PATH=/mnt/scratch/outputs`, `INPUTS_PATH=/mnt/scratch/inputs`
  - Updated restore script v0.4.2: Step 15 now verifies paths instead of creating symlinks
  - Updated Step 11 to set storage paths dynamically based on available mounts
  - Fixed embedded Redis IPs in restore script (were still Mello's, now Verda Tailscale)
- Downloaded 3 missing Flux Klein 9B models to Verda /mnt/sfs:
  - `diffusion_models/flux-2-klein-base-9b-fp8.safetensors` (9GB) - HF gated, required license acceptance
  - `text_encoders/qwen_3_8b_fp8mixed.safetensors` (8.1GB)
  - `vae/flux2-vae.safetensors` (321MB)
- Downloaded ALL 7 LTX-2 camera control LoRAs for filmmakers:
  - static (2.1GB), dolly-in/out/left/right (313MB each), jib-up/down (2.1GB each)
- Downloaded remaining models for full workflow coverage:
  - `checkpoints/ltx-2-19b-distilled.safetensors` (41GB) for distilled video workflow
  - `diffusion_models/flux-2-klein-base-4b.safetensors` + `flux-2-klein-4b.safetensors` (7.3GB each)
  - `text_encoders/qwen_3_4b.safetensors` (7.5GB) for 4B workflow
- Recreated all 22 containers with correct /mnt/sfs/models mount
- Templates tab verified: on-disk detection working across all 5 workflows
- Added comprehensive workflow template docs to CLAUDE.md:
  - All 5 workflows documented with subgraph explanations
  - Complete model inventory table (21 files, 172GB) with HF download URLs
  - Camera control LoRA table for filmmakers
- Deployed restore script v0.4.2 to Verda (root + dev) via SCP

**Model inventory: 21 files, 172GB on /mnt/sfs (33GB free, 85% usage)**
- Only missing: `flux-2-klein-9b-fp8.safetensors` (distilled 9B variant, HF gated)
- Potential cleanup: `gemma_3_12B_it.safetensors` (19GB full-precision, have fp4_mixed) and legacy checkpoints

**Private scripts repo:** commit 2a3d444 - restore script v0.4.2 pushed to main

---
## Progress Report 5 - 2026-02-08 - Templates & Models Management Tab (#88)

**Date:** 2026-02-08 | **Issue:** #88

**Done:**
- Implemented Phase 4: Templates & Models Management tab in admin panel
- Backend: 2 new endpoints + 2 helper functions (~182 lines added to app.py)
  - `_extract_models_from_workflow()` - parses workflow JSON, extracts models from `properties.models` + widget value fallbacks for UNETLoader/CheckpointLoaderSimple
  - `_check_model_on_disk()` - checks `/models/{dir}/{file}` existence and size
  - `GET /api/templates/scan` - per-workflow model status + disk info
  - `GET /api/templates/models` - deduplicated cross-workflow model list
- Frontend: 5th "Templates" tab (~253 lines added to dashboard.html)
  - 4 summary cards (Workflows, On Disk, Missing, Disk Free)
  - Per-workflow cards with subgraph names + model rows
  - ON DISK (green) / MISSING (red) badges with file sizes
  - "Copy wget" button generates `wget -c -P /mnt/sfs/models/shared/{dir}/ "{url}"`
  - Disk usage bar
- Tested model extraction against all 5 workflow files - correct results
- No new dependencies, no Docker changes needed
- Deployed to Verda: fetched branch, built admin container, restarted
- Fixed REDIS_BIND_IP and INFERENCE_SERVER_REDIS_HOST: Mello IP (100.99.216.71) → Verda Tailscale IP (100.89.38.43)
  - Updated on Verda live .env + private scripts repo .env (comfymulti-scripts 8259d60)
  - Best practice: bind Redis to Tailscale interface only (serverless containers connect via Tailscale)
- Reloaded nginx to pick up new admin container IP after recreation
- Initial browser testing looks great, need /mnt/sfs models mount to verify on-disk detection

---
## Progress Report 4 - 2026-02-08 - Verda debugging, restore script improvements, CLAUDE.md updates

**Date:** 2026-02-08

**Done:**
- Merged 34 commits from main into `admin-panel-team` (fast-forward after stash)
- Resolved merge conflict in `.claude/CLAUDE-RESUME-ADMIN-PANEL-TEAM.md`
- SSHed into Verda production (95.216.229.236) to debug admin panel auth
  - Root cause: browser URL-encoding `/` as `%2F` in password
  - Auth works fine server-side (curl 200), nginx logs confirmed password mismatch from encoded input
  - Generated corrected magic links for all 20 users (fixed domain + URL encoding)
- Copied fresh `.env` from Mello scripts repo to Verda `~/comfyume/.env`
- Copied SSH authorized_keys from root to dev user on Verda (was missing mac + termius keys)
- **Private scripts repo (comfymulti-scripts):**
  - `restore-verda-instance.sh`: added Termius SSH keys, copy keys root→dev, full .env v0.3.5 sync, added MELLO_PUBLIC_IP (PR #32 merged)
  - Created `claude-settings/all-teams/commands/` with all 12 command files
- CLAUDE.md: moved User Preferences to bottom, added "never push directly to main" rule to git workflow + user prefs

**Notable changes from main:**
- New testing-scripts-team with test suites (connectivity, serverless, integration)
- `/pull-main` and `/update-progress` commands added
- Docs archived and cleaned up
- Resume/handover files slimmed down
- Restore script renamed to `restore-verda-instance.sh` v0.4.0

---
## Progress Report 3 - 2026-02-07 - Close GH issues

**Date:** 2026-02-07

**Done:**
- Commented and closed GitHub issues #65, #66, #67 with implementation details referencing PR #69
- PR #69 already merged to main

---
### Implementation Phase
**Repository:** comfyume (https://github.com/ahelme/comfyume)
**Branch:** admin-panel-team
**Phase:** Admin Dashboard V2

## Progress Report 2 - 2026-02-06 - All 3 Phases Implemented

**Date:** 2026-02-06 | **Issues:** #65, #66, #67

**Done:**
- **Phase 1 (#65):** System status cards (Redis, QM, Serverless GPU, Disk), container management (list/restart/stop/start/logs), Docker socket integration
- **Phase 2 (#66):** GPU deployment switching panel with 4 serverless options (H200/B300 spot/on-demand), .env modification + queue-manager auto-restart, confirmation dialogs
- **Phase 3 (#67):** Disk usage breakdown, R2 bucket querying via boto3, directory browser with path security restrictions
- **Design:** Dark ComfyUI-themed UI with node-connection logo, colored port dots, dot-grid canvas background, 4-tab SPA navigation
- **Security:** All endpoints behind HTTP Basic Auth, container operations restricted to `comfy-` prefix, directory traversal prevention, XSS protection via HTML escaping

**Files created/modified:**
- `admin/app.py` - Complete rewrite: 691 lines, 20 API endpoints
- `admin/dashboard.html` - New: comprehensive dark-themed SPA (~600 lines CSS + JS)
- `admin/requirements.txt` - Added docker, redis, boto3 dependencies
- `admin/Dockerfile` - Added dashboard.html to COPY
- `docker-compose.yml` - Added Docker socket mount, .env mount, storage volume mounts, R2 env vars

**API Endpoints (20 total):**
- System: GET /api/system/status
- Containers: GET /api/containers, POST .../restart, POST .../stop, POST .../start, GET .../logs
- GPU: GET /api/gpu/status, POST /api/gpu/switch
- Storage: GET /api/storage/disk, GET /api/storage/r2, GET /api/storage/browse
- Queue: GET /api/queue/status, GET /api/queue/jobs, DELETE .../jobs/{id}, PATCH .../priority

**Architecture:**
- Optional Docker SDK (degrades gracefully if socket not mounted)
- Optional boto3 for R2 (shows helpful error if not configured)
- Optional Redis direct connection for health checks
- All queue operations proxied through admin backend (works behind nginx)

---

## Progress Report 1 - 2026-02-06 - Admin Panel Team Initialized

**Date:** 2026-02-06 | **Issues:** #65, #66, #67

**Done:**
- Team initialization: progress file, handover command, resume context, onboarding file
- Read and analyzed existing codebase: admin/app.py, queue-manager/*, scripts/switch-gpu.sh
- Read both team progress files (mello top 250 lines, verda top 250 lines)
- Designed ComfyUI-themed dark dashboard UI with 4-tab navigation

---
