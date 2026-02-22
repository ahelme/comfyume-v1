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
- **PR:** #76 (open, targeting main)

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

**Workflow:**
1. Push changes to `testing-mello-admin-panel-team-2026-02-22`
2. Merge into `testing-009`: `git checkout testing-009 && git merge <branch> && git push`
3. On server: `cd /home/dev/comfyume-v1 && git pull origin testing-009`
4. Rebuild/restart as needed: `docker compose build admin && docker compose up -d admin`

---

## CURRENT STATE

### What Was Built This Session (#75)

**Isolate mode toggle** — admin panel header toggle for fault isolation:
- OFF (default) = normal operation, everything works
- ON = all `/api/*` endpoints return 503 (isolation mode for debugging)
- Dashboard UI, `/health`, and `/api/admin/isolate` always accessible
- Backend: `GET/POST /api/admin/isolate`, middleware gate, `ADMIN_ISOLATE_MODE` env var
- Frontend: localStorage persistence (`admin_isolate_mode`) + backend sync on load

**GPU overlay mode toggle** — also in admin header:
- Sets `localStorage.setItem('gpu_overlay_mode', 'admin'|'user')`
- For mello-team-one's gpu_overlay extension (admin shows more detail)

**Docs updated:**
- CLAUDE.md: isolate mode docs, Quick Links with anegg.app, admin=operator not instructor
- README.md: serverless timeout layers table (4 layers, only Layer 2 configurable)
- All 5 team progress files: testing instance details at top
- All 5 handover skills: full-session GH issue analysis step added

### Infrastructure (unchanged from previous session)
- All containers healthy: nginx, redis, QM, admin, user001-005
- SSL cert for anegg.app (expires 2026-05-18)
- Credentials: per-user strong passwords (21 entries in htpasswd)
- `comfyume-test-vca-ftv-h200-spot` deployed, mounting CLONE_SFS

---

## GITHUB ISSUES

- **#75** — Isolate mode toggle. IMPLEMENTED and deployed. PR #76 open.
- **#78** — Static assets MIME type + manifest 401 (non-critical, nginx fix needed)
- **#79** — Favicon progress animation 404 (non-critical)
- **#80** — Userdata API 404 for subgraphs/templates (non-critical, normal for fresh install)
- **#72** — Environment-isolated serverless. Steps 1-7 done. Step 8 (inference testing) owned by mello-team-one.
- **#66** — SFS-based result delivery architecture. Still needed for production.
- **#45** — Cookie-based auth persistence (not started)
- **#46** — Cold start silent failure UX (not started)

---

## NEXT STEPS

### Immediate
- [ ] Merge PR #76 to main (user approved — safe to merge)
- [ ] Fix non-critical frontend issues (#78, #79, #80) — nginx MIME types + auth
- [ ] Add job timeout knob to admin panel (Layer 2: poll_serverless_history max_wait)

### Admin Panel Enhancements
- [ ] Per-feature isolate toggles (currently master on/off — future: granular)
- [ ] **#45** — Cookie-based auth persistence
- [ ] **#46** — Cold start silent failure UX

### Architecture (#66) — SFS-Based Result Delivery (Production)
- QM watches SFS filesystem instead of polling `/history/{id}` over HTTP
- Workers = vanilla ComfyUI (zero custom code on serverless)

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` (Report 18)
- [ ] Verify testing-009 is running: `ssh root@65.108.33.80 'docker ps --format "{{.Names}}\t{{.Status}}" | sort'`
- [ ] If containers down: `cd /home/dev/comfyume-v1 && docker compose up -d`
- [ ] Check PR #76 status — merge if approved
- [ ] Continue with next steps above
