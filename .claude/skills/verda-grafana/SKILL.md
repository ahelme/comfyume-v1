---
description: Grafana dashboard management on Verda.
user-invocable: true
---

Grafana dashboard management on Verda.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP
**Port:** 3001
**Config:** `/etc/grafana/grafana.ini`
**Service:** `systemctl {start|stop|restart|status} grafana-server`
**Default creds:** admin/admin (change on first login)
**Access:** `http://$VERDA_IP:3001` or `http://100.89.38.43:3001` (Tailscale)
**Future:** `https://grafana.aiworkshop.art` (once SSL configured)

## Common Operations

```bash
# Check health
ssh root@$VERDA_IP "curl -s localhost:3001/api/health"

# List data sources
ssh root@$VERDA_IP "curl -s http://admin:admin@localhost:3001/api/datasources | python3 -m json.tool"

# List dashboards
ssh root@$VERDA_IP "curl -s http://admin:admin@localhost:3001/api/search | python3 -m json.tool"

# Add Prometheus data source
ssh root@$VERDA_IP "curl -s -X POST -H 'Content-Type: application/json' -d '{\"name\":\"Prometheus\",\"type\":\"prometheus\",\"url\":\"http://localhost:9090\",\"access\":\"proxy\",\"isDefault\":true}' http://admin:admin@localhost:3001/api/datasources"

# Add Loki data source
ssh root@$VERDA_IP "curl -s -X POST -H 'Content-Type: application/json' -d '{\"name\":\"Loki\",\"type\":\"loki\",\"url\":\"http://localhost:3100\",\"access\":\"proxy\"}' http://admin:admin@localhost:3001/api/datasources"
```

## Installed Dashboards

| Dashboard | ID | Purpose |
|-----------|-----|---------|
| Docker Container Dashboard | 15331 | Container overview, CPU, memory, network |
| Container Resources | 14678 | Detailed resource usage per container |
| NVIDIA DCGM Exporter | 12239 | GPU metrics (when GPU instances run) |

## Import Dashboard via API

```bash
# Download dashboard JSON from grafana.com then import
ssh root@$VERDA_IP "curl -s https://grafana.com/api/dashboards/15331/revisions/latest/download | curl -s -X POST -H 'Content-Type: application/json' -d @- http://admin:admin@localhost:3001/api/dashboards/import"
```

## Change Admin Password

```bash
ssh root@$VERDA_IP "curl -s -X PUT -H 'Content-Type: application/json' -d '{\"oldPassword\":\"admin\",\"newPassword\":\"NEW_PASSWORD\"}' http://admin:admin@localhost:3001/api/user/password"
```

If $ARGUMENTS provided, treat as a Grafana operation or question.
