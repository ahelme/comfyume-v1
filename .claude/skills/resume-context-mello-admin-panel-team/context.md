# CLAUDE RESUME - COMFYUME (ADMIN PANEL TEAM)

**DATE**: 2026-02-17

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

**Debugging reference:** `docs/comfyui-debugging.md` — check BEFORE investigating any ComfyUI issue.

**Branching decision:** Continue with branches (not fork) for #66 architecture work. Feature branches off team branch provide code isolation; testing-009 provides infrastructure isolation.

---

## TOP PRIORITY: SFS-Based Result Delivery (#66)

### Root Cause of Inference Regression (#101) — CONFIRMED

Verda's serverless load balancer routes each HTTP request to a **different** container instance:
- `POST /prompt` → instance A (accepts, starts executing)
- `GET /history/{prompt_id}` → instance B (never saw this prompt, returns `{}`)

**Evidence (2026-02-17):** Two test jobs submitted, both accepted (HTTP 200), both timed out after 600s of polling with `Keys: []` — prompt_id never appeared in history.

### Proposed Architecture: "Dumb Pipes, Smart QM"

```
Frontend (ComfyUI + 1 thin extension: queue_redirect)
  ↓ POST /api/jobs
QM (FastAPI — fully ours, fire-and-forget POST /prompt)
  ↓
Serverless Worker (VANILLA ComfyUI, --output-directory /mnt/sfs/outputs)
  ↓ writes to SFS
QM watches /mnt/sfs/outputs/ (filesystem, NOT HTTP polling)
  ↓ copies to /outputs/userXXX/
Frontend serves locally
```

**Key changes:**
- Kill `serverless_proxy` extension (fragile, hooks into ComfyUI WebSocket internals)
- QM watches SFS filesystem instead of polling `/history/{id}` over HTTP
- Workers = vanilla ComfyUI (zero custom code) — migration-proof
- QM sends progress via its own WebSocket to frontend

**Challenge:** Matching output files to jobs (ComfyUI filenames don't contain prompt_id). Options: timestamp matching, unique prefix, or single-job attribution (`concurrent_requests_per_replica = 1`).

### Testing Instance Ready

**Instance 009:** `intelligent-rain-shrinks-fin-01` (65.108.33.80, CPU.8V.32G, fixed €0.0474/hr)
- **Domain:** anegg.app (DNS pointed, PR #68)
- CLONE_SFS attached (fd7efb9e-..., 220GB)
- Scratch disk attached (c07825bd-..., 50GB, /dev/vdb)
- Registered in infrastructure-registry.md (private scripts repo)

---

## Completed (Previous Sessions)

- [x] **#61** — nginx .htpasswd regenerated, all auth working
- [x] **#58** — SSL certbot renewal fixed, CORS cleaned (PR #59 merged)
- [x] **#66** — Architecture issue created with full design + test results
- [x] `--verbose` flag added to all containers (PR #67 merged)
- [x] `docs/comfyui-debugging.md` created
- [x] CLAUDE.md Critical Instruction #6: use debugging guide
- [x] OpenTofu danger warnings in context.md + containers.tf
- [x] Infrastructure registry: instance 009 + block vols 010/011
- [x] `anegg.app` domain added to infrastructure-registry.md + infrastructure.md (PR #68)

---

## OpenTofu IaC (#54) — ON NEW TESTING SERVER ONLY

**DONE:**
- [x] OpenTofu v1.11.5 on Mello, provider v1.1.1
- [x] `infrastructure/` dir: providers.tf, variables.tf, containers.tf
- [x] All 4 deployments imported, plan = 0 drift
- [x] `--verbose` added to .tf base_cmd

**TODO (on testing-009 only):**
- [ ] First `tofu apply` on testing server
- [ ] Add `--output-directory /mnt/sfs/outputs` to 3 missing deployments
- [ ] Fix healthcheck `/` → `/system_stats`

**Credentials:** `VERDA_CLIENT_ID` + `VERDA_CLIENT_SECRET` from `/home/dev/comfymulti-scripts/.env`

---

## MONITORING STACK (#106)

All live on production. Use `/verda-monitoring-check` to verify.

| Tool | Port | Access |
|------|------|--------|
| Prometheus | :9090 | https://prometheus.aiworkshop.art |
| Grafana | :3001 | https://grafana.aiworkshop.art |
| Loki | :3100 | via Grafana or SSH |
| cAdvisor | :8081 | via Prometheus |
| Portainer | :9443 | https://portainer.aiworkshop.art |

---

## GITHUB ISSUES

- **#68** — PR: add anegg.app testing domain. Pending merge.
- **#66** — TOP PRIORITY. SFS-based result delivery architecture. Root cause of #101.
- **#101** — Inference regression. Root cause = LB routing (#66). Symptom, not the fix target.
- **#54** — OpenTofu IaC. Import done, apply on testing-009 next.
- **#48** — QM logging gap: doesn't catch "prompt never appeared" timeout. Needs fix.
- **#63** — Browser console log tracking (user-created).
- **#44** — GPU progress banner for serverless mode.
- **#45** — Cookie-based auth persistence.
- **#46** — Cold start silent failure UX.
- **#22** — Image delivery gap. Root cause same as #66 (LB routing).
- **#43** — NFS model visibility. Fixed, close after inference works.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` top section
- [ ] Read `docs/comfyui-debugging.md` if investigating any ComfyUI issue
- [ ] Set up testing-009 with comfyume-v1 stack (deploy to anegg.app)
- [ ] Work on #66: implement SFS filesystem watching in QM (on testing-009)
- [ ] First `tofu apply` on testing-009 (#54)
- [ ] After inference fixed: close #43, work on #44/#45/#46
