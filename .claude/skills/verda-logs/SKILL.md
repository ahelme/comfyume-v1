---
description: Fetch logs for a service on Verda. Argument: service name (or "all" for summary).
user-invocable: true
---

Fetch logs for a service on Verda. Argument: service name (or "all" for summary).

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP

**Docker containers** (use `docker logs`):
- nginx, queue-manager, admin, redis, user001-user020, cadvisor, portainer_edge_agent

**Systemd services** (use `journalctl -u`):
- prometheus, loki, grafana-server, promtail

**Usage:**
- `$ARGUMENTS` = service name → fetch last 50 lines
- No arguments → show last 10 lines from queue-manager + nginx + admin (most useful)

**Commands:**
- Docker: `ssh root@$VERDA_IP "docker logs comfy-$ARGUMENTS --tail 50 2>&1"`
- Systemd: `ssh root@$VERDA_IP "journalctl -u $ARGUMENTS --no-pager -n 50"`

If the service name contains "user", prefix with `comfy-` for Docker.
If the service is prometheus/loki/grafana-server/promtail, use journalctl.
Otherwise try Docker first, fall back to journalctl.

Show output to the user with clear headers.
