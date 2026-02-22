**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) · anegg.app (testing)
**Doc Created:** 2026-02-07
**Doc Updated:** 2026-02-22

| Environment | URL | Instance | SSH |
|---|---|---|---|
| **Production** | https://aiworkshop.art | quiet-city (65.108.33.101) | `ssh dev@100.89.38.43` |
| **Testing (active)** | https://anegg.app | intelligent-rain-shrinks (65.108.33.80) | `ssh root@65.108.33.80` |

**All teams are currently working on the testing instance (anegg.app). Do NOT deploy to production without explicit approval.**

---
# Project Progress Tracker
**Target:** Workshop Feb 25 2026
### Implementation Phase
**MAIN Repo:** comfyume-v1 (https://github.com/ahelme/comfyume-v1)
**Branch:** mello-scripts-team-*
**Deploy branch:** testing-009 (shared — merge here before deploying to anegg.app)
**Phase:** Testing Scripts
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

- [x] P1 #6 Testing infrastructure rewrite — MERGED (PR #75)
- [x] P1 #22 Phase 3: archive scripts, update .env.example, update READMEs — MERGED (PR #85)
- [x] P1 #71 Mello cleanup script + CLAUDE.md updates
  - 2026-02-08 DONE
  - cleanup-mello.sh created, CLAUDE.md updated (Quick Links, architecture, tech stack)
- [x] P2 #111 Bidirectional file sharing on mello — DONE
  - 2026-02-09
  - /mello-share/, /mac-share/, /upload, /login with cookie auth
  - upload.aiworkshop.art subdomain live, paste (Cmd+V) support
- [x] P2 #111 Favicon — official ComfyUI logo — PR #112 MERGED
  - 2026-02-09 DONE
  - Yellow C on blue, data URI + nginx inline + static files
- [ ] P2 #111 Deploy favicon to Verda
  - 2026-02-09
  - Steps in GH issue #111 comment
  - `git pull`, rebuild admin, update host nginx favicon block, reload
- [ ] P2 Run test.sh on Verda app server to validate
  - 2026-02-07
  - Requires services running on production

---

# Progress Reports

---
### Implementation Phase
**Repository:** comfyume (https://github.com/ahelme/comfyume)
**Branch:** testing-scripts-team-2
**Phase:** Dev tooling + favicon

## Progress Report 8 - 2026-02-09 - File Sharing, Favicon, upload.aiworkshop.art (#111)

**Date:** 2026-02-09

**Done:**
- Created #111: bidirectional file sharing on mello (host nginx, not in repo)
  - `/login` — HTML form with cookie-based auth (browser saves password, 30-day cookie)
  - `/mello-share/` — browse/download files from mello (`/var/www/mello-share/`)
  - `/mac-share/` — browse uploads from Mac (`/var/www/mac-share/`)
  - `/upload` — drag & drop + Cmd+V paste upload form (WebDAV PUT, 500MB max)
  - nginx `map` on `dev_share` cookie → skips basic auth if valid, curl still works
  - htpasswd with admin creds from private scripts `.env`
- Set up `upload.aiworkshop.art` subdomain on mello
  - nginx server block at `/etc/nginx/sites-enabled/upload.aiworkshop.art`
  - SSL via SAN cert (portainer.aiworkshop.art covers upload subdomain)
  - Root (`/`) → upload page directly
- Favicon: replaced 3-dots design with official ComfyUI logo
  - Yellow "C" on blue (#172DD7) from Dashboard Icons (CC BY 4.0)
  - `admin/dashboard.html` — data URI in `<head>`
  - `nginx/nginx.conf` — inline SVG at `/favicon.ico`
  - `nginx/static/favicon.svg` + `.png` — static files
  - PR #112 merged

**Pending:**
- Deploy favicon to Verda (steps in #111 comment)
  - nginx `map` on `dev_share` cookie skips basic auth; curl still works with `-u`
  - htpasswd with admin creds from private scripts `.env`
- Favicon (fb51baf): inline SVG data URI for admin + nginx `return 200` for user frontends
  - 3 connected dots (green/blue/purple) representing ComfyUI nodes

---

## Progress Report 7 - 2026-02-08 - Model Download Engine (#93)

**Date:** 2026-02-08

**Done:**
- Created #93: model download engine in admin panel
- Backend (`admin/app.py`):
  - Download engine with resume support (Range header + temp files)
  - HuggingFace gated model detection (HEAD request, token check)
  - SSE streaming for real-time progress (`sse-starlette`)
  - ntfy.sh push notifications on completion
  - 5 new endpoints: check, download, status, stream, cancel
- Frontend (`admin/dashboard.html`):
  - Download progress panel with progress bar, console log, cancel button
  - "Check Downloads" button: scans HF gated status, groups by downloadable/gated/no-url
  - "Download All Missing" button + per-model "DL" buttons
  - SSE EventSource reconnects on tab switch if download active
- Config:
  - `docker-compose.yml`: models mount `:ro` → writable, `HF_TOKEN`/`NTFY_TOPIC` env vars
  - `.env.example`: new MODEL DOWNLOADS section
  - `admin/requirements.txt`: added `sse-starlette==2.2.1`
  - `nginx/nginx.conf`: `proxy_buffering off` + `proxy_cache off` on admin location for SSE

---

## Progress Report 6 - 2026-02-08 - Portainer Edge Agent in Restore Script

**Date:** 2026-02-08

**Done:**
- Updated `restore-verda-instance.sh` v0.4.0 → v0.4.1 (private scripts repo)
  - Filled in `VERDA_EDGE_ID` and `VERDA_EDGE_KEY` (were empty)
  - Set `VERDA_PORTAINER_CONNECTION_MODE` to `http2` (was `http`)
  - Added Step 16: Start Portainer edge agent (`docker run` with EDGE_PROTOCOL=http2, EDGE_INSECURE_POLL=1, --restart always)
- Commit: 9b66c7c pushed to comfymulti-scripts main

---

## Progress Report 5 - 2026-02-08 - Issue #71 Mello Cleanup

**Date:** 2026-02-08

**Done:**
- Created `scripts/cleanup-mello.sh` — dry-run by default, --execute to remove containers/images
- Updated CLAUDE.md: Quick Links → aiworkshop.art, architecture diagram → Verda CPU + DataCrunch serverless, tech stack → Mello as staging/backup, server table updated
- Containers already removed from Mello by user

---

## Progress Report 4 - 2026-02-07 - Issue #22 Phase 3 Complete

**Date:** 2026-02-07

**Done:**
- Archived `create-gpu-quick-deploy.sh` and `verda-startup-script.sh` to `scripts/archive/`
- Updated `.env.example` v0.3.2 → v0.3.5: added INFERENCE_MODE, serverless endpoint vars, SERVERLESS_API_KEY
- Updated `comfyui-worker/README.md`: added serverless production note
- Updated `README.md`: added aiworkshop.art, serverless architecture, current status

---

## Progress Report 3 - 2026-02-07 - PR #75 Created, Issue #6 Updated

**Date:** 2026-02-07

**Done:**
- PR #75 created: `testing-scripts-team` → `main` (7 commits)
- Issue #6 body rewritten with current architecture, deliverables table, acceptance criteria
- Issue #6 closed — implementation complete
- Pushed all commits + progress updates to remote

---

## Progress Report 2 - 2026-02-07 - Testing Infrastructure Rewrite (#6)

**Date:** 2026-02-07

**Done:**
- `scripts/test-helpers.sh` — shared library (colors, counters, pass/fail, check_http, container helpers)
- `scripts/test.sh` — rewritten: 10 sections for serverless arch, no worker refs, docker compose v2
- `scripts/test-serverless.sh` — new: serverless E2E test with --dry-run/--all/--timeout flags
- `scripts/test-connectivity.sh` — new: Redis/QM/nginx/domain/SSL/Docker network validation
- `docs/admin-testing-guide.md` — new: comprehensive testing guide (10 sections, troubleshooting, reference)
- `scripts/status.sh` — fixed docker-compose → docker compose (3 occurrences)
- `scripts/load-test.sh` — updated "next steps" (removed worker reference)
- `docs/testing-guide.md` → `docs/archive/testing-guide-load-test.md` (archived)

**Key decisions:**
- test.sh sources test-helpers.sh (DRY, consistent output across all test scripts)
- Section 7 (Serverless) only runs when INFERENCE_MODE=serverless
- Section 10 (SSL) only runs when DOMAIN is set and not example value
- test-serverless.sh --dry-run is safe (no GPU cost) — default for CI
- Endpoints returning 401 treated as "route exists" (auth-protected = valid)

---

## Progress Report 1 - 2026-02-07 - Testing Scripts Team Initialized

**Date:** 2026-02-07

**Done:**
- Team initialization: progress file, handover command, resume context, onboarding file
- Branch created: `testing-scripts-team`

---
