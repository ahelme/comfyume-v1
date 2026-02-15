# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-12

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `mello-team-one` (NOT main).

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** PRODUCTION LIVE AND WORKING. 24 containers healthy. Serverless inference working. Image delivery FIXED (Ralph Loop overnight, PRs #23-#28). Flux2 Klein 9B passing all 8 QA criteria.

**All code committed and merged to main. No uncommitted work. No deployment drift.**

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (Critical Instructions #4 and #5)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) — Priority tasks + Report 48
3. **`git log --oneline -10`** — Recent commits
4. **`docs/media-generation-flow.md`** (skim) — End-to-end flow for reference

---

## IMMEDIATE NEXT STEPS

**Phase 2 — Testing Server + Restore Script Fixes (#31)**

1. **Discuss staging server strategy with user:**
   - Verda gave free credits — can afford a testing server
   - Question: testing server only, or also a persistent staging server?
   - User leaning toward: test on testing server, then update production

2. **Create testing instance on Verda:**
   - New CPU instance + new blank scratch disk
   - Attach existing SFS (/mnt/sfs)
   - Run restore script — fixing bugs as they surface

3. **Fix restore script (comfymulti-scripts repo):**
   - #41: git pull fails silently on diverged history
   - #42: stale tarball overrides git fixes
   - #43: host nginx blocks port 80
   - #44: missing custom nodes deployment step
   - #45: NEW — codify Ralph's server-side fixes (SFS permissions, DataCrunch config)

4. **Test end-to-end on fresh instance:**
   - Run all 5 workflows (only workflow 1 tested so far)
   - Verify image delivery works on clean setup

5. **Other pending:**
   - Investigate .env variable warnings (#7)
   - Run setup-monitoring.sh (Prometheus, Grafana, Loki)
   - Close #8 (app flow doc done), close #22 (image delivery resolved)

---

## KEY ARCHITECTURE (quick reference)

```
Browser → ComfyUI native queue (serverless_proxy patches PromptExecutor)
  → POST /api/jobs → nginx → queue-manager:3000
  → QM submit_to_serverless() → POST to DataCrunch H200 /prompt
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
| `comfyume-extensions/extensions.conf` | Enable/disable extensions |
| `queue-manager/main.py` | Job routing, serverless polling, SFS image fetching |
| `comfyui-frontend/docker-entrypoint.sh` | Extension deploy, output symlink |
| `scripts/deploy.sh` | Git-based deploy: push → pull → rebuild → recreate |
| `.claude/qa-state.json` | Fix loop QA state |
| `docs/media-generation-flow.md` | 21-step end-to-end flow reference |
| `docs/admin-changes-to-comfyume-v1.md` | Complete changelog (35 commits, 8 phases) |
| `docs/admin-server-containers-sys-admin.md` | Server-side changes guide |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
