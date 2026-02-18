# CLAUDE RESUME - COMFYUME (ADMIN PANEL TEAM)

**DATE**: 2026-02-18

---

## DANGER — READ BEFORE DOING ANYTHING

**NEVER run `tofu plan`, `tofu apply`, or ANY OpenTofu/Terraform command from Mello or against production.**
OpenTofu commands ONLY run on a NEW TESTING server instance. Mistakes here change live serverless GPU deployments and cannot be easily reversed. Edit `.tf` files, commit via git flow, apply ONLY on a new testing server.

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

## CURRENT STATE: Testing Instance 009 (anegg.app) — FULLY OPERATIONAL

### What's Running
- All containers healthy: nginx, redis, QM, admin, user001-005
- SSL cert for anegg.app (expires 2026-05-18)
- QM: serverless mode, H200-SPOT active
- ComfyUI loads at `https://anegg.app/user001/` (auth: user001/workshop)
- 24 models visible, no Missing Models popup
- **E2E inference working** — Flux Klein 4B tested (18s warm, 307s cold)

### What Was Fixed This Session (#70)
- `infrastructure/containers.tf`: All 4 deployments now have `--output-directory /mnt/sfs/outputs` (was only h200-spot)
- `queue-manager/main.py`: Added `https://anegg.app` to CORS allow_origins
- `nginx/nginx.conf`: Changed hardcoded CORS origin to `$http_origin` (on testing instance only)
- `/mnt/scratch/outputs/`: Fixed permissions (`chmod -R 777`)
- `.htpasswd`: Created in `nginx/` dir (6 users + admin, password: workshop)
- `.env`: Comprehensive testing config (serverless, NUM_USERS=5, anegg.app domain)
- Frontend image: Rebuilt from correct branch (comfyume-v1, not comfy-multi)

### Key Discovery: LB Routing (#66) Partially Mitigated
- **Cold start (~5 min):** Model loading blocks container. LB routes GETs to different containers → empty history for ~300s. Eventually works when container becomes responsive.
- **Warm container (~18s):** History poll succeeds quickly. HTTP `/view` fallback downloads image.
- **SFS volume mismatch:** Serverless containers mount PROD_SFS, testing mounts CLONE_SFS. SFS-based image delivery won't work cross-environment. On production (same SFS), it would work.

---

## NEXT STEPS

### Immediate (on testing-009)
- [ ] Apply `--output-directory` fix via `tofu apply` on testing-009 (#54)
  - File ready: `infrastructure/containers.tf` already updated in git
  - Need `terraform.tfvars` with CLONE_SFS volume ID for testing
  - Credentials: `VERDA_CLIENT_ID` + `VERDA_CLIENT_SECRET` from `/home/dev/comfymulti-scripts/.env`
- [ ] Test with multiple users simultaneously (user001 + user002)
- [ ] Test LTX-2 video workflow (heavier, longer inference)

### Architecture (#66) — SFS-Based Result Delivery
The LB routing works for warm containers but is unreliable during cold starts. For production with 20 concurrent users, the full SFS-based architecture is still needed:

```
Frontend (ComfyUI + queue_redirect extension)
  ↓ POST /api/jobs
QM (FastAPI — fire-and-forget POST /prompt)
  ↓
Serverless Worker (VANILLA ComfyUI, --output-directory /mnt/sfs/outputs)
  ↓ writes to SFS
QM watches /mnt/sfs/outputs/ (filesystem, NOT HTTP polling)
  ↓ copies to /outputs/userXXX/
Frontend serves locally
```

**Key changes needed:**
- QM watches SFS filesystem instead of polling `/history/{id}` over HTTP
- Kill `serverless_proxy` extension (fragile)
- Workers = vanilla ComfyUI (zero custom code)
- Challenge: Matching output files to jobs (filename doesn't contain prompt_id)

### Lower Priority
- [ ] **#44** — GPU progress banner for serverless mode
- [ ] **#45** — Cookie-based auth persistence
- [ ] **#46** — Cold start silent failure UX
- [ ] Create PR from feature branch to team branch

---

## OpenTofu IaC (#54) — ON NEW TESTING SERVER ONLY

**DONE:**
- [x] OpenTofu v1.11.5 on Mello, provider v1.1.1
- [x] `infrastructure/` dir: providers.tf, variables.tf, containers.tf
- [x] All 4 deployments imported, plan = 0 drift
- [x] `--output-directory` added to all 4 deployments in .tf (committed)

**TODO (on testing-009 only):**
- [ ] Create `terraform.tfvars` on testing-009 with CLONE_SFS volume ID
- [ ] `tofu init && tofu plan` — review changes (should show cmd change on 3 deployments)
- [ ] `tofu apply` after user confirmation

---

## GITHUB ISSUES

- **#70** — Testing instance 009 restored + E2E inference working. Comment posted. Can close.
- **#66** — SFS-based result delivery architecture. Still needed for production reliability.
- **#54** — OpenTofu IaC. `--output-directory` fix committed, needs `tofu apply` on testing-009.
- **#101** — Inference regression. Partially fixed (works when warm). Root cause = LB routing (#66).
- **#44** — GPU progress banner for serverless mode.
- **#45** — Cookie-based auth persistence.
- **#46** — Cold start silent failure UX.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` (Report 16)
- [ ] Read `docs/learnings-testing-instance-009.md` for gotchas
- [ ] Verify testing-009 is still running: `ssh root@65.108.33.80 'docker ps --format "{{.Names}}\t{{.Status}}" | sort'`
- [ ] If containers down: `cd /home/dev/comfyume-v1 && docker compose --profile container-nginx up -d`
- [ ] Continue with next steps above
