# CLAUDE RESUME - COMFYUME (ADMIN PANEL TEAM)

**DATE**: 2026-02-22

---

## DANGER — READ BEFORE DOING ANYTHING

**NEVER run `tofu plan`, `tofu apply`, or ANY OpenTofu/Terraform command from Mello against PRODUCTION.**
Testing-009 has its own tofu state managing `comfyume-test-*` deployments only. Production state lives on Mello.
See CLAUDE.md "Production Safety — State File Isolation" for details.

---

## CONTEXT

**We are the Mello Admin Panel Team.**
- **Team branch:** `testing-mello-admin-panel-team`

**Production:** aiworkshop.art on Verda (quiet-city, 65.108.33.101), NOT Mello.
**Testing:** anegg.app on Verda (intelligent-rain-shrinks, 65.108.33.80).

**SSH (production):** `ssh dev@100.89.38.43` (Tailscale IP).
**SSH (testing):** `ssh root@65.108.33.80` (public IP).

**Debugging reference:** `docs/comfyui-debugging.md` — check BEFORE investigating any ComfyUI issue.
**Learnings from testing-009:** `docs/learnings-testing-instance-009.md` — gotchas, root causes, fixes.

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- See CLAUDE.md "Deploying to Testing-009" for full workflow

**Workflow:**
1. Push changes to `testing-mello-admin-panel-team`
2. Merge into `testing-009` (PR or local merge + push)
3. On server: `cd /home/dev/comfyume-v1 && git pull origin testing-009`
4. Rebuild/restart as needed

---

## CURRENT STATE: Testing Instance 009 (anegg.app)

### Infrastructure
- All containers healthy: nginx, redis, QM, admin, user001-005
- SSL cert for anegg.app (expires 2026-05-18)
- Credentials: per-user strong passwords from `comfymulti-scripts/.env` (21 entries in htpasswd)
- 24 models visible on CLONE_SFS

### Environment-Isolated Serverless (#71, #72) — DEPLOYED
- `comfyume-test-vca-ftv-h200-spot` created via `tofu apply` on testing-009
- Mounts CLONE_SFS (same volume as testing instance) — SFS image delivery should now work
- QM confirmed using testing endpoint: `https://containers.datacrunch.io/comfyume-test-vca-ftv-h200-spot`
- OpenTofu v1.11.5 installed on testing-009, state in `/home/dev/comfyume-v1/infrastructure/`
- Production deployments (`comfyume-vca-ftv-*`) completely untouched

### Mello Team One Fixes (deployed 2026-02-22)
- serverless_proxy error handling — malformed execution_error fixed (#73)
- Early bail on LB routing miss — ~120s instead of 600s timeout (#73)
- GPU overlay extension — modular progress banner (admin/user modes, #44)
- status_banner extension — reusable UI component (window.comfyumeStatus API)
- Inference verified on testing-009 — 31s warm, Flux Klein 4B

---

## NEXT STEPS

### Immediate
- [ ] Test inference on anegg.app — verify image delivery via CLONE_SFS
- [ ] Test with multiple users simultaneously (user001 + user002)
- [ ] Close #72 once E2E verified

### Architecture (#66) — SFS-Based Result Delivery (Production)
For production with 20 concurrent users, the full SFS-based architecture is still needed:
- QM watches SFS filesystem instead of polling `/history/{id}` over HTTP
- Workers = vanilla ComfyUI (zero custom code on serverless)
- Challenge: Matching output files to jobs (filename doesn't contain prompt_id)

### Lower Priority
- [ ] **#44** — GPU progress banner — DONE (status_banner + gpu_overlay extensions)
- [ ] **#45** — Cookie-based auth persistence
- [ ] **#46** — Cold start silent failure UX

---

## GITHUB ISSUES

- **#72** — Apply environment-isolated serverless on testing-009. Steps 1-7 done. Step 8 (test inference) remaining.
- **#73** — Serverless proxy error handling — FIXED by Mello Team One
- **#74** — Cold-start inference failure — LB routing issue, needs #66
- **#71** — SFS volume mismatch diagnosis. Resolved via environment isolation.
- **#69** — PR covering environment isolation work.
- **#66** — SFS-based result delivery architecture. Still needed for production.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` (latest report)
- [ ] Verify testing-009 is running: `ssh root@65.108.33.80 'docker ps --format "{{.Names}}\t{{.Status}}" | sort'`
- [ ] If containers down: `cd /home/dev/comfyume-v1 && docker compose --profile container-nginx up -d`
- [ ] Test inference on anegg.app — verify image delivery via CLONE_SFS
- [ ] Continue with next steps above
