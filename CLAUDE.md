**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**CURRENT Project Repository:** https://github.com/ahelme/comfyume-v1
**OLDER Project Repository:** https://github.com/ahelme/comfyume
**NOTE:** The older repo is more advanced, but is broken. This repo will revert to a stable state (by rsync from older OS drive) then we will cherry pick from the advanced yet broken older repo.
**Domain:** aiworkshop.art (production) · staging.aiworkshop.art · testing.aiworkshop.art
**Doc Updated:** 2026-02-16

---

## What We're Building

A multi-user ComfyUI platform for video generation workshops for professional filmmakers.
- CPU app hosting on Verda (aiworkshop.art) -- nginx, Redis, queue-manager, 20 user frontends
- Serverless GPU inference on Verda (H200/B300) -- scales on demand, pay per use
- Models and backups on Cloudflare R2 (.eu, cheap)

### Key Requirements

- Split architecture: CPU app server (Verda) + serverless GPU workers (Verda H200/B300)
- 20 isolated ComfyUI web interfaces
- Central job queue (FIFO/round-robin/priority)
- Serverless GPU workers scaling on demand
- HTTPS with aiworkshop.art domain (SSL cert via Let's Encrypt)
- HTTP Basic Auth password protection
- Tailscale VPN for secure Redis connection
- Persistent user storage
- Admin dashboard for instructor
- Grafana, Prometheus, Loki, Dry for monitoring
- FUTURE: ComfyGit (formerly ComfyDock)

### Quick Links

| Environment | URL | Health |
|---|---|---|
| **Production** | https://aiworkshop.art/ | /health |
| **Staging** | https://staging.aiworkshop.art/ | /health |
| **Testing** | https://testing.aiworkshop.art/ | /health |
| **Admin** | https://aiworkshop.art/admin | — |
| **API** | https://aiworkshop.art/api/queue/status | — |

---

## Critical Instructions

1. **BELIEVE THE USER** -- When the user reports something isn't working, investigate. Don't dismiss with "try cache refresh".
2. **USE LATEST STABLE LIBRARIES** as of Jan 2026.
3. **CHECK FOR EXISTING CODE FIRST** -- NEVER rewrite code that already exists. ALWAYS check for previous solutions.
4. **ALL COMFYUI CUSTOMISATIONS GO IN `comfyume-extensions/`** -- Any code that modifies, extends, or wraps ComfyUI behavior MUST live in `comfyume-extensions/`, never inside `comfyui-frontend/`. This is for separation of concerns, easy bugfixing, modularity, migration-friendliness, and ease of finding our changes vs upstream ComfyUI. Enable/disable extensions via `comfyume-extensions/extensions.conf`.
5. **DEPLOY VIA GIT FLOW** -- Use `./scripts/deploy.sh`. Never SCP files directly to production. Flow: edit → commit → push → deploy script handles the rest.
6. **USE `docs/comfyui-debugging.md` FOR ALL COMFYUI BUGS** -- Comprehensive debugging reference: CLI flags, API endpoints, container logs, monitoring, serverless-specific issues, common workflows. Check this BEFORE investigating any ComfyUI-related issue.
7. **INFRASTRUCTURE AS CODE (IaC) — MANDATORY** -- All Verda infrastructure MUST be managed via OpenTofu. NEVER make manual changes to serverless deployments, instance configs, or SFS settings via SDK calls, console clicks, or ad-hoc scripts. Untracked changes cause silent regressions.
8. **NEVER GENERATE SSH KEYS WITHOUT CONSULTING THE USER. EVER!** -- SSH keys are identity. Do not create, delete, or modify SSH keys on any machine without explicit user approval. Always check `.env` and `secrets/ssh/` for existing keys first.

### IaC Workflow (OpenTofu)

**Tool:** OpenTofu v1.11.5 · **Provider:** `verda-cloud/verda` v1.1.1
**Installed on:** Mello (local dev) + Verda (`/root/tofu/`)
**Config:** `infrastructure/` dir (committed) · State: local `.tfstate` (gitignored)

**What's managed (4 serverless deployments):**
- `comfyume-vca-ftv-h200-spot` · `comfyume-vca-ftv-h200-on-demand`
- `comfyume-vca-ftv-b300-spot` · `comfyume-vca-ftv-b300-on-demand`
- Each defines: startup command, GPU type, scaling, SFS mount, env vars, healthcheck

**NOT managed by provider:** SFS (shared filesystem) — Verda console/API only.

**Setup (first time):**
```bash
export VERDA_CLIENT_ID="..." VERDA_CLIENT_SECRET="..."  # from Verda console > API Keys
cd infrastructure
cp terraform.tfvars.example terraform.tfvars  # fill in sfs_volume_id, hf_token
tofu init  # downloads provider
```

**Making deployment changes:**
```bash
cd infrastructure
# 1. Edit .tf file (e.g. change startup command, scaling, GPU type)
# 2. Preview — ALWAYS before apply
tofu plan
# 3. Review output with user, then apply
tofu apply
# 4. Commit .tf changes via git flow (branch → PR → merge)
```

**Debugging / drift detection:**
```bash
cd infrastructure
export VERDA_CLIENT_ID="..." VERDA_CLIENT_SECRET="..."
tofu plan                    # shows ALL differences between .tf and live
tofu state list              # what's managed
tofu state show 'verda_container.worker["h200-spot"]'  # full details of one deployment
```
If `tofu plan` shows unexpected changes → something was modified outside of IaC (console, SDK, ad-hoc script). The plan diff tells you exactly what changed.

**Rules:**
- NEVER use Verda SDK/console to modify deployments — always through `.tf` files
- `tofu plan` before every `tofu apply` — review output, confirm with user
- State file is sensitive (contains secrets) — NEVER commit to git
- All `.tf` changes go through normal git flow (branch → PR → merge)
- First test changes on TESTING server, not production

**Production Safety — State File Isolation:**

| Machine | `.tfstate` exists? | What it knows about |
|---|---|---|
| **Mello** (dev) | YES — 4 production deployments imported | `comfyume-vca-ftv-h200-spot`, `h200-on-demand`, `b300-spot`, `b300-on-demand` |
| **Testing-009** | NO — completely clean | Nothing. Only `.terraform.lock.hcl` (provider version list) |

Why `tofu plan` on testing-009 is safe:
1. **No state = no knowledge of production.** OpenTofu only manages resources in its state file. No state → no existing resources → cannot modify, destroy, or interfere with production.
2. **`tofu plan` is read-only.** Only shows what would happen. `tofu apply` would only CREATE new resources.
3. **Different deployment names.** With `environment = "test"`, names are `comfyume-test-vca-ftv-*` — distinct from production's `comfyume-vca-ftv-*`.
4. **State is local, not shared.** Each machine's state is independent. Mello's and testing-009's states never interact.

---

## Critical ComfyUI Info

### ComfyUI v0.11.0 Workflow Storage

**Workflow Location:**
- Workflows MUST be in: `/comfyui/user/default/workflows/`
- Served via ComfyUI's userdata API: `/api/userdata?dir=workflows`

**How It Works:**
- docker-entrypoint.sh copies workflows from `/workflows` volume to `/comfyui/user/default/workflows/`
- Runs on every container startup
- All 5 template workflows appear in Load menu automatically

**Symptoms if wrong:**
- Workflows folder empty in ComfyUI Load menu
- Browser console errors: `404 /api/userdata?dir=workflows`

### ComfyUI Resources

- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Wiki](https://comfyui-wiki.com/)
- [ComfyUI API Docs](https://github.com/comfyanonymous/ComfyUI/discussions/2073)

---

## Architecture Overview

### Environments

| Environment | Domain | Verda Instance | SFS | SSL | Lifecycle |
|---|---|---|---|---|---|
| **Production** | aiworkshop.art | quiet-city (persistent) | SFS-prod | Let's Encrypt (exp 2026-05-12) | persistent |
| **Staging** | staging.aiworkshop.art | ephemeral | SFS-clone | Let's Encrypt | spin up/tear down |
| **Testing** | testing.aiworkshop.art | ephemeral | SFS-clone | Let's Encrypt | spin up/tear down |

| Machine | Role | Notes |
|---|---|---|
| **Mello** (comfy.ahelme.net) | Dev machine, user dir, Tailscale node | NO containers — dev dirs + scripts only |
| **Verda Serverless** | GPU inference | H200/B300, INFERENCE_MODE=serverless |

**DO NOT DELETE production Verda instance without migrating aiworkshop.art first!**

**DISASTER RECOVERY:** PROD_OS volume was backed up 2026-02-16 to `BACKUP_2026-02-16-PROD_OS-hiq7F8JM` (block-vol 009, FIN-01, 100GB). Full OS snapshot of quiet-city production instance.

```
  Verda (per environment — same architecture, different instance)
  ┌─────────────────────────────────────────┐
  │  Nginx (HTTPS, SSL) · Redis (job queue) │
  │  Queue Manager (FastAPI) · Admin        │
  │  User Frontends x20 (UI only)           │
  └──────────────┬──────────────────────────┘
                 │ HTTP (serverless)
  ┌──────────────▼──────────────────────────┐
  │  Verda Serverless Containers             │
  │  H200 141GB / B300 288GB (spot/demand)  │
  │  !LOAD-BALANCED — no direct HTTP back   │
  │  Images → SFS → QM copies to /outputs/  │
  └─────────────────────────────────────────┘

Code Architecture:

[User Browser]
    ↓ HTTPS
[Nginx :443] → SSL termination, routing
    ├─→ /user001-020/ → Frontend containers
    ├─→ /api → Queue Manager
    └─→ /admin → Admin Dashboard

[Queue Manager :3000] ← FastAPI + WebSocket
    ↓ Redis
[Job Queue] ← Redis list + pub/sub
    ↓
[ComfyUI Workers :8188-8190] ← GPU processing (serverless, load-balanced)
    ↓ writes to SFS (NOT HTTP back!)
[SFS /mnt/sfs/] ← models (read), outputs (write, 1777 perms)
```

---

## Dev Teams & Progress

Four teams (or more) work on this project:

| Team | AKA | Testing Dir | Resume | Handover | Progress |
|------|-----|-------------|--------|----------|----------|
| Mello Team One | mello-team-one | `/home/dev/projects/testing-mello-team-one` | [resume](.claude/skills/resume-context-mello-team-one/SKILL.md) | [handover](.claude/skills/handover-mello-team-one/SKILL.md) | [log](.claude/agent_docs/progress-mello-team-one-dev.md) |
| Verda Team One | verda-team-one | — | [resume](.claude/skills/resume-context-verda-team-one/SKILL.md) | [handover](.claude/skills/handover-verda-team-one/SKILL.md) | [log](.claude/agent_docs/progress-verda-team-one-dev.md) |
| Mello Admin Panel Team | mello-admin-panel-team | `/home/dev/projects/testing-mello-admin-panel-team` | [resume](.claude/skills/resume-context-mello-admin-panel-team/SKILL.md) | [handover](.claude/skills/handover-mello-admin-panel-team/SKILL.md) | [log](.claude/agent_docs/progress-mello-admin-panel-team-dev.md) |
| Mello Scripts Team | mello-scripts-team | `/home/dev/projects/testing-mello-scripts-team` | [resume](.claude/skills/resume-context-mello-scripts-team/SKILL.md) | [handover](.claude/skills/handover-mello-scripts-team/SKILL.md) | [log](.claude/agent_docs/progress-mello-scripts-team-dev.md) |
| Mello Ralph Team | mello-ralph-team | `/home/dev/projects/testing-mello-ralph-team` | [resume](.claude/skills/resume-context-mello-ralph-team/SKILL.md) | [handover](.claude/skills/handover-mello-ralph-team/SKILL.md) | [log](.claude/agent_docs/progress-mello-ralph-team-dev.md) |

**Central Log:** [.claude/agent_docs/progress-all-teams.md](.claude/agent_docs/progress-all-teams.md) -- 1-line-per-commit across all teams
**Update command:** `/update-progress``

### Dev Directories (Mello — separate clones)

| Directory | Repo | Branch | Team |
|---|---|---|---|
| `testing-mello-team-one` | comfyume-v1 | `testing-mello-team-one` | Main dev team |
| `testing-mello-admin-panel-team` | comfyume-v1 | `testing-mello-admin-panel-team` | Admin panel team |
| `testing-mello-scripts-team` | comfymulti-scripts | `testing-mello-scripts-team` | Scripts team |
| `staging-main` | comfyume-v1 | `staging` | All teams merge here |
| `staging-scripts` | comfymulti-scripts | `staging` | All teams merge here |
| `production-main` | comfyume-v1 | `main` | Production code |
| `production-scripts` | comfymulti-scripts | `main` | Proven scripts ONLY |

### Session Checklist

Before each session ends:
- [ ] Commit & push code changes to git
- [ ] Update progress files (`.claude/agent_docs/progress-*.md`)
- [ ] Update admin/dev docs with key changes made
- [ ] Update current implementation plan when plan changes
- [ ] Consider any user-facing doc changes
- [ ] Note any blockers or decisions
- [ ] Clear next session goals

---

## Repository

- **Platform:** GitHub
- **URL:** https://github.com/ahelme/comfyume-v1
- **Branch Strategy:**
  - `main` — production-ready code (maps to `production-main/`)
  - `staging` — validated, pre-production (maps to `staging-main/`)
  - Team branches — active development (e.g. `testing-mello-team-one`, `testing-mello-admin-panel-team`)
  - Feature branches — branched off team branches (e.g. `testing-mello-team-one-gpu-overlay`)
  - **NEVER push directly to main** -- ALWAYS use team branches or feature branches + PRs (BOTH repos!)
- **Scripts Repo** (PRIVATE!): `https://github.com/ahelme/comfymulti-scripts`

### Commits

Use conventional commit format. No boasting.
```
feat: add queue manager REST API endpoints
fix: resolve nginx routing for user/20
docs: update admin guide with priority override
test: add integration tests for worker
```

**When to commit:** end of major feature · before risky changes · end of session · when tests pass
**After commits:** always run `/update-progress`

### Task & Issue Management

- **ALWAYS reference GitHub issue numbers** (e.g., #15, #22, #13)
- **DO NOT use internal task numbers** (no Task #1, Task #2, etc.)
- **If no GitHub issue exists**, create one first before tracking work

| Tracker | URL |
|---|---|
| comfyume-v1 (active) | https://github.com/ahelme/comfyume-v1/issues |
| comfyume (original) | https://github.com/ahelme/comfyume/issues |
| comfymulti-scripts (private) | https://github.com/ahelme/comfymulti-scripts/issues |

**gh CLI gotcha:** `gh issue view` fails with "Projects (classic) deprecated" error. Use `--json` flag: `gh issue view 8 --json title,body,state`

See [project_management.md](.claude/agent_docs/project_management.md) for extended details.

### CRITICAL: Handling .env

User will request a fresh copy of `.env` from private scripts repo when needed, and ask to update it there when needed. Follow user's requests — do not copy or update autonomously.

---

## Critical Files and Locations

### Verda (production app server)

| File/Directory | Purpose |
|---|---|
| `.env` | Configuration (passwords, domain, etc.) |
| `docker-compose.yml` | Container orchestration |
| `docker-compose.users.yml` | 20 user containers (auto-generated) |
| `/etc/ssl/certs/fullchain.pem` | SSL public certificate |
| `/etc/ssl/private/privkey.pem` | SSL private key |
| `scripts/start.sh` | Start all services |
| `scripts/stop.sh` | Stop all services |
| `scripts/status.sh` | System health check |
| `scripts/generate-user-compose.sh` | Regenerates docker-compose.users.yml |

### Storage Per Environment

| Storage | Purpose | Shared by |
|---|---|---|
| **`PROD_OS-<string>`** | BlockStorage (OS) Prod. Instance operating system & app containers | Production only |
| **`TEST_OS-<string>`** | Blockstorage (OS) Testing Instance operating system & app containers | Testing only |
| **`STAG_OS-<string>`** | Blockstorage (OS) Staging Instance operating system & app containers | Staging only |
| **`PROD_SFS-Model-Vault-<date-created-<string>`** | Live models, stable, trusted | Production only |
| **`CLONE_SFS-Model-Vault-<date-created>-<string>`** | Cloned from prod — safe to experiment, doubles as backup | Testing + staging |
| **`PROD_Block-Storage-Scratch-Disk-Volume-<string>`** | Ephemeral: user outputs, inputs | One per instance |
| **`CLONE_Block-Storage-Scratch-DiskVolume-<string>`** | Cloned from prod - safe to experiment, doubles as backup | Testing + Staging |
| **Serverless Containers - Workers** | Various options e.g. H200, B300 available with replicas | Production, staging, testing |

### Mello (dev machine + user dir)

| File/Directory | Purpose |
|---|---|
| `~/projects/comfyume-v1/` | Dev directories (see Deployment Workflow above) |
| `~/comfymulti-scripts/` | Backup/Restore/Deploy scripts (private repo) |
| `~/comfymulti-scripts/restore-verda-instance.sh` | Instance restore (v0.4.2) |

*(Private repo: https://github.com/ahelme/comfymulti-scripts)*

See [project_structure.md](.claude/agent_docs/project_structure.md) for full file trees.

---

## Verda

NOTE: Spot instances are used for affordability but can be terminated anytime -- always use persistent storage (SFS or Block).

### Deployment Targets

- [Verda Products](https://verda.com/products) - Instance types
- [Verda Containers](https://verda.com/serverless-containers) - Serverless options, dynamic scaling
- [Verda Instances](https://docs.verda.com/cpu-and-gpu-instances/set-up-a-gpu-instance) - Setup an instance
- [Verda Serverless Containers](https://docs.verda.com/containers/overview) - Setup a container

### Resource Naming Convention

All Verda resources (instances, block volumes, SFS) use environment prefixes in their **console names**:

| Prefix | Environment | Example |
|--------|-------------|---------|
| `PROD_*` | Production | `PROD_OS-hiq7F8JM`, `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi` |
| `CLONE_*` | Cloned from prod (testing + staging shared) | `CLONE_SFS-Model-Vault-16-Feb-97Es5EBC` |
| `STAG_*` | Staging-only | `STAG_OS-...`, `STAG_Scratch-Disk-...` |
| `TEST_*` | Testing-only | `TEST_OS-...`, `TEST_Scratch-Disk-...` |
| `UNUSED_*` | Old/orphaned, pending deletion | `UNUSED_OLD-GPU-INSTANCE-OS-5qsQtVzV` |

Volume type suffixes (after the prefix):
- `OS-*` = OS disks (Ubuntu installed)
- `Scratch-Disk-*` or `Block-Storage-*` = Data volumes (ephemeral user data)
- `SFS-*` = Shared filesystem (models, outputs)

### After Provisioning

- Run `apt update && apt upgrade -y` before anything else (required for SFS/NFS connectivity)
- Verda images have Docker pre-installed (don't try to install docker.io -- conflicts with containerd)
- Ubuntu 24.04 uses `ssh` service name, not `sshd`

### SSH Keys for Verda

**During Verda provisioning, add BOTH public keys via Verda console:**

1. **User's Mac key** -- for manual SSH access
2. **Mello VPS key** -- for mello to SSH into Verda

```
# Mello VPS public key (MUST ADD):
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGiwaT6NQcHe7cYDKB5LrtmyIU0O8iRc7DJUmZJsNkDD aeon@vps-for-verda
```

**Why this matters for restore scripts:**
- Mac can SSH into Verda (Mac has private key)
- Mello can SSH into Verda (Mello has private key)
- Verda CANNOT pull from mello (Verda has no private key for mello until setup script finishes)

### Verda SSH Identities (per-environment, scripts #55)

Separate keys per environment so Tailscale assigns distinct IPs and Mello can identify which instance is calling. Without this, whichever instance connects first claims the Tailscale IP, locking out the others.

**Keys:** `comfymulti-scripts/secrets/ssh/verda_{production,testing,staging}_ed25519(.pub)`
**Restore scripts:** comment-out block — uncomment the key matching the target environment.
**Mello:** all three public keys in `authorized_keys`.
**Variable:** `VERDA_INSTANCE_SSH_PRIVATE_KEY` (old name was `VERDA_SSH_PRIVATE_KEY`).

### Verda Restore Scripts Are Adaptive

**Core Restore Workflow:** Restore scripts first check SFS (fast), then fall back to remote:
- **SFS** -- First choice (files cached from previous session)
- **R2** -- Binary files (models, container image, config tarball)
- **GitHub** -- Scripts (`ahelme/comfymulti-scripts` private repo)

See [storage.md](.claude/agent_docs/storage.md) for SFS and block storage details.

---

## Backup and Restore

### Critical Principles

**Check Before Downloading/Restoring (Scripts Check in This Order)**

| File Type | Check Order | Rationale |
|-----------|-------------|-----------|
| **Models** (~45GB) | SFS -> R2 | Large, live on SFS |
| **Config, identity, container** | /root/ -> SFS -> R2 | Extracted to instance |
| **Scripts** | /root/ -> SFS -> GitHub | Small, versioned |

**Tailscale Identity Must Be Restored BEFORE Starting Tailscale**

If Tailscale starts without the backed-up identity, it gets a **NEW IP address**.
The restore scripts restore `/var/lib/tailscale/` BEFORE running `tailscale up`.
This preserves the expected IP: **100.89.38.43**

---

## Deployment Workflow

**Promotion:** testing → staging → production · code only moves forward · never backwards

**Deploy method:** blue-green via DNS switch (TTL 60s — leave permanently)

### Blue-Green Deploy

1. Build & validate on staging instance (staging.aiworkshop.art)
2. Final check: optionally mount SFS-prod on staging to verify with real models
3. Switch DNS: `aiworkshop.art` A record → staging instance IP
4. Old production stays alive as rollback
5. Once confident → tear down old instance, staging becomes new production

### Deployment Prerequisites Checklist

Before deploying a new staging/testing instance, verify:

**Infrastructure:**
- [ ] **Production instance is running** (quiet-city, 65.108.33.101) — models come from PROD_SFS first
- [ ] **PROD_SFS** (`PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`) is healthy — this is the primary model source (~192GB, 28 models). New instances mount this via NFS and copy models locally. SFS must be shared with the new instance via Verda console "share settings".
- [ ] **CLONE_SFS** (`CLONE_SFS-Model-Vault-16-Feb-97Es5EBC`) available as backup/testing model source
- [ ] mello VPS is running (dev machine + user dir — comfy.ahelme.net)

**Fallback (only if PROD_SFS unavailable/deleted):**
- [ ] R2: **Models bucket** (`comfyume-model-vault-backups`) contains:
  - [ ] `checkpoints/*.safetensors` (~25-50 GB)
  - [ ] `text_encoders/*.safetensors` (~20 GB)

**Always required:**
- [ ] R2: **Cache bucket** (`comfyume-cache-backups`) contains:
  - [ ] `worker-image.tar.gz` (~2.5 GB)
  - [ ] `verda-config-backup.tar.gz` (~14 MB)
- [ ] R2: **Worker container bucket** (`comfyume-worker-container-backups`)
- [ ] R2: **User files bucket** (`comfyume-user-files-backups`) — available to receive backups
- [ ] GitHub: **Private Scripts Repo** (`ahelme/comfymulti-scripts`) contains:
  - [ ] `restore-verda-instance.sh`
- [ ] User's Mac: **SSH Keys and Setup Script** added to Verda console during provisioning
  - [ ] `dev@vps-for-verda` (Mello's key) & `developer@annahelme.com` (User's key)
  - [ ] `restore-verda-instance.sh` (latest version from GitHub!)

### Step-by-Step Deployment Process

See [Admin Backup & Restore Guide](./docs/admin-backup-restore.md) for complete step-by-step instructions including:
- Provisioning SFS and GPU instance and block storage (scratch disk) on Verda
- Running restore-verda-instance.sh on Verda (runs automatically on first boot)
- Script mounts PROD_SFS for models first (fast, NFS), falls back to R2 download only if SFS unavailable
- Backup cron jobs are set up automatically by the script

### Batched App Container Startup Architecture

**Dependency Chain:**
1. Queue Manager must be healthy FIRST
2. Then 4 batch leaders start in parallel: user001, user006, user011, user016 (each depends on queue-manager)
3. Within each batch: sequential with health checks (user002 depends on user001, etc.)
4. Total time: ~1-2 minutes for 5 users, ~2-3 minutes estimated for 20 users

**Commands (Verda - App Server):**
- Start: `docker compose up -d` (includes docker-compose.users.yml automatically)
- Set auto-restart: `docker update --restart=unless-stopped $(docker ps -q --filter "name=comfy")` (survives reboots)
- Regenerate: `./scripts/generate-user-compose.sh` (updates docker-compose.users.yml)

**Commands (Verda - Worker):**
- Start worker: `cd ~/comfyume/comfyui-worker/ && sudo docker compose up -d worker-1`
- Check logs: `sudo docker logs comfy-worker-1 -f` (container name, not image name)
- Set auto-restart: `sudo docker update --restart=unless-stopped $(sudo docker ps -q --filter "name=comfy")` (survives reboots)
- Check Redis: `redis-cli -h 100.99.216.71 -p 6379 -a $REDIS_PASSWORD ping`

### Troubleshooting

See [Admin Backup & Restore Guide - Troubleshooting](./docs/admin-backup-restore.md#troubleshooting) for common issues and solutions.

---

## CRITICAL GOTCHAS

### CRITICAL: Worker Container Infinite Restart Loop

**Symptom:** Worker container restarts every 30 seconds with "ComfyUI failed to start" error.

**Root Cause:** Original startup script uses `curl` for health checks, but `curl` not installed in worker container. Health check always fails -> script exits -> container restarts.

**Fix:** Remove curl-based health check, use simple sleep:
`bash
#!/bin/bash
echo "Starting ComfyUI Worker: $WORKER_ID"
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 &
COMFYUI_PID=$!
sleep 60  # Simple wait instead of curl check
cd /workspace
python3 worker.py
kill $COMFYUI_PID 2>/dev/null || true
`

**To apply fix on running container:**
`bash
cat > /tmp/start-simple.sh << 'EOF'
#!/bin/bash
echo "Starting ComfyUI Worker: $WORKER_ID"
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 &
sleep 60
cd /workspace && python3 worker.py
EOF
chmod +x /tmp/start-simple.sh
docker stop comfy-worker-1
docker cp /tmp/start-simple.sh comfy-worker-1:/workspace/start-worker.sh
docker start comfy-worker-1
`

**Success indicators:** Worker logs show "Worker worker-1 started", polling queue manager every 2s, HTTP 200 OK responses.

### CRITICAL: Disk Space Monitoring

Run `disk-check.sh` before builds/backups. Use `--block` to abort if >90% full. Auto-runs (blocking) in: start.sh, build.sh, backup scripts, restore-verda-instance.sh.

`bash
df -h /tmp /mnt/sfs  # quick manual check before any large operation
`

### CRITICAL: Server Unresponsive Emergency Fix

**If server stops responding (20x user containers overwhelm resources):**
1. Hard Reset the server via hosting provider dashboard
2. SSH in ASAP after reboot
3. Run: `sudo docker stop $(sudo docker ps -q --filter "name=comfy")`

This stops all ComfyUI containers to prevent resource exhaustion on startup.

### CRITICAL: Attaching Block Storage

Block storage gets **WIPED** if attached during instance provisioning!

Safe workflow:
1. Create instance **WITHOUT** block storage attached
2. Boot the instance
3. **Shut down** the instance (required for attachment)
4. Attach block storage via Verda Dashboard
5. Boot instance again
6. Mount the volume: `mount /dev/vdc /mnt/models`

### CRITICAL: Object Storage Is Append-Only

**NEVER delete backups from R2 or Hetzner Object Storage.** Only add new dated files alongside existing ones. Old backups stay untouched indefinitely. This applies to all buckets (models, user-files, worker-container, cache).

### CRITICAL: R2 .eu Domain

Cloudflare R2 buckets require `.eu` in the middle of the endpoint URL. Omitting it causes silent connection failures -- uploads/downloads fail with no clear error message. Always use the full endpoint:
`
https://f1d627b48ef7a4f687d6ac469c8f1dea.r2.cloudflarestorage.com.eu
`
Note: `.eu` appears between `cloudflarestorage.com` and the path, not as a suffix.

### CRITICAL: Docker Image Architecture

**Single Shared Image for All Users:**
- All 20 users use `comfyume-frontend:v0.11.0` (NOT per-user images)
- `docker-compose.users.yml` uses `image:` not `build:` (regenerated by `scripts/generate-user-compose.sh`)

**Custom Nodes Volume Mount Gotcha:**
- Custom nodes volume-mounted per user: `./data/user_data/userXXX/comfyui/custom_nodes:/comfyui/custom_nodes`
- **Volume mount OVERWRITES image contents!** Empty host directory = empty container directory
- **Solution:** Copy default custom nodes from `comfyui-frontend/custom_nodes/` to each user's directory
- Required nodes: `default_workflow_loader` (Flux2 Klein auto-load), `queue_redirect` (job submission)

---

### CRITICAL: Serverless Inference — No Direct HTTP Back to Containers

HTTP image download doesn't work with serverless load balancing. Verda routes each HTTP request to a **different container instance**. So `GET /view?filename=...` returns 404 because it hits a different instance than the one that generated the image. The fix was pivoting to **SFS-based delivery** — images written to shared NFS, QM copies from SFS to local `/outputs/userXXX/`, frontend serves locally.

**Key principle:** Serverless containers are ephemeral and load-balanced — you cant talk back to a specific instance. All persistent data must go through shared storage (SFS).

**Related fixes from Ralph Loop (PRs #23-#28):**
1. **QM must poll + fetch results** — `submit_to_serverless()` (`queue-manager/main.py:314`) must call `poll_serverless_history()` (`:174`) after POST `/prompt`, not fire-and-forget. SFS copy at `:279`.
2. **SFS directory permissions** — `/mnt/sfs/outputs` needs `chmod 1777` (sticky + world-writable). ComfyUI runs as uid 1000 inside containers, not root. (Server-side fix, not in git.)
3. **`--output-directory` flag required** — without it, ComfyUI saves to container-local `/workspace/ComfyUI/output/` (ephemeral, lost on scale-down). Must pass `--output-directory /mnt/sfs/outputs` in container start command via Verda SDK. (Server-side fix, not in git.)

### CRITICAL: Verda Rebrand (ex. DataCrunch)

Verda was previously called `DataCrunch`. ALL docs, code comments, specs, and API references must say **Verda**, not DataCrunch. API endpoint URLs may still use `containers.datacrunch.io` — verify current domain before updating URLs. When writing new docs, always use "Verda". First mention in standalone docs: "Verda (ex. DataCrunch)".

### OTHER GOTCHAS

See [gotchas.md](.claude/agent_docs/gotchas.md) for full details:

- **Issue #54:** Workflow Save/Load nginx proxy_pass fix
- **Health Checks:** Dependencies required in Dockerfile (curl, libgomp1, requests)
- **Silent Failures:** Large file operations report success while failing

---

## Documentation

### Documentation Format

All .md files must have this header:

`
**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art · staging.aiworkshop.art · testing.aiworkshop.art
**Doc Created:** [date]
**Doc Updated:** [date]
`

Docs MUST be comprehensive yet NO FLUFF. No boasting.

### Core Documents

- [README.md](./README.md) - Public project overview and dev quickstart
- Progress Logs -- see Dev Teams table above
- Agent Docs -- see `.claude/agent_docs/`

### User Documentation

- **docs/archive/user-guide.md** - For workshop participants (may need update)
- **docs/admin-guide.md** - For developer/maintainer/instructor
- **docs/archive/troubleshooting.md** - Common issues

---

## User Preferences

- Appreciates thoroughness and detail
- Values comprehensive and accurate documentation
- Wants progress tracking (hence progress files)
- Likes structured approaches
- Fix at the source, not quick hacks on the server
- Option-based config with clear comments over complex mechanisms
- Hates BOASTING in DOCS, COMMITS, GH ISSUES, GH COMMENTS
- Express pride in chat, NOT in docs/GitHub
- **NEVER push directly to main** -- ALWAYS use testing/staging/production and team/feature branches, e.g. `testing-mello-team-one`, `testing-mello-team-one-gpu-overlay`, `staging` + PRs (BOTH repos!)

---

## Agent Docs (Progressive Disclosure)

Read these when their trigger matches your task. TL;DR uses: `·` sep `@` location `!` danger `:` port `→` consequence
**Maintenance:** When updating an agent_doc, also update its TL;DR here — it's a second source of truth.

| File | Read when... | TL;DR |
|------|-------------|-------|
| [models_and_data.md](.claude/agent_docs/models_and_data.md) | models, templates, downloads | Flux+LTX-2 · 22 models 172GB@/mnt/sfs · yaml key = folder type verbatim |
| [project_structure.md](.claude/agent_docs/project_structure.md) | finding files, dir layout | data/user_data/userXXX/ · .users.yml auto-gen · scripts/ admin/ nginx/ qm/ |
| [project_management.md](.claude/agent_docs/project_management.md) | commits, issues, PRs | conventional commits · ref GH# always · `gh issue` needs --json |
| [security.md](.claude/agent_docs/security.md) | auth, firewall, VPN, SSL, R2 | Redis Tailscale-only:6379 · bcrypt auth · SSL exp 2026-05-12 · !R2 needs .eu |
| [infrastructure.md](.claude/agent_docs/infrastructure.md) | servers, Docker, services | 3-tier Verda (prod·staging·testing) · Mello=dev+user-dir · 20 frontends+qm+redis+nginx+admin · serverless H200/B300 · resource naming: PROD_ STAG_ TEST_ UNUSED_ |
| [infrastructure-registry.md](https://github.com/ahelme/comfymulti-scripts/blob/main/infrastructure-registry.md) | IPs, instance names, SFS IDs, secrets refs | PRIVATE scripts repo · actual resource IDs · update when provisioning |
| [monitoring.md](.claude/agent_docs/monitoring.md) | health, logs, dashboards | Prom:9090 Graf:3001 Loki:3100 cAdv:8081 · 12 /verda-* skills |
| [storage.md](.claude/agent_docs/storage.md) | SFS, block storage, mounts | SFS=shared NFS@/mnt/sfs · /outputs/ needs 1777 perms · block=single-instance · !WIPED if attached@provisioning |
| [backups.md](.claude/agent_docs/backups.md) | backup, restore, R2, retention | !append-only · 4 R2 buckets · SFS→R2 fallback · dated naming · rotation: 5d/3w/3m · scripts need updating |
| [backups-log.md](https://github.com/ahelme/comfymulti-scripts/blob/main/backups-log.md) | verify R2 contents, audit trail | PRIVATE scripts repo · VERIFIED contents only · append-only · new entries at top |
| [gotchas.md](.claude/agent_docs/gotchas.md) | unexpected failures, debugging | !SFS console rename→pseudopath change on reboot · !SFS needs share settings per instance · nginx decodes %2F→#54 · Dockerfile needs curl+libgomp1+requests · large ops fail silent · !Verda ex.DataCrunch rebrand |
| [external-references.md](.claude/agent_docs/external-references.md) | architecture research | Visionatrix · SaladTech · Modal · 9elements — multi-user patterns |

---

**Last Updated:** 2026-02-15 -- Added 3-tier deployment workflow (testing/staging/production), SFS-clone, blue-green deploy
