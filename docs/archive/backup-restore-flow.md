# Backup/Restore Flow Analysis

**Project:** ComfyUI Multi-User Workshop Platform
**Doc Created:** 2026-02-01
**Purpose:** Map backup/restore flow for comfyume deployment

---

## Current State

### Repositories
- **comfy-multi** (mello VPS) - `/home/dev/projects/comfyui/`
  - Queue manager, admin, nginx, user frontends
  - User data, workflows

- **comfyume** (verda GPU) - `/home/dev/comfyume/`
  - Worker code (Dockerfile, worker.py, vram_monitor.py)
  - NEW separate codebase

- **comfymulti-scripts** (private)
  - Deployment and backup scripts

---

## Backup/Restore Flow

### SCENARIO 1: First Deployment (No Backups Exist)

**Problem:** restore-verda-instance.sh expects backups, but none exist yet!

**Flow:**
```
1. Provision Verda instance
2. restore-verda-instance.sh runs
3. Checks SFS for comfyume backup → ❌ NOT FOUND
4. Checks R2 for comfyume backup → ❌ NOT FOUND
5. MISSING: Fallback to git clone OR copy from mello
   → Currently script would FAIL here!
```

**Solution Needed:**
```bash
# In restore-verda-instance.sh
if [ ! -d /home/dev/$PROJECT_NAME ]; then
    # No backup found - first deployment
    if [ -n "$GITHUB_TOKEN" ]; then
        # Clone from GitHub
        git clone https://github.com/ahelme/$PROJECT_NAME.git /home/dev/$PROJECT_NAME
    else
        # Or copy from mello via scp (requires mello connection)
        scp -r dev@100.99.216.71:/home/dev/$PROJECT_NAME /home/dev/
    fi
fi
```

---

### SCENARIO 2: Subsequent Deployments (Backups Exist)

**Flow:**
```
1. Provision Verda instance
2. restore-verda-instance.sh runs
3. Checks SFS for comfyume backup → ✅ FOUND (from previous session)
4. Restores comfyume codebase
5. Restores Tailscale identity (preserves IP)
6. Restores configs, container image
7. Models restored from SFS or R2
8. Worker starts
```

---

## What Gets Backed Up Where?

### From Verda (backup-verda.sh → R2)

**Critical System Configs:**
- Tailscale identity: `/var/lib/tailscale/` → SFS + R2
- SSH host keys: `/etc/ssh/ssh_host_*` → SFS + R2
- Security configs: fail2ban, ufw → SFS + R2

**Project Files:**
- `/home/dev/comfyume/` → R2 cache bucket
  - comfyui-worker/
  - .env (if exists)
  - docker-compose.yml

**Large Files:**
- Container image: `docker save` → R2 cache bucket (~2.5GB)
- Models: `/mnt/sfs/models/` → R2 models bucket (~45GB)

### From Mello (backup-mello.sh → R2)

**User Data:**
- `/home/dev/projects/comfyui/data/user_data/userXXX/` → R2 user-files bucket
- `/home/dev/projects/comfyui/data/workflows/` → R2 user-files bucket

**Optional (large):**
- `/home/dev/projects/comfyui/data/outputs/userXXX/` → R2 user-files bucket
- `/home/dev/projects/comfyui/data/inputs/userXXX/` → R2 user-files bucket

---

## Data Flow: Mello ↔ Verda ↔ Comfyume

### Question: Does comfyume need files from comfy-multi?

**Workflows:**
- Location on mello: `/home/dev/projects/comfyui/data/workflows/`
- Needed on verda? Maybe - for testing? Or loaded from mello queue?
- **Decision needed:** Copy workflows to comfyume repo OR fetch from mello at runtime?

**Models:**
- Location on mello: Empty (models live on verda SFS)
- Location on verda: `/mnt/sfs/models/` (symlinked to `/home/dev/comfyume/data/models/`)
- Backed up: Yes, to R2 models bucket

**User Data:**
- Location on mello: `/home/dev/projects/comfyui/data/user_data/`
- Needed on verda? NO - worker doesn't need user settings
- Backed up: Yes, from mello to R2 user-files bucket

---

## Files Missing from Comfyume Repo

### What comfyume currently has:
```
/home/dev/comfyume/
├── comfyui-worker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── worker.py
│   ├── vram_monitor.py
│   ├── start-worker.sh
│   ├── requirements.txt
│   ├── test-deployment.sh
│   └── README.md
├── docs/
│   └── implementation-plan-v0.11.0.md
└── .git/
```

### What comfyume needs for deployment:
```
/home/dev/comfyume/
├── comfyui-worker/          ✅ Exists
├── data/                    ❌ MISSING (created by setup script via symlinks)
│   ├── models/              → symlink to /mnt/sfs/models
│   ├── outputs/             → symlink to /mnt/scratch/outputs
│   └── inputs/              → symlink to /mnt/scratch/inputs
├── .env                     ❌ MISSING (contains REDIS_PASSWORD, etc.)
└── .git/                    ✅ Exists
```

---

## Issues Identified

### Issue 1: First Deployment Fallback
**Problem:** restore-verda-instance.sh has no fallback if backups don't exist
**Solution:** Add git clone or scp fallback for first deployment

### Issue 2: Environment Variables
**Problem:** .env file not in comfyume repo (contains secrets)
**Solution:**
- Create `.env.example` in repo
- restore-verda-instance.sh creates .env from template + secrets

### Issue 3: Workflows Location
**Problem:** Unclear if workflows needed on verda
**Current:** Workflows live on mello, jobs come via queue
**Decision:** Workflows NOT needed on verda (fetched from queue payload)

### Issue 4: Data Directory Structure
**Problem:** /home/dev/comfyume/data/ doesn't exist in repo
**Solution:** Created by restore-verda-instance.sh as symlinks (already implemented)

---

## Recommended Flow

### Pre-Deployment Checklist

**On Mello (development):**
1. ✅ Commit comfyume worker code to GitHub
2. ✅ Update comfymulti-scripts with PROJECT_NAME
3. ❌ Create .env.example template in comfyume repo
4. ❌ Test backup-mello.sh (backs up comfy-multi user data)

**On Verda (first deployment):**
1. ❌ Add git clone fallback to restore-verda-instance.sh
2. ❌ Test restore-verda-instance.sh with NO existing backups
3. ❌ Verify symlinks created: data/models, data/outputs, data/inputs
4. ❌ Test worker container build and startup
5. ❌ Test backup-verda.sh creates proper backups

**On Verda (subsequent deployments):**
1. ❌ Test restore from SFS cache (fast path)
2. ❌ Test restore from R2 (fallback path)
3. ❌ Verify Tailscale IP preserved

---

## Next Steps

1. **Create .env.example** in comfyume repo
2. **Update restore-verda-instance.sh** with git clone fallback
3. **Create GitHub issue** for first deployment testing
4. **Test locally** with Docker build before deploying to Verda

---

## Questions for User

1. Should workflows be copied to comfyume repo or fetched from mello at runtime?
2. Should we test local Docker build first before Verda deployment?
3. Any other files from comfy-multi needed in comfyume?
