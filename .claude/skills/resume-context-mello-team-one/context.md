# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-15

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda (ex. DataCrunch) CPU instance.

**Current state:** PRODUCTION LIVE AND WORKING. 24 containers healthy. Serverless inference working. Image delivery FIXED. Flux2 Klein 9B passing all 8 QA criteria.

**3-tier deployment workflow established:** testing → staging → production. Blue-green deploy via DNS. Per-team testing dirs on Mello. All code committed, PR #36 merged to main.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially Deployment Workflow, Critical Gotchas)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~130 lines) — Priority tasks + Report 49
3. **`git log --oneline -10`** — Recent commits
4. **`docs/media-generation-flow.md`** (skim) — End-to-end flow for reference

---

## IMMEDIATE NEXT STEPS

**1. Username rename dev→aeon (#37)**
   - Rename Linux user `dev` to `aeon` on Mello and Verda
   - Cannot rename while logged in — needs root session
   - Update restore script (comfymulti-scripts repo)
   - See #37 for full checklist

**2. Phase 2 — Testing Server + Restore Script Fixes (#31)**
   - Create new Verda testing instance + scratch disk + SFS-clone
   - Set up testing.aiworkshop.art (DNS already configured by user)
   - Fix restore script bugs (scripts #41, #42, #43, #44, #45)
   - Run restore, test end-to-end (all 5 workflows)

**3. Other pending:**
   - Investigate .env variable warnings (#7)
   - Run setup-monitoring.sh (Prometheus, Grafana, Loki)
   - Close #8 (app flow doc done), close #22 (image delivery resolved)

---

## KEY ARCHITECTURE (quick reference)

```
Browser → ComfyUI native queue (serverless_proxy patches PromptExecutor)
  → POST /api/jobs → nginx → queue-manager:3000
  → QM submit_to_serverless() → POST to Verda H200 /prompt
  → QM polls /api/history/{prompt_id} (600s max, 10s per-poll)
  → Images saved to /mnt/sfs/outputs/ by serverless container (!1777 perms)
  → QM copies from SFS to /outputs/user001/
  → Frontend serves via /api/view → image in UI + sidebar
  !!! NO direct HTTP back to serverless — load-balanced, different instance each request
```

**Key files:**
| File | Purpose |
|------|---------|
| `comfyume-extensions/serverless_proxy/__init__.py` | Patches PromptExecutor for serverless delegation |
| `comfyume-extensions/queue_redirect/web/redirect.js` | Defers to native queue in serverless mode |
| `comfyume-extensions/extensions.conf` | Enable/disable extensions |
| `queue-manager/main.py` | Job routing, serverless polling (`poll_serverless_history` :174), SFS image fetching (:279) |
| `comfyui-frontend/docker-entrypoint.sh` | Extension deploy, output symlink |
| `scripts/deploy.sh` | Git-based deploy: push → pull → rebuild → recreate |
| `.claude/qa-state.json` | Fix loop QA state |
| `docs/media-generation-flow.md` | 21-step end-to-end flow reference |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
