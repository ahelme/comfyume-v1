**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume
**Domain:** comfy.ahelme.net (staging) / aiworkshop.art (production)
**Doc Created:** 2026-02-06
**Doc Updated:** 2026-02-22

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

⏳ **(IN PROGRESS) - comfyume-v1 #75 - Admin panel: isolate mode toggle**
    - Created: 2026-02-22 | Updated: 2026-02-22
    - Overlay toggle (localStorage `gpu_overlay_mode` = admin/user) for mello-team-one's GPU overlay
    - Isolate mode toggle: OFF = normal, ON = all /api/* return 503 (fault isolation)
    - Backend: GET/POST `/api/admin/isolate`, middleware gate, `ADMIN_ISOLATE_MODE` env var
    - Frontend: localStorage persistence + backend sync on load
    - Deployed to testing-009 (anegg.app)
    - Serverless timeout table added to README.md
    - Admin panel described as admin/operator (not instructor)
    - Related: #78, #79, #80

🔲 **NEW - comfyume-v1 #78 - Static assets MIME type + manifest 401**
    - Created: 2026-02-22
    - Non-critical: CSS wrong MIME, manifest-*.json gets 401 behind auth
    - Likely nginx fix: mime.types + auth_basic off for /assets/

🔲 **NEW - comfyume-v1 #79 - Favicon progress animation 404**
    - Created: 2026-02-22
    - Non-critical: /assets/images/favicon_progress_16x16/ not found

🔲 **NEW - comfyume-v1 #80 - Userdata API 404 for subgraphs/templates**
    - Created: 2026-02-22
    - Non-critical: expected on fresh install, ComfyUI handles gracefully

⏳ **(IN PROGRESS) - comfyume-v1 #72 - Apply environment-isolated serverless on testing-009**
    - Created: 2026-02-22 | Updated: 2026-02-22
    - Steps 1-7 COMPLETE: tofu apply done, `comfyume-test-vca-ftv-h200-spot` created
    - QM pointing to testing endpoint, CLONE_SFS mounted
    - Credentials restored (correct per-user strong passwords)
    - **REMAINING: Step 8 — mello-team-one now owns inference testing**
    - Related: #71, #54, #69

✅ **(COMPLETE) - comfyume-v1 #71 - SFS volume mismatch — environment-isolated serverless**
    - Created: 2026-02-22 | Updated: 2026-02-22
    - Diagnosed: serverless mounts PROD_SFS, testing mounts CLONE_SFS → images invisible
    - Fix: IaC `environment` variable namespaces deployments per-environment
    - `environment=prod` → unchanged names, `environment=test` → `comfyume-test-*`
    - .gitignore fixed across all 7 repos (tfstate, terraform.tfvars)
    - Production safety docs added to CLAUDE.md
    - mello-team-one review: permissions 777→1777, CORS comment, --verbose note
    - Related: #70, #54, #66, #69

✅ **(COMPLETE) - comfyume-v1 #70 - Restore testing instance 009 + fix E2E inference**
    - Created: 2026-02-17 | Updated: 2026-02-17
    - Testing instance 009 (anegg.app) fully operational with E2E inference
    - Flux Klein 4B: 18s warm, 307s cold (model loading)
    - HTTP polling works when container is warm (LB stabilizes)
    - SFS volume mismatch: serverless uses PROD_SFS, testing uses CLONE_SFS
    - Related: #66, #54, #101, #48, #22

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

🚨 **TOP PRIORITY - comfyume-v1 #66 - Migrate from HTTP polling to SFS-based result delivery**
    - Created: 2026-02-17
    - ROOT CAUSE of inference regression: Verda LB routes history polls to wrong instance
    - Architecture: fire-and-forget POST /prompt → worker writes to SFS → QM watches filesystem
    - Kill serverless_proxy extension (fragile), move progress to QM WebSocket
    - Workers become vanilla ComfyUI (zero custom code) — migration-proof
    - Related: #101 (symptom), #48 (logging gap), #54 (missing --output-directory)

🚨 **CRITICAL - comfyume-v1 #101, #103 - Serverless Inference BROKEN**
    - Created: 2026-02-09 | Updated: 2026-02-17
    - ROOT CAUSE IDENTIFIED: Verda load balancer routes history polls to different instance (#66)
    - Yaml key on SFS confirmed CORRECT as of Feb 16 (latent_upscale_models)
    - Flux Klein WAS working (Feb 15 18:20 UTC — 2 images generated successfully)
    - **BROKEN** as of Feb 16 04:57 UTC — serverless returns `status=error`, not a cold start issue
    - Investigation: no code drift (all files match git), container healthy, models visible
    - Server rebooted Feb 15 15:19 UTC — container restarts NOT the cause (inference worked after)
    - **QM error logging deployed (#48)** — next failed job will log actual error details
    - **OpenTofu drift audit complete (#54)** — .tf matches live, no deployment config drift found
    - NEXT: trigger a test job to capture actual error via new QM logging

✅ **(COMPLETE) - comfyume-v1 #61 - nginx 500: .htpasswd regenerated**
    - Created: 2026-02-17 | Updated: 2026-02-17
    - .htpasswd was empty file after git ops from previous session
    - Regenerated 21 bcrypt entries (20 users + admin) via Python bcrypt from .env
    - Force-recreated nginx container, all auth working (200/401 verified)

✅ **(COMPLETE) - comfyume-v1 #58 - SSL: certbot renewal, CORS cleanup, doc corrections**
    - Created: 2026-02-17 | Updated: 2026-02-17
    - Pivoted from subdomain approach to keep path-based routing (simpler, already works)
    - Fixed certbot: standalone→webroot, added /var/www/certbot volume mount
    - Cleaned CORS whitelist (removed stale subdomain/old domain origins)
    - Corrected SSL references in 6 files (Namecheap→Let's Encrypt, exp 2026-05-12)
    - Synced .env to Verda (found 10 inconsistencies inc. R2 double .eu.eu bug)
    - Captured Ralph Loop local changes via PR #60
    - Recreated all 24 containers — all healthy
    - PR #59 merged

🔧 **IN PROGRESS - comfyume-v1 #54 - IaC: OpenTofu for Verda Serverless**
    - Created: 2026-02-16 | Updated: 2026-02-16
    - OpenTofu v1.11.5 installed on Mello, `verda-cloud/verda` v1.1.1 provider
    - `infrastructure/` dir: providers.tf, variables.tf, containers.tf, .gitignore, .lock
    - All 4 deployments imported + plan = 0 real drift
    - Drift audit found: `--output-directory` missing from 3 of 4 deployments, healthcheck `/` not `/system_stats`
    - CLAUDE.md updated with debugging + deployment change workflow
    - NEXT: first `tofu apply` on testing server, fix 3 missing `--output-directory` flags

✅ **(COMPLETE) - comfyume-v1 #48 - QM Error Logging**
    - Created: 2026-02-16 | Updated: 2026-02-16
    - poll_serverless_history now logs full error status + messages on failure
    - Returns immediately on error instead of polling for 10 minutes
    - Deployed to production QM via docker cp + restart (needs image rebuild to persist)

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
## Progress Report 18 - 2026-02-22 - Admin panel toggles, isolate mode, testing-009 branch (#75)

**Date:** 2026-02-22 | **Issues:** #75, #78, #79, #80

**Done:**
- Confirmed admin panel code already synced between comfyume and comfyume-v1 (1-line diff only)
- Created #75: admin panel isolate mode toggle
- Added GPU overlay mode toggle (localStorage `gpu_overlay_mode` = admin/user) for mello-team-one
- Added isolate mode toggle: OFF = normal, ON = all `/api/*` return 503 for fault isolation
- Backend: `GET/POST /api/admin/isolate`, middleware gate, `ADMIN_ISOLATE_MODE` env var (default false)
- Frontend: localStorage persistence + backend sync on page load
- Renamed from "Features" to "Isolate" — better semantics (OFF = normal, ON = everything disabled)
- Dashboard, `/health`, and `/api/admin/isolate` always accessible (can't lock yourself out)
- Added serverless timeout layers table to README.md (4 layers, only Layer 2 configurable)
- Fixed admin panel description: admin/operator, not instructor
- Created `testing-009` shared deployment branch (both teams merge here before deploying)
- Merged latest main (mello-team-one's GPU overlay, error handling, status_banner)
- All deployed to anegg.app and verified
- Created #78 (CSS MIME + manifest 401), #79 (favicon 404), #80 (userdata 404s) — all non-critical

**Commits:**
- `f0d36fb` feat: add overlay mode + features toggles to admin panel header (#75)
- `eb8679d` feat: wire admin features toggle to backend + localStorage (#75)
- `a0728c8` docs: add features toggle fault-isolation workflow to CLAUDE.md (#75)
- `396baf5` refactor: rename features toggle to isolate mode (#75)

**Branch strategy:**
- Feature branch: `testing-mello-admin-panel-team-2026-02-22` (off main)
- Shared deployment: `testing-009` (both teams merge here)
- PR #76 open for main

---
## Progress Report 17 - 2026-02-22 - Environment-isolated serverless deployed, SFS fix (#71, #72)

**Date:** 2026-02-22 | **Issues:** #71, #72, #54, #69

**Done:**
- Diagnosed SFS volume mismatch: serverless mounts PROD_SFS, testing mounts CLONE_SFS → images invisible to testing instance
- Created GH #71 (diagnosis) and #72 (apply steps)
- Added `environment` variable to IaC: `prod` → unchanged names, `test` → `comfyume-test-*` deployments
- Fixed .gitignore across ALL 7 repos on Mello (tfstate, terraform.tfvars — were NOT excluded)
- Added production safety verification to CLAUDE.md (state file isolation table)
- Addressed mello-team-one review: permissions 777→1777, CORS comment, --verbose note
- Installed OpenTofu v1.11.5 on testing-009
- `tofu plan` → 1 to add, 0 to change, 0 to destroy (production untouched)
- `tofu apply` → `comfyume-test-vca-ftv-h200-spot` created, mounting CLONE_SFS
- Updated testing-009 `.env` with testing endpoint, recreated QM container
- Restored htpasswd to correct per-user strong passwords (was incorrectly set to "workshop")
- Scrubbed docs of "workshop" password references
- Updated PR #69 title/description to cover all work on this branch

**Key learnings:**
- `docker restart` does NOT reload `.env` changes — must use `docker compose up -d`
- OpenTofu state is per-machine — fresh state on testing-009 cannot affect production
- `environment = "prod"` → empty prefix → deployment names byte-identical to production (backward compatible)

**Commits:**
- `6588f93` fix: add OpenTofu state files to .gitignore + production safety docs (#71, #54)
- `0c10d41` feat: add environment variable for isolated serverless deployments (#71)
- `5a4cc05` fix: address mello-team-one review — permissions, CORS, verbose (#71)
- `4ab61c6` fix: restore correct per-user credentials on testing-009, remove "workshop" refs

**Remaining:**
- Test inference on anegg.app → verify images appear via CLONE_SFS (not stale hedgehog)
- CLIP model error on cold start needs investigation (Feb 18 logs showed `clip input is invalid: None`)

---
## Progress Report 16 - 2026-02-17 - Testing instance 009 restored, E2E inference working (#70)

**Date:** 2026-02-17 | **Issues:** #70, #54, #66

**Done:**
- Created GH #70: infra: restore testing instance 009 (anegg.app) + fix E2E inference
- Phase 0: Created learnings doc `docs/learnings-testing-instance-009.md`
- Phase 1: SSH to instance, updated OS (`apt upgrade`), mounted CLONE_SFS + scratch disk
- Phase 2: Created testing variant of restore script (`-testing.sh`):
  - Changed hostname/IP/instance-ID to 009 (intelligent-rain-shrinks)
  - Domain: anegg.app (SSL cert obtained via certbot webroot)
  - SSH keys: switched from production to testing identity
  - Removed old PUB_KEY_VERDA (production host key)
- Phase 3: Restore completed. Fixed post-restore issues:
  - Wrong git remote (comfy-multi → comfyume-v1), switched to feature branch
  - .env was bare-bones — wrote comprehensive testing .env with all serverless config
  - USE_HOST_NGINX=false (containerized), stopped host nginx
  - nginx/.htpasswd was directory (Docker auto-created) — removed + recreated as file
  - Frontend image rebuilt from correct branch (old image missing `requests` module)
  - Generated docker-compose.users.yml for 5 users
  - nginx CORS: changed hardcoded `aiworkshop.art` to `$http_origin`
- Phase 4: All containers healthy (nginx, redis, QM, admin, user001-005)
  - 24 models visible, no Missing Models popup
  - SSL cert valid until 2026-05-18
  - QM: serverless mode, H200-SPOT active
- Phase 5: Fixed --output-directory in containers.tf (all 4 deployments)
  - Added anegg.app to QM CORS allow_origins
  - First inference attempt: 307s cold start, execution success, but `/outputs/user001` permission denied
  - Fixed permissions: `chmod -R 777 /mnt/scratch/outputs/`
  - Second inference: 18s warm, image generated + saved + displayed in ComfyUI
  - **E2E inference confirmed working**

**Key findings:**
- LB routing issue (#66) mitigated by warm containers — history poll succeeds after model loading
- SFS volume mismatch: serverless containers mount PROD_SFS, testing mounts CLONE_SFS
- SFS image delivery won't work cross-environment, but HTTP /view fallback works
- Restore script clones wrong repo (comfy-multi), needs manual remote URL fix
- Cold start ~5 min (model loading), warm inference ~18s

**Commits:**
- `eab1a1b` fix: add --output-directory to all serverless deployments + CORS for anegg.app (#70, #54)
- `2a81358` docs: update learnings from testing instance 009 — E2E inference confirmed (#70)

---
## Progress Report 15 - 2026-02-17 - anegg.app testing domain, branch strategy

**Date:** 2026-02-17 | **Issues:** #68

**Done:**
- User set up `anegg.app` domain pointing to testing instance 009 (65.108.33.80)
- Updated infrastructure-registry.md (private scripts) with domain field (I-16)
- Updated infrastructure.md (agent_docs) machines + environments tables
- Created PR #68 for comfyume-v1
- Decision: continue with branches (not fork) for #66 architecture work
- Created feature branch `testing-mello-admin-panel-team-new-testing-instance`

---
## Progress Report 14 - 2026-02-17 - nginx .htpasswd fix, session resume (#61)

**Date:** 2026-02-17 | **Issues:** #61, #58

**Context:**
- Resumed session. Previous session (Report 13) fixed SSL/certbot (#58), synced .env, captured Ralph Loop changes (#60), recreated all 24 containers — but .htpasswd was lost during git operations.
- #58 resolved: title updated to reflect path-based approach (no subdomains), certbot webroot working, CORS cleaned, docs corrected across 6 files.

**Done:**
- Created #61: nginx 500 — .htpasswd empty after git operations from previous session
- Regenerated 21 bcrypt entries (20 users + admin) via Python `bcrypt` from .env USER_CREDENTIALS
- Docker restart failed (cached directory mount type) — force-recreated nginx container
- Verified: user001→200, admin→200, no-auth→401, health→200
- User confirmed login working from browser
- Closed #61 (htpasswd not installed on Verda)

---
## Progress Report 13 - 2026-02-17 - SSL/certbot fix, .env sync, container recreation (#58, #59, #60)

**Date:** 2026-02-17 | **Issues:** #58, #59, #60

**Done:**
- Investigated SSL/nginx/URL confusion — found 4 problems: wrong DNS, no wildcard cert, path-only routing, broken certbot
- Created #58, then **pivoted from subdomains to path-based** after complexity analysis (CORS issues, duplicated nginx blocks, wildcard cert burden)
- Fixed certbot: standalone→webroot authenticator, added `/var/www/certbot` volume mount to docker-compose.yml, updated renewal config
- Cleaned CORS in queue-manager/main.py: removed admin.aiworkshop.art, *.aiworkshop.art, comfy.ahelme.net
- Corrected SSL references in CLAUDE.md (3 places), security.md, infrastructure.md, admin-server-containers-sys-admin.md
- Updated private scripts repo .env: DOMAIN, SSL paths, USE_HOST_NGINX=false, SERVER_MODE=serverless
- Synced .env to Verda — found 10 inconsistencies (R2 double .eu.eu bug, wrong REDIS_BIND_IP, stale domain refs)
- Captured Ralph Loop local changes from Verda: PR #60 (52 files), handled GitHub push protection (secrets in .env.bak)
- Recreated all 24 containers with `--force-recreate` — all healthy, certbot dry-run passed
- **Broke .htpasswd** during git operations → #61

---
## Progress Report 12 - 2026-02-16 - OpenTofu IaC Setup + Drift Audit (#54)

**Date:** 2026-02-16 | **Issues:** #54

**Done:**
- Installed OpenTofu v1.11.5 on Mello (ARM64 Ubuntu 24.04)
- Researched `verda-cloud/verda` provider v1.1.1 — supports `verda_container` for serverless
- Got full provider schema via `tofu providers schema -json` (7 resource types, `verda_container` confirmed)
- Created `infrastructure/` dir: providers.tf, variables.tf, containers.tf, terraform.tfvars.example, .gitignore
- Queried all 4 live deployments via Verda SDK — full config dump
- Drift audit — significant differences between documented and actual config:
  - `--output-directory /mnt/sfs/outputs` only on H200-spot (3 missing)
  - Healthcheck `/` not `/system_stats`
  - Exec-style entrypoint (no shell wrapper)
  - GPU names `H200`/`B300` (not `H200 SXM5 141GB`)
  - Queue load threshold `2` (not `1`), `deadline_seconds` missing from .tf
  - 3 volume mounts (scratch + memory + shared), not just shared
- Updated .tf files to match live production exactly
- Imported all 4 deployments: `tofu import` by name
- `tofu plan` = 0 real changes (only sensitive value display)
- Created GH #54 with full rationale, drift table, and remaining work
- Updated CLAUDE.md IaC section: setup, making changes, debugging workflow
- Updated `/verda-terraform` and `/verda-open-tofu` skills
- PRs #53 and #55 merged to main

**SFS volumes identified:**
- PROD: `be539393-...` (PROD_SFS-Model-Vault-22-Jan-01, 220GB NVMe_Shared)
- CLONE: `fd7efb9e-...` (CLONE_SFS-Model-Vault-16-Feb, 220GB NVMe_Shared)

**Provider limitations:** No `verda_sfs` resource — SFS management stays manual.

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

**Session 2 (same day, continued):**
- Completed handover file updates from interrupted session
- Pulled latest from main (CLAUDE.md + team files from Mello-Team-One)
- Investigated inference regression:
  - All containers healthy (20 frontends, QM, redis, nginx, admin)
  - QM health OK, INFERENCE_MODE=serverless, serverless_proxy deployed
  - Last successful inference: Feb 15 18:20 UTC (AFTER our container restarts)
  - Failed job Feb 16 04:57: `status=error` on serverless, but QM doesn't log error detail (#48)
  - Server rebooted Feb 15 15:19 UTC — no container restarts since
  - **No deployment drift** — all 4 critical files match git (QM, redirect.js, serverless_proxy, nginx)
  - Serverless container healthy (system_stats, object_info respond, models visible)
  - Execution errors but actual error message unknown — QM logging gap (#48)
- Created GH #48: QM poll_serverless_history doesn't log error details
- Added CLAUDE.md Critical Instruction #6: IaC via OpenTofu mandatory
- **Decision: IaC setup must happen on TESTING server, not production**

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
