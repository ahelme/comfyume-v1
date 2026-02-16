# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-16

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy. Inference BROKEN (admin team investigating — serverless returns status=error).

**Last session completed:** Restore script v0.5.0 — all 6 naming mismatches and 5 bugs (#41-#45) fixed. Merged as scripts PR #52.

**Backup status:** ALL items present and verified on R2. Cron running. Dashboard: `comfymulti-scripts/backups-log.md`.

**Restore script status:** v0.5.0 READY. Matches backup system. Not yet tested on a real instance.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially Backup and Restore, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~100 lines) — Priority tasks + Reports 52-53
3. **`git log --oneline -10`** — Recent commits
4. **`comfymulti-scripts/restore-verda-instance.sh`** — The fixed restore script (1828 lines, v0.5.0)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Provision testing instance — restore script is ready !!**

### Step 1: Copy models to CLONE_SFS (scripts #51)

SFS-clone (`CLONE_SFS-Model-Vault-16-Feb-97Es5EBC` at `/mnt/clone-sfs`) is EMPTY. Testing instance needs models.

```bash
# On quiet-city (both SFS volumes mounted):
rsync -avP /mnt/sfs/models/ /mnt/clone-sfs/models/     # ~192 GiB
rsync -avP /mnt/sfs/cache/ /mnt/clone-sfs/cache/       # backups + container images
```

Alternative: share SFS-prod with the testing instance (faster, no copy needed).

### Step 2: Provision testing instance

- Verda CPU instance (FIN-01 or FIN-03)
- Add both SSH keys during provisioning (Mello + Aeon)
- Create and attach block storage AFTER boot (not during — gets wiped!)
- Share SFS with new instance via Verda console share settings

### Step 3: Run restore script

```bash
# On new instance:
./restore-verda-instance.sh "mount -t nfs -o nconnect=16 nfs.fin-01.datacrunch.io:/<SFS-path> /mnt/sfs" --format-scratch
```

### Step 4: Fix production issues on testing instance

- Inference regression (serverless returns status=error)
- Test all 5 workflows end-to-end
- Deploy to prod via blue-green when confident

**Other pending:**
- Username rename dev→aeon (#37)
- Hetzner Object Storage setup (comfyume-v1 #42)
- Run setup-monitoring.sh

---

## KEY INFRASTRUCTURE

**Resource naming convention:** `PROD_*` `CLONE_*` `STAG_*` `TEST_*` `UNUSED_*`

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`
- SFS-clone: `/mnt/clone-sfs` — `CLONE_SFS-Model-Vault-16-Feb-97Es5EBC` (EMPTY!)

**R2 Buckets (4):** comfyume-model-vault-backups, comfyume-cache-backups, comfyume-worker-container-backups, comfyume-user-files-backups. Dashboard: `comfymulti-scripts/backups-log.md`.

**Key files:**
| File | Purpose |
|------|---------|
| `comfymulti-scripts/restore-verda-instance.sh` | v0.5.0 — READY, not yet tested on instance |
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
