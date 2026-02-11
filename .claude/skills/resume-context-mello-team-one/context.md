# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** Core stack is RUNNING (Redis, QM, admin, 20 frontends all healthy).
Nginx container is FAILING — can't resolve upstream user containers. No SSL cert yet.

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~120 lines) - Priority tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## IMMEDIATE NEXT STEPS

1. **Fix nginx upstream resolution** — nginx container not on Docker network, can't resolve `user001:8188`. Check `nginx/` config and docker-compose.yml network settings.
2. **Get SSL cert** — `certbot certonly --standalone -d aiworkshop.art` (stop nginx first so certbot can bind port 80)
3. **Investigate .env variable warnings** — `y1w`, `HUFr7` etc. suggest unescaped `$` in values on server (#7)
4. **Test end-to-end** — browser → nginx → frontend → QM → serverless
5. **Clean up old Docker images** — ~80GB of stale per-user images from earlier builds
6. **Run setup-monitoring.sh** — Prometheus, Grafana, Loki, Promtail, cAdvisor

---

## KEY FILES

| File | Purpose |
|------|---------|
| `./CLAUDE.md` | Project guide, architecture, gotchas |
| `.claude/agent_docs/progress-mello-team-one-dev.md` | Tasks + session progress |
| `.claude/agent_docs/progress-all-teams.md` | All-teams commit log |
| `docker-compose.yml` | Main compose — check nginx service + network config |
| `nginx/nginx.conf` | Nginx config — upstream resolution issue here |
| `SERVERLESS_UPDATE.md` | Serverless setup docs (endpoints, API keys, GPU options) |

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
