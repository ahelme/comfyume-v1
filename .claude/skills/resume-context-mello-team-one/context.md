# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-17

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy. Inference status: admin team investigating serverless error responses.

**Phase 2.5 COMPLETE this session:** Backup system overhaul + SSH identity cleanup.
- backup-mello.sh → backup-user-data.sh (runs locally on Verda, not SSH to Mello)
- backup-cron.sh v3.2: local user data backup, fixed double-logging, disk-check --require
- Per-environment SSH identities: verda_{production,testing,staging}_ed25519 (scripts #55)
- Restore scripts: comment-out block for environment selection
- All deployed to Verda, verified working

**Next phase: 2.75 — Provision testing instance.** SFS-clone ready (22 models), restore script ready (v0.5.0), SSH identities ready.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially SSH Identities, Backup and Restore, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) — Priority tasks + all phase details
3. **`git log --oneline -10`** — Recent commits
4. **`.claude/qa-state.json`** — Fix loop state (no active loop)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Provision testing instance — everything is ready !!**

1. Provision Verda CPU instance (FIN-01 or FIN-03)
   - Add both SSH keys during provisioning (Mello + Aeon)
   - Create + attach block storage AFTER boot (not during — gets wiped!)
   - Share SFS-clone with new instance via Verda console share settings
2. Uncomment testing key in restore script, run on new instance
3. Fix production issues on testing instance (inference regression)
4. Deploy to prod via blue-green when confident

**Other pending:** Username rename dev→aeon (#37), Hetzner Object Storage (#42), setup-monitoring.sh

---

## KEY INFRASTRUCTURE

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — 192GB, 22 models, all backups
- SFS-clone: `/mnt/clone-sfs` — 192GB, mirrors SFS-prod (verified 2026-02-17)

**R2 Buckets (4):** model-vault, cache, worker-container, user-files. Dashboard: `comfymulti-scripts/backups-log.md`

**SSH identities:** `comfymulti-scripts/secrets/ssh/verda_{production,testing,staging}_ed25519(.pub)`
All 3 public keys in Mello authorized_keys. Restore scripts use comment-out block.

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1
**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)
**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
