---
description: Prometheus monitoring on Verda — metrics collection and querying.
user-invocable: true
---

Prometheus monitoring on Verda — metrics collection and querying.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP
**Port:** 9090
**Config:** `/etc/prometheus/prometheus.yml`
**Data:** `/var/lib/prometheus/` (7-day retention)
**Service:** `systemctl {start|stop|restart|status} prometheus`

## Common Operations

```bash
# Check targets
ssh root@$VERDA_IP "curl -s localhost:9090/api/v1/targets | python3 -m json.tool | head -30"

# Query a metric (PromQL via API)
ssh root@$VERDA_IP "curl -s 'localhost:9090/api/v1/query?query=up' | python3 -m json.tool"

# Check config
ssh root@$VERDA_IP "cat /etc/prometheus/prometheus.yml"

# Reload config without restart
ssh root@$VERDA_IP "curl -X POST localhost:9090/-/reload"

# Check storage usage
ssh root@$VERDA_IP "du -sh /var/lib/prometheus/"
```

## Useful PromQL Queries

```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total{name=~"comfy-.*"}[5m])

# Container memory usage
container_memory_usage_bytes{name=~"comfy-.*"}

# Container network I/O
rate(container_network_receive_bytes_total{name=~"comfy-.*"}[5m])

# Filesystem usage (for SFS/block storage debugging)
container_fs_usage_bytes{name=~"comfy-.*"}

# Container restart count
container_start_time_seconds{name=~"comfy-.*"}

# All targets up/down
up
```

## Scrape Targets

- `prometheus` (self, localhost:9090)
- `cadvisor` (Docker metrics, localhost:8081)

To add more targets, edit `/etc/prometheus/prometheus.yml` and reload.

If $ARGUMENTS provided, treat as a PromQL query or Prometheus operation.
