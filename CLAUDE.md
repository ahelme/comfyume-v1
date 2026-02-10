**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**CURRENT Project Repository:** https://github.com/ahelme/comfyume-v1
**OLDER Project Repository:** https://github.com/ahelme/comfyume
**NOTE:** The older repo is more advanced, but is broken. This repo will revert to a stable state (by rsync from older OS drive) then we will cherry pick from the advanced yet broken older repo.
**Domain:** aiworkshop.art (PRODUCTION) + comfy.ahelme.net (staging)
**Doc Updated:** 2026-02-10

---

## What We're Building

A multi-user ComfyUI platform for video generation workshops for professional filmmakers.
- CPU app hosting on Verda (aiworkshop.art) -- nginx, Redis, queue-manager, 20 user frontends
- Serverless GPU inference on DataCrunch (H200/B300) -- scales on demand, pay per use
- Models and backups on Cloudflare R2 (.eu, cheap)

### Key Requirements

- Split architecture: CPU app server (Verda) + serverless GPU workers (DataCrunch H200/B300)
- 20 isolated ComfyUI web interfaces
- Central job queue (FIFO/round-robin/priority)
- Serverless GPU workers scaling on demand
- HTTPS with aiworkshop.art domain (SSL cert via Namecheap)
- HTTP Basic Auth password protection
- Tailscale VPN for secure Redis connection
- Persistent user storage
- Admin dashboard for instructor
- Grafana, Prometheus, Loki, Dry for monitoring
- FUTURE: ComfyGit (formerly ComfyDock)

### Quick Links

- **Production:** https://aiworkshop.art/
- **Health Check:** https://aiworkshop.art/health
- **Admin Dashboard:** https://aiworkshop.art/admin
- **API:** https://aiworkshop.art/api/queue/status

---

## Critical Instructions

1. **BELIEVE THE USER** -- When the user reports something isn't working, investigate. Don't dismiss with "try cache refresh".
2. **USE LATEST STABLE LIBRARIES** as of Jan 2026.
3. **CHECK FOR EXISTING CODE FIRST** -- NEVER rewrite code that already exists. ALWAYS check for previous solutions.

---

## Architecture Overview

| Server | Domain | Role | Status |
|--------|--------|------|--------|
| **VERDA** | aiworkshop.art | **PRODUCTION** | nginx, queue-manager, Redis -> serverless |
| MELLO | comfy.ahelme.net | Staging/backup only | Containers removed (#71), backup scripts, Tailscale node |

**DO NOT DELETE VERDA without migrating aiworkshop.art back to Mello first!**

```
  Current Architecture:
  ┌─────────────────────────────────────────┐
  │ Verda CPU Instance (aiworkshop.art)     │
  │  - Nginx (HTTPS, SSL)                   │
  │  - Redis (job queue)                    │
  │  - Queue Manager (FastAPI)              │
  │  - Admin Dashboard                      │
  │  - User Frontends x20 (UI only)         │
  └──────────────┬──────────────────────────┘
                 │ HTTP (serverless)
  ┌──────────────▼──────────────────────────┐
  │  Verda/DataCrunch Serverless Containers │
  │  - H200 141GB (spot / on-demand)        │
  │  - B300 288GB (spot / on-demand)        │
  │  INFERENCE_MODE=serverless              │
  └─────────────────────────────────────────┘

  Mello (comfy.ahelme.net) — staging/backup only
  ┌─────────────────────────────────────────┐
  │  - Tailscale node (100.99.216.71)       │
  │  - Backup scripts (comfymulti-scripts)  │
  │  - Git repos, SSH                       │
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
[ComfyUI Workers :8188-8190] ← GPU processing (serverless)
    ↓
[Shared Volumes] ← models, outputs, workflows
```

---

## Dev Teams & Progress

Four teams work on this project. Coordination via GitHub Issue #7 -- check like email before proceeding with conflicting work.
Master task list: Issue #1.

| Team | AKA | Resume | Handover | Progress |
|------|-----|--------|----------|----------|
| Mello Team One | mello-team-one | [resume](.claude/skills/resume-context-mello-team-one/SKILL.md) | [handover](.claude/skills/handover-mello-team-one/SKILL.md) | [log](.claude/agent_docs/progress-mello-team-one-dev.md) |
| Verda Team One | verda-team-one | [resume](.claude/skills/resume-context-verda-team-one/SKILL.md) | [handover](.claude/skills/handover-verda-team-one/SKILL.md) | [log](.claude/agent_docs/progress-verda-team-one-dev.md) |
| Mello Admin Panel Team | admin-panel-team | [resume](.claude/skills/resume-context-admin-panel-team/SKILL.md) | [handover](.claude/skills/handover-admin-panel-team/SKILL.md) | [log](.claude/agent_docs/progress-admin-panel-team-dev.md) |
| Mello Testing Scripts Team | testing-scripts-team | [resume](.claude/skills/resume-context-testing-scripts-team/SKILL.md) | [handover](.claude/skills/handover-testing-scripts-team/SKILL.md) | [log](.claude/agent_docs/progress-testing-scripts-dev.md) |

**Central Log:** [.claude/agent_docs/progress-all-teams.md](.claude/agent_docs/progress-all-teams.md) -- 1-line-per-commit across all teams
**Update command:** `/update-progress`

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
  - `main` - production-ready code
  - Feature branches as needed
  - **NEVER push directly to main** -- ALWAYS use feature branches + PRs for BOTH repos!
- **Scripts Repo** (PRIVATE!): https://github.com/ahelme/comfymulti-scripts

See [project_management.md](.claude/agent_docs/project_management.md) for commit conventions and issue tracking.

---

## Documentation Format

All .md files must have this header:

```
**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** [date]
**Doc Updated:** [date]
```

Docs MUST be comprehensive yet NO FLUFF. No boasting.

---

## Core Documents

- [README.md](./README.md) - Public project overview and dev quickstart
- Progress Logs -- see Dev Teams table above

### User Documentation

- **docs/archive/user-guide.md** - For workshop participants (may need update)
- **docs/admin-guide.md** - For developer/maintainer/instructor
- **docs/archive/troubleshooting.md** - Common issues

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

### Verda Storage

| Storage | Purpose |
|---|---|
| BlockStorage (OS) | Instance operating system & worker |
| BlockStorage (scratch) | Ephemeral: user inputs/outputs |
| SFS (network drive) | Persistent: models, cache, backups |

### Mello (staging/backup)

| File/Directory | Purpose |
|---|---|
| `~/comfymulti-scripts/` | Backup/Restore/Deploy scripts (private repo) |
| `~/comfymulti-scripts/restore-verda-instance.sh` | Production app server restore (v0.4.2) |
| `~/comfymulti-scripts/README-RESTORE.md` | README for restoring Verda |

*(Private repo: https://github.com/ahelme/comfymulti-scripts)*

See [project_structure.md](.claude/agent_docs/project_structure.md) for full file trees.

---

## Core ComfyUI Docs

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

## Batched Startup Architecture

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

---

## CRITICAL GOTCHAS

### CRITICAL: Worker Container Infinite Restart Loop

**Symptom:** Worker container restarts every 30 seconds with "ComfyUI failed to start" error.

**Root Cause:** Original startup script uses `curl` for health checks, but `curl` not installed in worker container. Health check always fails -> script exits -> container restarts.

**Fix:** Remove curl-based health check, use simple sleep:
```bash
#!/bin/bash
echo "Starting ComfyUI Worker: $WORKER_ID"
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 &
COMFYUI_PID=$!
sleep 60  # Simple wait instead of curl check
cd /workspace
python3 worker.py
kill $COMFYUI_PID 2>/dev/null || true
```

**To apply fix on running container:**
```bash
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
```

**Success indicators:** Worker logs show "Worker worker-1 started", polling queue manager every 2s, HTTP 200 OK responses.

### CRITICAL: Disk Space Monitoring

Run `disk-check.sh` before builds/backups. Use `--block` to abort if >90% full. Auto-runs (blocking) in: start.sh, build.sh, backup scripts, restore-verda-instance.sh.

```bash
df -h /tmp /mnt/sfs  # quick manual check before any large operation
```

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

### CRITICAL: R2 .eu Domain

Cloudflare R2 buckets require `.eu` in the middle of the endpoint URL. Omitting it causes silent connection failures -- uploads/downloads fail with no clear error message. Always use the full endpoint:
```
https://f1d627b48ef7a4f687d6ac469c8f1dea.r2.cloudflarestorage.com.eu
```
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

## OTHER GOTCHAS

See [gotchas.md](.claude/agent_docs/gotchas.md) for full details:

- **Issue #54:** Workflow Save/Load nginx proxy_pass fix
- **Health Checks:** Dependencies required in Dockerfile (curl, libgomp1, requests)
- **Silent Failures:** Large file operations report success while failing

---

## Verda

NOTE: Spot instances are used for affordability but can be terminated anytime -- always use persistent storage (SFS or Block).

### Deployment Targets

- [Verda Products](https://verda.com/products) - Instance types
- [Verda Containers](https://verda.com/serverless-containers) - Serverless options, dynamic scaling
- [Verda Instances](https://docs.verda.com/cpu-and-gpu-instances/set-up-a-gpu-instance) - Setup an instance
- [Verda Serverless Containers](https://docs.verda.com/containers/overview) - Setup a container

### Volume Naming Convention

- `OS-*` = OS disks (will have Ubuntu installed)
- `Volume-*` = Data volumes (your actual block storage)

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
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGiwaT6NQcHe7cYDKB5LrtmyIU0O8iRc7DJUmZJsNkDD dev@vps-for-verda
```

**Why this matters for restore scripts:**
- Mac can SSH into Verda (Mac has private key)
- Mello can SSH into Verda (Mello has private key)
- Verda CANNOT pull from mello (Verda has no private key for mello until setup script finishes)

### Restore Scripts Are Adaptive

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

### Deployment Prerequisites Checklist

Before starting, verify:
- [ ] mello VPS is running (staging/backup -- comfy.ahelme.net)
- [ ] R2: **Models bucket** (`comfyume-model-vault-backups`) contains:
  - [ ] `checkpoints/*.safetensors` (~25-50 GB)
  - [ ] `text_encoders/*.safetensors` (~20 GB)
- [ ] R2: **Cache bucket** (`comfyume-cache-backups`) contains:
  - [ ] `worker-image.tar.gz` (~2.5 GB)
  - [ ] `verda-config-backup.tar.gz` (~14 MB)
- [ ] R2: **Worker container bucket** (`comfyume-worker-container-backups`)
- [ ] R2: **User files bucket** (`comfyume-user-files-backups`) -- available to receive backups
- [ ] GitHub: **Private Scripts Repo** (`ahelme/comfymulti-scripts`) contains:
  - [ ] `restore-verda-instance.sh`
- [ ] User's Mac: **SSH Keys and Setup Script** added to Verda console during provisioning
  - [ ] `dev@vps-for-verda` (Mello's key) & `developer@annahelme.com` (User's key)
  - [ ] `restore-verda-instance.sh` (latest version from GitHub!)

### Step-by-Step Deployment Process

See [Admin Backup & Restore Guide](./docs/admin-backup-restore.md) for complete step-by-step instructions including:
- Provisioning SFS and GPU instance and block storage (scratch disk) on Verda
- Running restore-verda-instance.sh on Verda (runs automatically on first boot)
- Script downloads models from R2 (unless available on SFS already)
- Backup cron jobs are set up automatically by the script

### Troubleshooting

See [Admin Backup & Restore Guide - Troubleshooting](./docs/admin-backup-restore.md#troubleshooting) for common issues and solutions.

---

## User Preferences

- Appreciates thoroughness and detail
- Values comprehensive and accurate documentation
- Wants progress tracking (hence progress files)
- Likes structured approaches
- Hates BOASTING in DOCS, COMMITS, GH ISSUES, GH COMMENTS
- Express pride in chat, NOT in docs/GitHub
- **NEVER push directly to main** -- ALWAYS use feature branches + PRs (BOTH repos!)

---

## Agent Docs (Progressive Disclosure)

Read these files when their topic is relevant to your current task:

| File | Contents |
|------|----------|
| [models_and_data.md](.claude/agent_docs/models_and_data.md) | Workshop templates, ML models, LoRAs, model inventory |
| [project_structure.md](.claude/agent_docs/project_structure.md) | File trees, directory layouts (both repos) |
| [project_management.md](.claude/agent_docs/project_management.md) | Git workflow, commit conventions, issue tracking |
| [security.md](.claude/agent_docs/security.md) | Firewall, auth, Tailscale VPN, SSL, R2 buckets |
| [infrastructure.md](.claude/agent_docs/infrastructure.md) | Servers, backups, Docker, services |
| [monitoring.md](.claude/agent_docs/monitoring.md) | Portainer, Prometheus, Grafana, Loki, skills |
| [storage.md](.claude/agent_docs/storage.md) | Verda SFS and block storage options |
| [gotchas.md](.claude/agent_docs/gotchas.md) | Non-critical known issues and workarounds |
| [external-references.md](.claude/agent_docs/external-references.md) | Research references and related projects |

---

**Last Updated:** 2026-02-10 -- Refactored to progressive disclosure modules
