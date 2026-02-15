# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-15

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda (ex. DataCrunch) CPU instance. 24 containers healthy. Serverless inference working. Image delivery FIXED.

**This session completed:** Verda infra cleanup, SFS clone, resource naming convention. Phase 1.75 done.

**SFS clone COMPLETE:** 128GB rsync'd from SFS-prod to SFS-clone. Both mounted on quiet-city.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially Resource Naming Convention, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~140 lines) — Priority tasks + Report 50
3. **`git log --oneline -10`** — Recent commits
4. **`docs/media-generation-flow.md`** (skim) — End-to-end flow for reference

---

## IMMEDIATE NEXT STEPS

**1. Check Temp-Model-Vault for extra models (#38)**
   - Aeon is spinning up RTX A6000 spot instance in FIN-01 (no CPU available)
   - Temp-Model-Vault block vol restored from deleted state
   - Mount block vol + both SFS on the new instance, compare model lists
   - Copy any extras to both SFS-prod and SFS-clone
   - Then delete block vol permanently
   - See #38 for full step-by-step

**2. Username rename dev→aeon (#37)**
   - Create NEW `aeon` user on Mello and Verda (not rename)
   - Full audit done — see #37 for file-by-file checklist
   - Both repos need updates (~180+ references across active + archive files)
   - .env files need VERDA_DEV_USER_PASSWORD → VERDA_AEON_USER_PASSWORD

**3. Fix restore script (comfymulti-scripts repo):**
   - #41: git pull fails silently on diverged history
   - #42: stale tarball overrides git fixes
   - #43: host nginx blocks port 80
   - #44: missing custom nodes deployment step
   - #45: NEW — codify Ralph's server-side fixes (SFS permissions, Verda config)

**4. Test end-to-end on fresh instance:**
   - Run all 5 workflows (only workflow 1 tested so far)
   - Verify image delivery works on clean setup

**5. Phase 2 — Testing Server (#31, #38)**
   - RTX A6000 instance stays for Phase 2 testing (or spin up CPU when available)
   - Set up testing.aiworkshop.art

**6. Other pending:**
   - Investigate .env variable warnings (#7)
   - Run setup-monitoring.sh (Prometheus, Grafana, Loki)

---

## KEY INFRASTRUCTURE

**Resource naming convention:** `PROD_*` `CLONE_*` `STAG_*` `TEST_*` `UNUSED_*`

**SFS volumes (both on quiet-city):**
- SFS-prod: `/mnt/sfs` — `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`
- SFS-clone: `/mnt/clone-sfs` — `CLONE_SFS-Model-Vault-16-Feb-97Es5EBC`

**DANGER:** Renaming SFS console name may change pseudopath on next reboot. See gotchas.md.

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
| `.claude/agent_docs/gotchas.md` | SFS pseudopath risk, nginx %2F, health check deps |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Check if Aeon's RTX A6000 instance is up — ask for IP if so
- [ ] Read `.claude/qa-state.json` for fix loop state
