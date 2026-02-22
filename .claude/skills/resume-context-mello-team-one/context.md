# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-22

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy.
**Testing:** anegg.app on testing-009 (65.108.33.80). Shared by all teams.

**This session:** Fixed serverless_proxy error handling (#73), added early bail on LB routing miss, created modular GPU overlay (status_banner + gpu_overlay extensions with admin/user modes), verified inference on testing-009 (31s warm). Identified branch collision problem on testing-009 — solved with shared `testing-009` deployment branch.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially "Deploying to Testing-009" section)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) — Priority tasks + all phase details
3. **`git log --oneline -10`** — Recent commits
4. **`.claude/qa-state.json`** — Fix loop state (no active loop)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Cold-start inference failure (#74, #66) !!**
- Testing-009 works warm (31s), fails cold (LB routing — POST hits container A, GET /history hits container B)
- Early bail now detects this in ~120s instead of 600s
- Full fix: SFS-based result delivery (#66) — QM watches SFS filesystem instead of HTTP polling

**Also pending:** Username rename dev→aeon (#37), ComfyUI native progress bar not working during serverless inference

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- See CLAUDE.md "Deploying to Testing-009" for full workflow

---

## KEY INFRASTRUCTURE

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — 192GB, 22 models, all backups
- SFS-clone: `/mnt/clone-sfs` — 192GB, mirrors SFS-prod (verified 2026-02-17)

**R2 Buckets (4):** model-vault, cache, worker-container, user-files. Dashboard: `comfymulti-scripts/backups-log.md`

**SSH identities:** `comfymulti-scripts/secrets/ssh/verda_{production,testing,staging}_ed25519(.pub)`
All 3 public keys in Mello authorized_keys. Restore scripts use comment-out block.

**Production:** root@65.108.33.101, project at /home/dev/comfyume-v1
**Testing-009:** root@65.108.33.80, project at /home/dev/comfyume-v1
**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)
**Branch naming:** `testing-mello-team-one` (team), `testing-mello-team-one-<feature>` (feature)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
