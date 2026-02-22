# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-22

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one` (NOT main).
**Feature branch:** `testing-mello-team-one-new-testing-instance` (current work).

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy.
**Testing:** anegg.app on testing-009 (65.108.33.80). Shared by all teams via `testing-009` branch.

**This session completed:**
- #73 DONE: serverless_proxy error handling + early bail + HTTP error body extraction
- #44 DONE: GPU overlay (modular: status_banner + gpu_overlay), admin/user modes, no fake stages
- Shared `testing-009` deployment branch (prevents teams overwriting each other)
- Rebuilt comfyume-frontend:v0.11.0 with all 4 extensions baked in
- PR #77 merged to main

**Key discovery:** Docker entrypoint copies extensions from baked image on EVERY restart. Host-level `cp` gets overwritten. Must rebuild image to update extensions permanently.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially "Deploying to Testing-009" section)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) — Priority tasks + phase details
3. **`git log --oneline -10`** — Recent commits
4. **`.claude/qa-state.json`** — Fix loop state (no active loop)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Cold-start inference failure (#74, #66) !!**
- Testing-009 works warm (31s), fails cold (LB routing — POST hits container A, GET /history hits container B)
- Early bail detects this in ~170s with detailed error message
- Full fix needed: SFS-based result delivery (#66) — QM watches SFS filesystem instead of HTTP polling
- This is the main blocker for production with 20 users

**Also pending:** Username rename dev→aeon (#37), ComfyUI native progress bar not working during serverless inference

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- Must rebuild Docker image to update extensions: `docker build -t comfyume-frontend:v0.11.0 -f comfyui-frontend/Dockerfile .`
- See CLAUDE.md "Deploying to Testing-009" for full workflow

---

## KEY INFRASTRUCTURE

**SFS volumes (both on quiet-city, SFS-prod in fstab):**
- SFS-prod: `/mnt/sfs` — 192GB, 22 models, all backups
- SFS-clone: `/mnt/clone-sfs` — 192GB, mirrors SFS-prod (verified 2026-02-17)

**R2 Buckets (4):** model-vault, cache, worker-container, user-files

**Production:** root@65.108.33.101, project at /home/dev/comfyume-v1
**Testing-009:** root@65.108.33.80, project at /home/dev/comfyume-v1
**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one` — get latest
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
