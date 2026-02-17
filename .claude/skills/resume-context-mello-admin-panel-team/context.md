# CLAUDE RESUME - COMFYUME (ADMIN PANEL TEAM)

**DATE**: 2026-02-17

---

## DANGER — READ BEFORE DOING ANYTHING

**NEVER run `tofu plan`, `tofu apply`, or ANY OpenTofu/Terraform command from Mello or against production.**
OpenTofu commands ONLY run on a NEW TESTING server instance. Mistakes here change live serverless GPU deployments and cannot be easily reversed. Edit `.tf` files, commit via git flow, apply ONLY on a new testing server.

---

## CONTEXT

**We are the Mello Admin Panel Team.** Branch: `testing-mello-admin-panel-team`.

**Production:** aiworkshop.art runs on Verda CPU instance (see `VERDA_PUBLIC_IP` in `.env`), NOT Mello.

**SSH (temporary):** `ssh dev@100.89.38.43` (Tailscale IP). Root on public IP broken after reprovision — will be fixed when instance is re-provisioned or keys restored.

---

## IMMEDIATE PRIORITY

### 1. Inference regression — ALL workflows broken (#101)

**Status:** Root cause still UNKNOWN. QM error logging (#48) deployed but no new job triggered yet to capture actual error.

**Timeline:**
- Feb 15 18:20 UTC — last successful inference (Flux Klein, 2 images)
- Feb 16 04:57 UTC — first failure, `status=error` on serverless
- No code drift, no container restarts between success and failure

**OpenTofu drift audit (#54) found NO deployment config drift** — .tf matches live. The regression is NOT caused by a changed startup command, scaling, or mount config.

**Drift audit DID find these inconsistencies (not causing regression but need fixing):**
- `--output-directory /mnt/sfs/outputs` missing from 3 of 4 deployments (only H200-spot has it)
- Healthcheck path `/` (should be `/system_stats`)
- Queue load threshold `2` (documented as `1`)

**Next step:** Trigger a test job to capture actual ComfyUI execution error via new QM logging.

### 2. OpenTofu IaC — first apply on TESTING server (#54)

**DONE:**
- [x] OpenTofu v1.11.5 installed on Mello
- [x] `infrastructure/` dir created: providers.tf, variables.tf, containers.tf
- [x] `verda-cloud/verda` v1.1.1 provider — supports `verda_container`
- [x] All 4 live deployments imported into tofu state
- [x] `tofu plan` = 0 real drift (confirms .tf matches production)
- [x] GH #54 created with full drift audit
- [x] CLAUDE.md updated: IaC debugging + deployment change workflow
- [x] PRs #53, #55 merged

**TODO:**
- [ ] First `tofu apply` on TESTING server (NOT production)
- [ ] Fix: add `--output-directory /mnt/sfs/outputs` to 3 missing deployments
- [ ] Fix: healthcheck `/` → `/system_stats`
- [ ] Set up remote state backend (currently local — fragile)

**Credentials:** `VERDA_CLIENT_ID` + `VERDA_CLIENT_SECRET` from `/home/dev/comfymulti-scripts/.env`
**SFS IDs:** PROD `be539393-...` / CLONE `fd7efb9e-...`

---

## MONITORING STACK (#106) + SUBDOMAINS (#109)

All live. Use `/verda-monitoring-check` to verify.

| Tool | Port | Access |
|------|------|--------|
| Prometheus | :9090 | https://prometheus.aiworkshop.art (basic auth) |
| Grafana | :3001 | https://grafana.aiworkshop.art (admin login) |
| Loki | :3100 | via Grafana or SSH |
| cAdvisor | :8081 | via Prometheus |
| Promtail | :9080 | ships Docker logs → Loki |
| Portainer | :9443 | https://portainer.aiworkshop.art |

**12 skills:** `/verda-ssh`, `/verda-status`, `/verda-logs`, `/verda-containers`, `/verda-terraform`, `/verda-open-tofu`, `/verda-prometheus`, `/verda-dry`, `/verda-loki`, `/verda-grafana`, `/verda-monitoring-check`, `/verda-debug-containers`

---

## KEY RESEARCH FINDINGS

**ComfyUI folder_paths.py:**
- `extra_config.py:load_extra_path_config()` iterates yaml keys
- Each key passed to `folder_paths.add_model_folder_path(key, path)`
- `map_legacy()` only maps `unet`→`diffusion_models` and `clip`→`text_encoders`
- Yaml key IS the folder type verbatim — no other aliasing

**Verda SDK:**
- `update_deployment(name, deployment)` takes a full `Deployment` object, NOT kwargs
- No container logs via SDK or API; no exec/shell into containers
- `get_deployments()` returns all 4 deployments, `get_deployment_scaling_options(name)` for scaling
- Deployment object has no `id` field — import by name works

**OpenTofu `verda_container` schema:**
- `entrypoint_overrides`: `enabled`, `entrypoint` (list), `cmd` (list) — live uses exec-style (no shell)
- `volume_mounts`: `type` (scratch/memory/secret/shared), `mount_path`, `volume_id` (for shared)
- `scaling`: `deadline_seconds` exists alongside `queue_message_ttl_seconds`
- SFS has NO provider resource (`verda_sfs` doesn't exist)

---

## GITHUB ISSUES

- **#101** — Yaml key fix applied. Inference BROKEN — regression. No deployment drift found via tofu.
- **#103** — SFS mount resolved. Instance sees SFS.
- **#106** — [x] Monitoring stack complete.
- **#109** — [x] SSL certs complete.
- **#43** — Fixed (container restart). Close after confirming inference works.
- **#44** — OPEN. GPU progress banner for serverless mode.
- **#45** — OPEN. Cookie-based auth persistence.
- **#46** — OPEN. Cold start silent failure UX.
- **#48** — [x] QM error logging deployed. Needs image rebuild to persist.
- **#54** — IN PROGRESS. OpenTofu IaC for Verda serverless. Import done, apply on testing next.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` top section
- [ ] Run `/verda-monitoring-check` to verify stack is healthy
- [ ] Trigger test job to capture inference error via new QM logging (#48)
- [ ] After error captured: diagnose root cause of inference regression (#101)
- [ ] First `tofu apply` on testing server (#54)
- [ ] Fix 3 deployments missing `--output-directory` via .tf change
- [ ] After inference fixed: close #43, work on #44/#45/#46
