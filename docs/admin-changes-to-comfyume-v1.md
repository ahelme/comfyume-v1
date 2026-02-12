**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-12
**Doc Updated:** 2026-02-12

---

# Complete Changelog — comfyume-v1

Every commit to the `comfyume-v1` repository from initial commit to present, with precise file/container/directory references. Organized by phase.

**Instance:** quiet-city-purrs-fin-01 (65.108.33.101), CPU.8V.32G, Ubuntu 24.04
**SFS:** /mnt/sfs (shared NFS, models + outputs + cache)
**Containers:** 24 healthy (nginx, redis, queue-manager, admin, 20 frontends)

---

## Phase 0: Repository Setup (2026-02-10)

### `d920010` — feat: initial commit — project docs, Claude skills, and agent config

**Direct to main.** Created the comfyume-v1 repository structure.

| File/Directory | Change |
|---|---|
| `CLAUDE.md` | Project instructions, architecture overview, critical gotchas |
| `README.md` | Public project overview |
| `.claude/skills/resume-context-*/` | Resume context skills for all teams (mello-team-one, verda-team-one, admin-panel-team, testing-scripts-team) |
| `.claude/skills/handover-*/` | Handover skills for all teams |
| `.claude/agent_docs/progress-*.md` | Progress logs per team |
| `.claude/agent_docs/*.md` | Agent docs: infrastructure, security, storage, gotchas, etc. |

### `b3663a6` — docs: update priorities for comfyume-v1, standardize headers (#1)

**Direct to main.** Standardized doc headers, updated priority tasks referencing GH Issue #1.

| File | Change |
|---|---|
| `.claude/agent_docs/progress-mello-team-one-dev.md` | Priority task structure for new CPU instance restore |
| `.claude/agent_docs/progress-all-teams.md` | Central log updated |

### `c0bd29e` — docs: clean up about-us.md across all team resume skills

**Direct to main.** Standardized the "about us" docs loaded at session start.

| File | Change |
|---|---|
| `.claude/skills/*/about-us.md` | Cleaned up formatting across all team skills |

---

## Phase 1: Pre-Restore Preparation (2026-02-11 early)

### `0fb1936` — refactor: replace hardcoded Verda IP with $VERDA_IP from .env (#1)

**Direct to main.** Decoupled server IP from code so the restore script and deploy script work on any instance.

| File | Change |
|---|---|
| Multiple scripts and docs | `65.108.33.101` → `$VERDA_IP` (from `.env`) |

### `c9baa4d` — docs: add trigger-based agent docs table with TL;DR micro-summaries

**Direct to main.** Added progressive disclosure table to CLAUDE.md for agent docs.

| File | Change |
|---|---|
| `CLAUDE.md` | Agent Docs table with TL;DR using `·` `@` `!` `:` `→` separators |

### `23760f9` — docs: add 3-step onboarding to resume skills (meet collaborator, meet yourself, load context)

**Direct to main.** Improved the session resume workflow.

| File | Change |
|---|---|
| `.claude/skills/resume-context-*/context.md` | 3-step onboarding: about-us, from-claude-on-being, context loading |

---

## Phase 2: Restore and Initial Bring-Up (2026-02-11 mid-day)

### `2c42279` — feat: import working app code from comfyume repo (Mello frozen state)

**Direct to main.** THE BIG IMPORT. Copied the working app codebase from the older `comfyume` repo (which was frozen with `chmod -R a-w` on Mello).

| File/Directory | What was imported |
|---|---|
| `comfyui-frontend/` | Dockerfile, docker-entrypoint.sh, custom_nodes/ |
| `comfyui-worker/` | worker.py, start-worker.sh, Dockerfile |
| `queue-manager/` | main.py, config.py, models.py, redis_client.py |
| `admin/` | Admin dashboard (FastAPI + templates) |
| `nginx/` | nginx.conf with SSL, dynamic routing |
| `docker-compose.yml` | Service orchestration (redis, qm, admin, nginx, worker) |
| `docker-compose.users.yml` | 20 user frontend containers (auto-generated) |
| `scripts/` | generate-user-compose.sh, start.sh, stop.sh, status.sh |
| `data/` | User data directories, workflow templates |
| `SERVERLESS_UPDATE.md` | Serverless implementation notes |
| `.env.example` | Environment variable template |

**Containers defined:** comfy-nginx, comfy-redis, comfy-queue-manager, comfy-admin, comfy-worker-1, comfy-user001 through comfy-user020

### `c405f9a` — docs: update progress with session 40 discoveries and restore plan (#1, #2, #3)

**Direct to main.** Documented findings from running restore script on quiet-city.

### `0d587fa` — docs: update progress — restore script running on quiet-city, DNS updated (#1, #2, #3)

**Direct to main.** DNS pointed to new instance, restore in progress.

---

## Phase 3: Configuration Fixes (2026-02-11 afternoon)

These commits went **directly to main** to support the restore script which pulls from main.

### `a9f5693` — fix: use REDIS_HOST directly in docker-compose (remove APP_SERVER_REDIS_HOST indirection)

Fixed Redis configuration confusion. The `docker-compose.yml` was using `APP_SERVER_REDIS_HOST` but `.env` only had `REDIS_HOST`.

| File | Change |
|---|---|
| `docker-compose.yml` | `${APP_SERVER_REDIS_HOST}` → `${REDIS_HOST}` (line ~95) |

**Container affected:** comfy-queue-manager (connects to comfy-redis)

### `749def7` — fix: add gpu profile to worker-1 so it only starts on GPU instances

Worker container was failing with nvidia driver errors on our CPU-only instance.

| File | Change |
|---|---|
| `docker-compose.yml` | Added `profiles: [gpu]` to worker-1 service definition |

**Container affected:** comfy-worker-1 (now requires `--profile gpu` to start)

### `5ecbaa4` — fix: remove unused redis.conf volume mount (config via command line)

Redis was trying to mount a `redis.conf` file that didn't exist.

| File | Change |
|---|---|
| `docker-compose.yml` | Removed `./redis.conf:/usr/local/etc/redis/redis.conf` volume mount |

**Container affected:** comfy-redis (now configured entirely via `redis-server --requirepass`)

### `93bf1a1` — fix: use dynamic DNS resolution in nginx to prevent startup crashes

Nginx was crashing because upstream containers weren't started yet. Fixed with `resolver` and variable-based proxy_pass.

| File | Change |
|---|---|
| `nginx/nginx.conf` | Added `resolver 127.0.0.11 valid=30s` (Docker DNS), changed `proxy_pass http://user001:8188` to use `set $upstream_userXXX` variables |

**Container affected:** comfy-nginx (now starts even if frontend containers are still booting)

### `f38f260` — docs: update progress — worker gpu profile fix, branch rename, third restore run (#1, #2, #5)

**Direct to main.** Progress update documenting the GPU profile fix and branch rename.

---

## Phase 4: Production Live + Debug (2026-02-11 afternoon/evening)

### `cae94ab` — docs: production live! nginx fixed, SSL cert, end-to-end working (#1)

**Direct to main.** Documented that production was live: nginx serving, SSL cert installed, 24 containers healthy.

### `580e512` — docs: debug session — queue_redirect working, loader API mismatch (#1, #8)

**Direct to main.** Debug session findings — queue_redirect extension was intercepting Queue Prompt correctly, but default_workflow_loader had API mismatch with v0.11.0.

### `9d812c8` — docs: clarify default_workflow_loader is convenience add-on, not core (#1)

**Direct to main.** Clarified that the workflow loader extension is optional.

### `c613a06` — fix: self-healing custom nodes + v0.11.0 workflow loader API (#1, #8)

**Direct to main.** Fixed the custom nodes deployment mechanism in docker-entrypoint.sh.

| File | Change |
|---|---|
| `comfyui-frontend/docker-entrypoint.sh` | Added self-healing: if custom_nodes volume is empty, restore from `/tmp/custom_nodes_backup` |
| `comfyui-frontend/Dockerfile` | Added `cp -r /comfyui/custom_nodes /tmp/custom_nodes_backup` during build |

**Containers affected:** All 20 comfy-user001 through comfy-user020 (on next rebuild)
**Directory:** `/comfyui/custom_nodes/` (inside container), `/tmp/custom_nodes_backup/` (inside container)

### `b5f74a6` — fix: wait for canvas before loading workflow + progress update (#1, #8, #12)

**Direct to main.** Fixed default_workflow_loader timing issue — was trying to load before canvas was ready.

| File | Change |
|---|---|
| `comfyui-frontend/custom_nodes/default_workflow_loader/web/loader.js` | Added canvas readiness check before loading workflow |

---

## Phase 5: Extensions Refactor + Deploy Script (2026-02-11 evening, via PRs)

From this point forward, all changes went through proper git flow (feature branches + PRs).

### PR #14 — `b883467` — fix: GPU progress banner + sync deployment drift (#1, #13)

**Branch:** `fix/sync-deployment-drift-13` | **Merged:** 2026-02-11 17:59 | **Issue:** #13

Synced 6 surgical SCP deployments that had bypassed git back into the repo. Added floating GPU progress banner.

| File | Change |
|---|---|
| `comfyume-extensions/queue_redirect/web/redirect.js` | Added floating status banner showing GPU inference progress |
| `comfyui-frontend/docker-entrypoint.sh` | Synced deployed version back to git |
| `queue-manager/main.py` | Synced serverless submission logic |
| `nginx/nginx.conf` | Synced dynamic DNS resolution |
| `docker-compose.yml` | Synced worker gpu profile, redis config |

**Containers affected:** All frontends (redirect.js loaded by browser), comfy-queue-manager

### PR #15 — `2e172ba` — refactor: factor out extensions to comfyume-extensions/ (#12, #13)

**Branch:** `refactor/comfyui-customisations-12` | **Merged:** 2026-02-11 18:12 | **Issue:** #12

Moved ComfyuME customizations OUT of `comfyui-frontend/` into a separate `comfyume-extensions/` directory at project root.

| File/Directory | Change |
|---|---|
| `comfyume-extensions/` | **NEW directory** at project root |
| `comfyume-extensions/extensions.conf` | **NEW** — enable/disable extensions (queue_redirect ON, default_workflow_loader OFF) |
| `comfyume-extensions/queue_redirect/` | Moved from `comfyui-frontend/custom_nodes/queue_redirect/` |
| `comfyume-extensions/default_workflow_loader/` | Moved from `comfyui-frontend/custom_nodes/default_workflow_loader/` |
| `comfyui-frontend/docker-entrypoint.sh` | Updated to read `extensions.conf` and deploy enabled extensions to `/comfyui/custom_nodes/` |
| `comfyui-frontend/Dockerfile` | Updated to COPY `comfyume-extensions/` to `/build/comfyume-extensions/` |
| `scripts/deploy.sh` | **NEW** — git-based deploy script (push, pull on server, rebuild, recreate) |
| `.dockerignore` | Updated to exclude `.claude/`, `docs/`, etc. from Docker build context |

**Architecture change:** All ComfyUI customizations now live in `comfyume-extensions/` (CLAUDE.md rule #4).

### PR #16 — `9006781` — docs: add extension separation and deploy flow rules (#12, #13)

**Branch:** `docs/claude-md-extensions-rule` | **Merged:** 2026-02-11 18:18

| File | Change |
|---|---|
| `CLAUDE.md` | Added Critical Instruction #4 (extensions in comfyume-extensions/) and #5 (deploy via git flow) |

### PR #17 — `53f51ad` — feat: ComfyUI QA loop skill for autonomous workflow testing (#1)

**Branch:** `feat/comfyui-qa-loop` | **Merged:** 2026-02-11 18:21

Created the autonomous testing infrastructure that Ralph Loop uses.

| File/Directory | Change |
|---|---|
| `.claude/skills/comfyui-fix-loop/SKILL.md` | **NEW** — 6-phase QA protocol (navigate, load workflow, queue prompt, observe, diagnose, fix) |
| `.claude/qa-state.json` | **NEW** — QA state tracking (workflows, criteria, bugs found) |

### PR #18 — `bd358f3` — fix: QA loop improvements — context, iterations, resume (#1)

**Branch:** `fix/qa-loop-improvements` | **Merged:** 2026-02-11 18:26

| File | Change |
|---|---|
| `.claude/skills/comfyui-fix-loop/SKILL.md` | 50 max iterations, Phase 0 auto-resume from qa-state.json, context management, stuck handler |

### PR #19 — `8bc4936` — docs: session handover — QA loop ready (#1)

**Branch:** `docs/handover-session-47` | **Merged:** 2026-02-11 18:32

| File | Change |
|---|---|
| `.claude/skills/resume-context-mello-team-one/context.md` | Updated handover with QA loop instructions |
| `.claude/agent_docs/progress-mello-team-one-dev.md` | Progress Report 47 |
| `.claude/agent_docs/progress-all-teams.md` | Central log updated |

---

## Phase 6: Ralph Loop Team Created (2026-02-11 evening)

### PR #20 — `e258c8c` — feat: create Mello Ralph Team — autonomous QA agent (#1)

**Branch:** `feat/mello-ralph-team` | **Merged:** 2026-02-11 18:36

Created the Ralph Team as an autonomous QA agent identity.

| File/Directory | Change |
|---|---|
| `.claude/skills/resume-context-mello-ralph-team/` | **NEW** — SKILL.md, about-us.md, context.md |
| `.claude/skills/handover-mello-ralph-team/` | **NEW** — SKILL.md |
| `.claude/agent_docs/progress-mello-ralph-team-dev.md` | **NEW** — Ralph team progress log |
| `CLAUDE.md` | Added Mello Ralph Team to Dev Teams table |

---

## Phase 7: Ralph Loop Execution (2026-02-11 19:00 — 2026-02-12 02:00)

Ralph Loop ran autonomously, testing the Flux2 Klein 9B workflow and engineering fixes for image delivery.

### PR #21 (merged from `mello-ralph-team` branch) — multiple commits

**Branch:** `mello-ralph-team` | **Merged:** 2026-02-11 19:55

Ralph's first iteration: credential fixes, QA iteration 1 results, skill rename.

| Commit | File | Change |
|---|---|---|
| `467b4d7` | `.claude/skills/comfyui-fix-loop/SKILL.md` | Reference `.env` line 367 for test credentials instead of hardcoding |
| `74fb6eb` | `.claude/agent_docs/progress-mello-ralph-team-dev.md` | Progress Report 2: first loop run, credential fix |
| `04428bb` | `.gitignore` | Exclude `.claude/*.local.md` (session files) |
| `cf0be64` | `.claude/qa-state.json` | QA Iteration 1 results: 5/7 criteria pass, image delivery gap confirmed |
| `97c4f0c` | `.claude/skills/comfyui-fix-loop/` | Renamed from `comfyui-qa-loop` → `comfyui-fix-loop` (10 files) |

**Diagnosis:** Queue Prompt works, GPU inference completes, but `submit_to_serverless()` in `queue-manager/main.py` only POSTs `/prompt` and never fetches `/api/history/{prompt_id}` or `/api/view` to get images.

### PR #23 — `74bccc0` — feat: image delivery gap fix — serverless proxy + QM image fetching (#22)

**Branch:** `fix/image-delivery-gap` | **Merged:** 2026-02-11 19:54 | **Issue:** #22

THE CORE FIX. A 3-part coordinated solution for the image delivery gap.

| File | Change | Lines |
|---|---|---|
| `comfyume-extensions/serverless_proxy/__init__.py` | **NEW** (177 lines) — monkey-patches `PromptExecutor.execute()` to proxy through QM. Feature-gated by `INFERENCE_MODE=serverless`. Sends WebSocket messages for queue/progress/history. | 1-185 |
| `queue-manager/main.py` | After `/prompt`, polls `/api/history/{prompt_id}`, downloads images via `/view`, saves to `/outputs/{user_id}/` | +137/-4 |
| `comfyume-extensions/queue_redirect/web/redirect.js` | Checks `/api/health` for `inference_mode`, auto-defers to native queue in serverless mode | +21/-1 |
| `comfyui-frontend/docker-entrypoint.sh` | Output dir symlink (`/comfyui/output → /outputs`), exports `INFERENCE_MODE` env var | +14/-2 |
| `comfyume-extensions/extensions.conf` | Enabled `serverless_proxy` extension | +3/-1 |
| `docker-compose.users.yml` | Added `INFERENCE_MODE=${INFERENCE_MODE:-local}` to all user containers | +20 |
| `scripts/generate-user-compose.sh` | Pass `INFERENCE_MODE` to generated user containers | +1 |
| `.claude/qa-state.json` | Updated BUG-001 status and files_modified | +19/-11 |

**Containers affected:** All 20 frontends (new extension + env var), comfy-queue-manager (polling + image fetch)
**New extension:** `serverless_proxy` in `/comfyui/custom_nodes/serverless_proxy/`

### PR #24 — `b93fe9f` — fix: /api/health route alias for nginx proxy path (#22)

**Branch:** `mello-ralph-team` | **Merged:** 2026-02-11 20:00

nginx proxied `/api/health` preserving the `/api/` prefix, but QM only had `/health`. redirect.js's serverless mode check failed silently.

| File | Change | Line |
|---|---|---|
| `queue-manager/main.py` | Added `@app.get("/api/health")` alias alongside existing `/health` | +1 |

**Container affected:** comfy-queue-manager

### PR #25 — `77c3a6e` — fix: set history_result in serverless proxy for ComfyUI v0.11.0 (#22)

**Branch:** `fix/history-result-attr` | **Merged:** 2026-02-11 20:10

ComfyUI v0.11.0's `prompt_worker` reads `e.history_result` after `execute()` returns. The serverless proxy wasn't setting this attribute, causing `AttributeError` crash.

| File | Change | Lines |
|---|---|---|
| `comfyume-extensions/serverless_proxy/__init__.py` | Set `self.history_result = {"outputs": outputs, "meta": {}}` in both success and error paths | +3 |

**Container affected:** All 20 frontends (via serverless_proxy extension)

### PR #26 — `b4116d1` — fix: improve serverless polling diagnostics and timeouts (#22)

**Branch:** `fix/qa-improved-polling-and-timeouts` | **Merged:** 2026-02-12 01:11

Model loading on H200 takes 200+ seconds, causing timeouts.

| File | Change | Lines |
|---|---|---|
| `queue-manager/main.py` | `max_wait` 240s → 300s, wall-clock timing, detailed response logging | +46/-9 |
| `comfyume-extensions/serverless_proxy/__init__.py` | `urlopen` timeout 300s → 600s | +6/-2 |

**Containers affected:** comfy-queue-manager, all frontends

### PR #27 — `48fb876` — fix: increase poll timeout to 600s, reduce per-request to 10s (#22)

**Branch:** `fix/qa-increase-timeouts-and-logging` | **Merged:** 2026-02-12 01:32

Further timeout tuning after observing cold start behavior.

| File | Change | Lines |
|---|---|---|
| `queue-manager/main.py` | `max_wait` 300s → 600s, per-request timeout 30s → 10s (fail fast, retry more), detailed output structure logging | +25/-15 |

**Container affected:** comfy-queue-manager

### PR #28 — `f79eefc` — feat: SFS-based image delivery for serverless mode (#22)

**Branch:** `fix/qa-sfs-image-delivery` | **Merged:** 2026-02-12 01:58

The pivotal fix. DataCrunch routes HTTP requests to different container instances, so `/view` downloads return 404. SFS is shared NFS — all containers can read/write the same files.

| File | Change | Lines |
|---|---|---|
| `queue-manager/main.py` | `fetch_serverless_images()` tries SFS (`/mnt/sfs/outputs/`) first, HTTP fallback | +64/-70 |
| `docker-compose.yml` | Added `/mnt/sfs/outputs:/mnt/sfs/outputs:ro` volume mount to queue-manager | +2 |

**Containers affected:** comfy-queue-manager (new SFS mount)
**Directory:** `/mnt/sfs/outputs/` (shared between serverless containers and queue-manager)

---

## Phase 8: Ralph Loop Results Logged (2026-02-12)

### `e6fd900` — fix: log Ralph Loop results — QA passed, image delivery fixed

**Branch:** `ralph-changes-unlogged` | **PR:** #32 (open)

Final Ralph Loop artifacts after overnight run. Iteration 4 passed all 8 QA criteria.

| File | Change |
|---|---|
| `.claude/qa-state.json` | Iteration 4, phase "passed", all 8 criteria green for Flux2 Klein 9B |
| `SERVERLESS_UPDATE.md` | Documented `--output-directory /mnt/sfs/outputs` flag (line 98) |
| `.claude/ralph-debug-hook.sh` | **NEW** (138 lines) — debug wrapper for Ralph Loop stop hook |

---

## Server-Side Changes (NOT in git — applied live on production)

These changes were applied directly on quiet-city (65.108.33.101) during Ralph Loop execution. They need to be codified in restore scripts.

### BUG-002: SFS output directory permissions

```bash
chmod 1777 /mnt/sfs/outputs/
```

**Problem:** `mkdir` created `/mnt/sfs/outputs/` with `755 root:root`. ComfyUI on serverless containers runs as uid 1000 (non-root) and couldn't write.
**Fix:** Sticky bit + world-writable (`1777`), same pattern as `/tmp`.
**Where to codify:** `restore-verda-instance.sh` in comfymulti-scripts repo.

### BUG-003: DataCrunch container --output-directory flag

**Problem:** DataCrunch container start command only had `--listen`, `--port`, `--extra-model-paths-config`. ComfyUI saved images to `/workspace/ComfyUI/output/` (container-local, ephemeral).
**Fix:** Updated via Verda Python SDK `update_deployment()` API:
```bash
python3 -c "
from verda import Verda
client = Verda()
client.containers.update_deployment('comfyume-vca-ftv-h200-spot', cmd=[
    'python3', '/workspace/ComfyUI/main.py',
    '--listen', '0.0.0.0', '--port', '8188',
    '--extra-model-paths-config', '/mnt/sfs/extra_model_paths.yaml',
    '--output-directory', '/mnt/sfs/outputs'
])
"
```
**Where to codify:** Deployment automation script or Verda Terraform config.

### SFS wrapper script update

**File:** `/mnt/sfs/start-comfyui-wrapper.sh` (on SFS, not in git)
**Change:** Ensures `/mnt/sfs/outputs/` has correct permissions on startup.

---

## Summary Statistics

| Metric | Value |
|---|---|
| Total commits | 35 |
| Commits direct to main | 17 (Phase 0-4) |
| Commits via PRs | 18 (Phase 5-8, PRs #14-#28, #32) |
| PRs created | 16 (#14-#28, #32) |
| PRs merged | 15 |
| PRs open | 1 (#32) |
| GH Issues created | 17 (#1-#13, #22, #29-#31) |
| Files created | ~100+ (initial import) |
| Key new files | serverless_proxy/__init__.py, extensions.conf, deploy.sh, qa-state.json |
| Server-side fixes | 3 (SFS permissions, --output-directory, wrapper script) |
| Time span | 2026-02-10 to 2026-02-12 (3 days) |

---

## GH Issues Reference

| # | Title | State | Phase |
|---|---|---|---|
| #1 | Restore working app state: Create NEW CPU instance | CLOSED | 2-4 |
| #2 | Adapt restore script for comfyume-v1 | OPEN | 2 |
| #3 | Get comfyume-v1 to WORKING EDITION on quiet-city | OPEN | 2-4 |
| #4 | Build Docker images with GitHub Actions + GHCR | OPEN | Future |
| #5 | Build single shared frontend image | OPEN | Future |
| #6 | Use CPU-only PyTorch in frontend image | OPEN | Future |
| #7 | Redis config: remove redis.conf mount, investigate warnings | OPEN | 3 |
| #8 | App flow map: Queue Prompt to serverless inference | OPEN | 4, 7 |
| #9 | Infrastructure config map | OPEN | Future |
| #10 | Missing workshop extensions | OPEN | 4 |
| #11 | Core deployment step missing: no custom nodes | OPEN | 4 |
| #12 | Factor out ComfyuME customisation layer | CLOSED | 5 |
| #13 | Sync deployment drift: 6 SCP deployments bypassed git | CLOSED | 5 |
| #22 | Image delivery gap: QM never fetches images | OPEN | 7 |
| #29 | Post-Ralph-Phase-1: commit changes, docs, code flow | OPEN | 8 |
| #30 | Post-Ralph cleanup: commit, docs, testing server | OPEN | 8 |
| #31 | Post-Ralph-Phase-2: testing site, restore script fixes | OPEN | Future |
