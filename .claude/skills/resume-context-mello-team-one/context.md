# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** PRODUCTION LIVE! Full stack running and serving HTTPS.
All containers healthy (Redis, QM, admin, nginx, 20 frontends).
SSL cert valid (expires 2026-05-12). Serverless GPU inference TESTED AND WORKING.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) - Priority tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## IMMEDIATE NEXT STEPS

1. **Rebuild nginx image on server** — dynamic DNS fix (93bf1a1) is committed but server still runs old image. Run: `cd /home/dev/comfyume-v1 && docker compose build nginx && docker compose --profile container-nginx up -d nginx`
2. **Investigate .env variable warnings** — `y1w`, `HUFr7` etc. suggest unescaped `$` in values on server (#7)
3. **Clean up old Docker images** — ~80GB of stale per-user images from earlier builds
4. **Run setup-monitoring.sh** — Prometheus, Grafana, Loki, Promtail, cAdvisor
5. **Workshop prep** — test all 20 user slots, verify workflows load, check magic link URLs

---

## KEY FILES

| File | Purpose |
|------|---------|
| `./CLAUDE.md` | Project guide, architecture, gotchas |
| `.claude/agent_docs/progress-mello-team-one-dev.md` | Tasks + session progress |
| `.claude/agent_docs/progress-all-teams.md` | All-teams commit log |
| `docker-compose.yml` | Main compose — nginx, redis, QM, admin, worker |
| `nginx/docker-entrypoint.sh` | Generates user routing config (dynamic DNS resolver) |
| `nginx/nginx.conf` | Nginx config — SSL, auth, proxy rules |

---

## TEAM COORDINATION

**GitHub Issues:** https://github.com/ahelme/comfyume-v1/issues
**Private Scripts:** https://github.com/ahelme/comfymulti-scripts

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` on both repos
- [ ] Can you SSH to Verda? `ssh root@65.108.33.101`
- [ ] Read `.claude/agent_docs/progress-mello-team-one-dev.md` top section
- [ ] Check container health: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | sort'`
- [ ] Discuss priorities with user
