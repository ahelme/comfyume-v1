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
- **Feature branch:** `testing-mello-admin-panel-team-new-testing-instance` (current)

**Production:** aiworkshop.art on Verda (quiet-city, 65.108.33.101), NOT Mello.
**Testing:** anegg.app on Verda (intelligent-rain-shrinks, 65.108.33.80).

**SSH (production):** `ssh dev@100.89.38.43` (Tailscale IP).
**SSH (testing):** `ssh root@65.108.33.80` (public IP).

**Debugging reference:** `docs/comfyui-debugging.md` — check BEFORE investigating any ComfyUI issue.
**Learnings from testing-009:** `docs/learnings-testing-instance-009.md` — gotchas, root causes, fixes.

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

### What Was Fixed This Session
- `infrastructure/`: `environment` variable added — `prod` unchanged, `test` creates `comfyume-test-*`
- `.gitignore`: Added tfstate/tfvars exclusions across all 7 repos on Mello
- `CLAUDE.md`: Production safety verification table (state file isolation)
- `docs/learnings`: permissions 777→1777 (sticky bit), CORS comment, --verbose note
- htpasswd: restored correct per-user strong passwords (was incorrectly "workshop")

---

## NEXT STEPS

### Immediate — Test Inference (#72 step 8)
- [ ] Submit Flux2 Klein generation from anegg.app/user001/
- [ ] Verify the generated image appears (not the stale hedgehog from Feb 17)
- [ ] Check QM logs for `SFS image:` (Strategy 1 — direct SFS read should now work)
- [ ] If CLIP model error appears (`clip input is invalid: None`), investigate text encoder path on CLONE_SFS

### After Inference Verified
- [ ] Test with multiple users simultaneously (user001 + user002)
- [ ] Test LTX-2 video workflow (heavier, longer inference)
- [ ] Close #72 once E2E verified

### Architecture (#66) — SFS-Based Result Delivery (Production)
For production with 20 concurrent users, the full SFS-based architecture is still needed:
- QM watches SFS filesystem instead of polling `/history/{id}` over HTTP
- Workers = vanilla ComfyUI (zero custom code on serverless)
- Challenge: Matching output files to jobs (filename doesn't contain prompt_id)

### Lower Priority
- [ ] **#44** — GPU progress banner for serverless mode
- [ ] **#45** — Cookie-based auth persistence
- [ ] **#46** — Cold start silent failure UX
- [ ] Create PR from feature branch to team branch

---

## GITHUB ISSUES

- **#72** — Apply environment-isolated serverless on testing-009. Steps 1-7 done. Step 8 (test inference) remaining.
- **#71** — SFS volume mismatch diagnosis. Resolved via environment isolation. Comment posted.
- **#69** — PR covering all work on this branch (9 commits). Updated title/description.
- **#70** — Testing instance 009 restored. Can close.
- **#66** — SFS-based result delivery architecture. Still needed for production.
- **#54** — OpenTofu IaC. `--output-directory` applied via tofu on testing-009.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` (Report 17)
- [ ] Verify testing-009 is running: `ssh root@65.108.33.80 'docker ps --format "{{.Names}}\t{{.Status}}" | sort'`
- [ ] If containers down: `cd /home/dev/comfyume-v1 && docker compose --profile container-nginx up -d`
- [ ] Test inference on anegg.app — verify image delivery via CLONE_SFS
- [ ] Continue with next steps above
