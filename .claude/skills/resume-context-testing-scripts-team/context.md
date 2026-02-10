# CLAUDE RESUME - COMFYUME (TESTING SCRIPTS TEAM)

**DATE**: 2026-02-09

---

## CONTEXT

**We are the Testing Scripts Team.** Branch: `testing-scripts-team-2`.

**Production:** aiworkshop.art runs on Verda CPU instance. Inference is serverless (DataCrunch H200/B300). Mello is staging/backup only (containers removed).

---

## RECENT WORK (this session — 2026-02-09)

### Issue #111 — File sharing + favicon (PR #112 MERGED)
- Bidirectional file sharing on mello (host nginx config, NOT in repo):
  - `upload.aiworkshop.art` — dedicated subdomain, root = upload page
  - `comfy.ahelme.net/upload` — same via mello domain
  - Cookie-based login form at `/login` (browser saves password, 30-day cookie)
  - `/mello-share/` (mello→mac), `/mac-share/` (mac→mello, WebDAV PUT)
  - Drag & drop + Cmd+V paste support on upload page
- Favicon: official ComfyUI logo (yellow C on blue)
  - Replaced in admin dashboard (data URI), nginx (inline SVG), static files
  - Source: Dashboard Icons (CC BY 4.0)

### Mello host files (NOT in repo)
- `/etc/nginx/sites-enabled/upload.aiworkshop.art` — upload subdomain
- `/etc/nginx/sites-enabled/comfy.ahelme.net` — share locations + cookie map
- `/etc/nginx/share-htpasswd` — admin auth
- `/var/www/login.html`, `/var/www/upload.html` — login + upload pages
- `/var/www/mello-share/`, `/var/www/mac-share/` — share directories

---

## PENDING WORK

- [ ] Deploy favicon to Verda (steps in GH issue #111 comment)
  - `git pull`, `docker compose build admin`, update host nginx, reload
- [ ] Run test.sh on Verda app server to validate test scripts
- [ ] Close #71 after Hetzner downgrade (user handles manually)

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-testing-scripts-team-dev.md`** (top ~250 lines) - Recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## KEY FILES

| File | Purpose |
|------|---------|
| `./CLAUDE.md` | Project guide, architecture, gotchas |
| `.claude/agent_docs/progress-testing-scripts-team-dev.md` | Tasks + session progress |
| `.claude/agent_docs/progress-all-teams.md` | All-teams commit log |
| `scripts/test.sh` | Main integration test suite (10 sections) |
| `scripts/test-helpers.sh` | Shared test library |
| `scripts/test-serverless.sh` | Serverless E2E test |
| `scripts/test-connectivity.sh` | Network connectivity test |
| `admin/dashboard.html` | Admin panel (has favicon data URI) |
| `nginx/nginx.conf` | Docker nginx config (has favicon inline SVG) |

---

## TEAM COORDINATION

**GitHub Issues:** https://github.com/ahelme/comfyume/issues
**Completed:** #6 (test scripts), #22 (Phase 3 docs), #93 (download engine), #111 (file sharing + favicon)
**In Progress:** #71 (Mello cleanup — awaiting Hetzner downgrade)
**Branch:** `testing-scripts-team-2`

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` - any uncommitted changes?
- [ ] Read `.claude/agent_docs/progress-testing-scripts-team-dev.md` top section
- [ ] Check relevant GitHub issues for updates
- [ ] Discuss priorities with user
