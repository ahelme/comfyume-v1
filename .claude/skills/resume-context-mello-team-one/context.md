# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-16

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy. Inference BROKEN (admin team investigating — serverless returns status=error, QM logging improved in PR #51).

**Last session completed:** Backup system fully verified. R2: 13 uploads, 0 failures, all VERIFIED. Cron running. Gap analysis of restore script found 6 critical naming mismatches.

**Backup status:** ALL items present and verified on R2. See `comfymulti-scripts/backups-log.md` for dashboard.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially Backup and Restore, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~160 lines) — Priority tasks + Report 52
3. **`git log --oneline -10`** — Recent commits
4. **`comfymulti-scripts/restore-verda-instance.sh`** — The restore script that needs fixing (1688 lines)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Fix restore script — BLOCKER for testing instance !!**

The restore script (`comfymulti-scripts/restore-verda-instance.sh`) has 6 critical naming mismatches with the current backup system. It WILL FAIL on a new instance:

1. **Container images:** Script looks for `app-containers.tar.gz` (single file). Backups produce individual tarballs: `comfyume-frontend-v0.11.0.tar.gz`, `comfyume-queue-manager.tar.gz`, etc. on R2 `comfyume-worker-container-backups` bucket.

2. **R2 key paths:** `get_cache_file()` looks for `s3://comfyume-cache-backups/<filename>` (root). Backups put files under `s3://comfyume-cache-backups/config/<filename>`. Script won't find them.

3. **SSL cert naming:** Script looks for `letsencrypt-backup.tar.gz`. Backups produce `ssl-certs-YYYY-MM-DD.tar.gz`.

4. **Wrong repo:** `GH_APP_REPO=ahelme/comfyume` should be `ahelme/comfyume-v1`.

5. **Wrong project dir:** `PROJECT_DIR=/home/dev/comfyume` should be `/home/dev/comfyume-v1`. `PROJECT_NAME=comfyume` should be `comfyume-v1`.

6. **SFS-clone empty:** Testing instance uses SFS-clone (not SFS-prod), but SFS-clone has NO models, NO cache, NOTHING. Either copy models from SFS-prod or share SFS-prod with testing instance.

**Also fix known bugs (scripts #41-#45):**
- #41: `git pull origin main` → `git fetch origin && git reset --hard origin/main`
- #42: Tarball priority too high → git pull after tarball restore, OR check tarball age
- #43: Stop/disable host nginx before starting container nginx (`systemctl stop nginx && systemctl disable nginx`)
- #44: Copy custom nodes to user data dirs after restore
- #45: Set SFS `/mnt/sfs/outputs` to 1777 permissions, add fstab entry

**After restore script is fixed:**
- Provision testing instance (Verda CPU, FIN-01 or FIN-03)
- Run restore script on it
- Fix production issues there (inference regression)
- Deploy to prod via blue-green

**Other pending:**
- Username rename dev→aeon (#37)
- Hetzner Object Storage setup (#42)
- Run setup-monitoring.sh

---

## KEY INFRASTRUCTURE

**Resource naming convention:** `PROD_*` `CLONE_*` `STAG_*` `TEST_*` `UNUSED_*`

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`
- SFS-clone: `/mnt/clone-sfs` — `CLONE_SFS-Model-Vault-16-Feb-97Es5EBC` (EMPTY!)

**R2 Buckets (4):** comfyume-model-vault-backups, comfyume-cache-backups, comfyume-worker-container-backups, comfyume-user-files-backups. Dashboard: `comfymulti-scripts/backups-log.md`.

**Backup automation (Verda cron):**
- Hourly: 8 config items to SFS (50M)
- 3am: 4 container images to SFS
- 2/6/14/18:00: R2 upload (all config + containers)
- Verify log: `/var/log/r2-verify.log`

**Key files:**
| File | Purpose |
|------|---------|
| `comfymulti-scripts/restore-verda-instance.sh` | THE FILE TO FIX — 1688 lines, v0.4.3 |
| `comfymulti-scripts/backups-log.md` | R2 backup status dashboard |
| `comfymulti-scripts/backup-cron.sh` | Hourly SFS backup + R2 trigger |
| `comfymulti-scripts/upload-backups-to-r2.sh` | R2 upload with verification |
| `queue-manager/main.py` | Job routing, serverless polling, SFS image fetching |
| `scripts/deploy.sh` | Git-based deploy (REMOTE_DIR still /home/dev/ — #37 to fix) |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
