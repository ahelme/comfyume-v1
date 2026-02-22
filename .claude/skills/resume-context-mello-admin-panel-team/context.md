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
- **Feature branch:** `testing-mello-admin-panel-team-2026-02-22`
- **Deploy branch:** `testing-009` (shared — ALL teams merge here before deploying)
- **PRs merged:** #76 (isolate mode), #84 (cookie auth + assets fix)

**Production:** aiworkshop.art on Verda (quiet-city, 65.108.33.101) — DO NOT TOUCH.
**Testing:** anegg.app on Verda (intelligent-rain-shrinks, 65.108.33.80) — all teams work here.

**SSH (production):** `ssh dev@100.89.38.43` (Tailscale IP).
**SSH (testing):** `ssh root@65.108.33.80` (public IP).

**All teams are currently working on the testing instance (anegg.app). Do NOT deploy to production.**

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- See CLAUDE.md "Deploying to Testing-009" for full workflow
- **CRITICAL: use `docker compose up -d` after build, NOT `docker compose restart`** — restart keeps the old image

---

## CURRENT STATE

### Completed This Session
- **#45 — Cookie-based auth persistence** — DEPLOYED to anegg.app
  - nginx `map` checks `comfyume_session` cookie against `AUTH_COOKIE_SECRET` env var
  - Match = bypass Basic Auth. After successful auth, Set-Cookie persists 24h
  - HttpOnly, Secure, SameSite=Strict. Disabled by default (set env var to enable)
  - Files: `nginx/nginx.conf`, `nginx/docker-entrypoint.sh`, `docker-compose.yml`, `.env.example`

- **#78 — Assets auth bypass** — DEPLOYED to anegg.app
  - Regex location `auth_basic off` for `/userXXX/assets/*` — fixes manifest.json 401
  - CSS MIME issue noted as upstream ComfyUI behavior (cosmetic only)
  - Gotcha: nginx doesn't like `\d{3}` — use `[0-9][0-9][0-9]`

- **#85 — Job timeout knob** — GH ISSUE CREATED, PLAN APPROVED, NOT YET IMPLEMENTED
  - Plan file: `.claude/plans/silly-purring-mist.md`

### Previously Completed
- **#75** — Isolate mode toggle (PR #76 merged to main)
- **#76** — Admin toggles PR (merged)
- **#84** — Cookie auth + assets PR (merged)
- CLAUDE.md: docker restart gotcha added

### Infrastructure
- All containers healthy: nginx, redis, QM, admin, user001-005
- SSL cert for anegg.app (expires 2026-05-18)
- Cookie auth active with `AUTH_COOKIE_SECRET` in .env
- Mello-team-one pushed SFS-based delivery (#82) — QM refactored with two paths

---

## GITHUB ISSUES

- **#85** — Job timeout knob. Plan approved, implementation ready. See plan file.
- **#75** — Isolate mode toggle. COMPLETE. PR #76 merged.
- **#78** — Assets auth bypass. COMPLETE (manifest fix). CSS MIME is upstream.
- **#45** — Cookie auth persistence. COMPLETE. PR #84 merged.
- **#79** — Favicon progress animation 404 (non-critical, not started)
- **#80** — Userdata API 404 for subgraphs/templates (non-critical, expected on fresh install)
- **#46** — Cold start silent failure UX (not started)
- **#82** — SFS-based result delivery (mello-team-one, merged to testing-009)

---

## NEXT STEPS

### Immediate — #85 Job Timeout Knob
- [ ] Implement plan from `.claude/plans/silly-purring-mist.md`
- [ ] QM main.py: module var `serverless_max_wait`, GET/POST `/api/admin/timeout`, wire both delivery paths
- [ ] Admin dashboard: range slider (60-1800s) in header, localStorage + QM sync
- [ ] Deploy to testing-009, verify slider works
- **Key insight:** reuse existing `sfs_max_wait` from config.py as default. One knob controls both SFS and HTTP delivery paths.

### Admin Panel Enhancements
- [ ] **#79** — Favicon progress animation 404
- [ ] **#80** — Userdata API 404
- [ ] **#46** — Cold start silent failure UX
- [ ] Per-feature isolate toggles (granular, beyond current master toggle)

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` (Report 19)
- [ ] Verify testing-009 is running: `ssh root@65.108.33.80 'docker ps --format "{{.Names}}\t{{.Status}}" | sort'`
- [ ] If containers down: `cd /home/dev/comfyume-v1 && docker compose up -d`
- [ ] Read plan file `.claude/plans/silly-purring-mist.md` — implement #85
- [ ] Continue with next steps above
