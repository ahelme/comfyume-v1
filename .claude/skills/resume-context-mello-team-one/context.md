# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-16

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda (ex. DataCrunch) CPU instance. 24 containers healthy. Serverless inference working. Image delivery FIXED.

**Last session completed:** PR #41 merged. R2 audit of all 4 buckets. Backup scripts fixed (scripts #48). backups-log.md created.

**R2 backup status:** Models COMPLETE (24 files, ~192 GiB). Cache has 2 broken tarballs. No automated cron yet.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially Backup and Restore, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~140 lines) — Priority tasks + Report 51
3. **`git log --oneline -10`** — Recent commits
4. **`docs/media-generation-flow.md`** (skim) — End-to-end flow for reference

---

## IMMEDIATE NEXT STEPS

**1. Fix broken backup scripts (#42, scripts #48)**
   - SSL cert backup: certs inside nginx container at `/etc/nginx/ssl/`, not on host. Need `docker cp comfy-nginx:/etc/nginx/ssl/ /tmp/ssl-backup/` before tarring
   - SSH host key backup: script used wrong source path, keys at `/etc/ssh/ssh_host_*`
   - backup-cron.sh has uncommitted image naming fix (scripts repo)
   - Set up cron jobs on production (NO automated backups running yet)

**2. Upload missing container images to R2**
   - User noted we missed most container images in previous upload
   - Container image backup was started in rewound conversation — verify status
   - Need ALL images: frontend, worker, queue-manager, nginx, admin, redis, grafana, prometheus, loki, cadvisor, dry
   - Use dated naming: `<image-name>-<YYYY-MM-DD>.tar.gz`

**3. Username rename dev→aeon (#37)**
   - Create NEW `aeon` user on Mello and Verda (not rename)
   - Full audit done — see #37 for file-by-file checklist
   - Both repos need updates (~180+ references across active + archive files)

**4. Fix restore script (comfymulti-scripts repo):**
   - #41: git pull fails silently on diverged history
   - #42: stale tarball overrides git fixes
   - #43: host nginx blocks port 80
   - #44: missing custom nodes deployment step
   - #45: codify Ralph's server-side fixes (SFS permissions, Verda config)

**5. Test end-to-end on fresh instance:**
   - Run all 5 workflows (only workflow 1 tested so far)
   - No testing instance available (FIN-01 CPU scarce)

**6. Other pending:**
   - Hetzner Object Storage setup — same bucket names as R2 (#42)
   - Investigate .env variable warnings (#7)
   - Run setup-monitoring.sh (Prometheus, Grafana, Loki)

---

## KEY INFRASTRUCTURE

**Resource naming convention:** `PROD_*` `CLONE_*` `STAG_*` `TEST_*` `UNUSED_*`

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`
- SFS-clone: `/mnt/clone-sfs` — `CLONE_SFS-Model-Vault-16-Feb-97Es5EBC`

**DANGER:** Renaming SFS console name may change pseudopath on next reboot. See gotchas.md.

**R2 Buckets (4):** comfyume-model-vault-backups, comfyume-cache-backups, comfyume-worker-container-backups, comfyume-user-files-backups. Audit trail: `comfymulti-scripts/backups-log.md`.

**DR backup:** PROD_OS cloned to block-vol 009 (BACKUP_2026-02-16-PROD_OS-hiq7F8JM, 100GB).

**CRUCIAL QUEUE MANAGER FLOW:**
```
Browser → ComfyUI native queue (serverless_proxy patches PromptExecutor)
  → POST /api/jobs → nginx → queue-manager:3000
  → QM submit_to_serverless() → POST to Verda H200 /prompt
  → QM polls /api/history/{prompt_id} (600s max, 10s per-poll)
  → Images saved to /mnt/sfs/outputs/ by serverless container
  → QM copies from SFS to /outputs/user001/
  → Frontend serves via /api/view → image in UI + sidebar
```

**Key files:**
| File | Purpose |
|------|---------|
| `comfyume-extensions/serverless_proxy/__init__.py` | Patches PromptExecutor for serverless delegation |
| `comfyume-extensions/queue_redirect/web/redirect.js` | Defers to native queue in serverless mode |
| `queue-manager/main.py` | Job routing, serverless polling, SFS image fetching |
| `scripts/deploy.sh` | Git-based deploy (REMOTE_DIR still /home/dev/ — #37 to fix) |
| `.claude/agent_docs/backups.md` | Backup retention policy, R2 bucket schedules |
| `.claude/agent_docs/gotchas.md` | SFS pseudopath risk, nginx %2F, health check deps |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
