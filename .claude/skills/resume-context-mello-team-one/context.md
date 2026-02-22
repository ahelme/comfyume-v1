# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-22

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `testing-mello-team-one-2026-02-22`.

**Production:** aiworkshop.art on quiet-city (65.108.33.101). 24 containers healthy.
**Testing:** anegg.app on testing-009 (65.108.33.80). Shared by all teams via `testing-009` branch.

**This session completed:**
- #82 SFS-based result delivery implemented + deployed to testing-009 (PR #83 merged)
- QM startup confirmed: "Delivery mode: SFS (prefix injection)"
- SFS watch runs correctly: 200 polls/600s, prefix matching, clean timeout
- BLOCKED: serverless container accepts prompt but never executes (VRAM empty, no model loaded)
- SaladTechnologies research: sidecar pattern vs our split architecture
- `/update-progress` skill updated to include GH issue updates (step 4)

**Key finding:** The SFS delivery code works. The problem is upstream — the serverless container's ComfyUI accepts the HTTP POST but the execution engine never processes the prompt. Models never load into VRAM.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (especially "Deploying to Testing-009" section)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) — Priority tasks + phase details
3. **`git log --oneline -10`** — Recent commits
4. **`.claude/qa-state.json`** — Fix loop state (no active loop)

---

## IMMEDIATE NEXT STEPS

**!! PRIORITY: Debug serverless container execution (#82, #74, #66) !!**
- SFS delivery code is deployed and working — QM correctly injects prefix, polls SFS, times out cleanly
- The blocker is the serverless container itself — it accepts prompts but never executes them
- `system_stats` showed `torch_vram_total: 0` after 10 min — no model loaded
- Possible causes: model loading fails silently on CLONE_SFS, container recycled, execution engine issue
- Try: warm inference test (container may still be up), production endpoint, check Verda container logs
- The `comfyui-debugging.md` doc has API endpoints and CLI flags for diagnosis
- User credentials for testing: `USER_CREDENTIALS_USER001` in `/home/dev/comfymulti-scripts/.env`

**Also pending:** Username rename dev→aeon (#37), GPU overlay real-time status from QM via WebSocket

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- **After `docker compose build`, use `up -d` NOT `restart`** — restart reuses old image!
- Must rebuild Docker image to update extensions: `docker build -t comfyume-frontend:v0.11.0 -f comfyui-frontend/Dockerfile .`
- See CLAUDE.md "Deploying to Testing-009" for full workflow

---

## KEY INFRASTRUCTURE

**SFS volumes:**
- Testing-009 mounts CLONE_SFS at `/mnt/sfs` (192GB, 22 models)
- Serverless containers mount same CLONE_SFS via terraform.tfvars `sfs_volume_id = fd7efb9e-...`
- Both confirmed to be the same volume

**R2 Buckets (4):** model-vault, cache, worker-container, user-files

**Production:** root@65.108.33.101, project at /home/dev/comfyume-v1
**Testing-009:** root@65.108.33.80, project at /home/dev/comfyume-v1
**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] `git pull origin testing-mello-team-one-2026-02-22` — get latest
- [ ] SSH to testing-009: `ssh root@65.108.33.80 'docker logs comfy-queue-manager --tail 5 2>&1'` — check QM running
- [ ] Read `.claude/qa-state.json` for fix loop state
