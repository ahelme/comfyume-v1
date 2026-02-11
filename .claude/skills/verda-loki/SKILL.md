---
description: Loki log aggregation on Verda — query logs with LogQL.
user-invocable: true
---

Loki log aggregation on Verda — query logs with LogQL.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP
**Port:** 3100
**Config:** `/etc/loki/config.yml`
**Promtail config:** `/etc/promtail/config.yml`
**Retention:** 7 days
**Services:** `systemctl {start|stop|restart|status} loki` / `promtail`

## Common Operations

```bash
# Check Loki is ready
ssh root@$VERDA_IP "curl -s localhost:3100/ready"

# Check Promtail is shipping logs
ssh root@$VERDA_IP "systemctl is-active promtail && curl -sf localhost:9080/ready && echo 'Promtail: READY' || echo 'Promtail: NOT READY'"

# Query logs via LogQL API
ssh root@$VERDA_IP "curl -s -G 'localhost:3100/loki/api/v1/query_range' --data-urlencode 'query={container_name=~\"comfy-.*\"}' --data-urlencode 'limit=20' | python3 -m json.tool | head -50"

# Check available labels
ssh root@$VERDA_IP "curl -s localhost:3100/loki/api/v1/labels"

# Check storage usage (data stored in /tmp/loki, NOT /var/lib/loki)
ssh root@$VERDA_IP "du -sh /tmp/loki/"

# Check which containers are being indexed
ssh root@$VERDA_IP "curl -s localhost:3100/loki/api/v1/label/container_name/values | python3 -m json.tool"
```

## LogQL Query Syntax

```logql
# All logs from a specific container
{container_name="comfy-queue-manager"}

# Filter by text
{container_name="comfy-queue-manager"} |= "error"

# Exclude pattern
{container_name="comfy-nginx"} != "health"

# Regex filter
{container_name=~"comfy-user.*"} |~ "model|path|mount"

# Multiple filters (AND)
{container_name="comfy-queue-manager"} |= "serverless" |= "error"

# JSON parsing
{container_name="comfy-queue-manager"} | json | level="error"

# Rate of errors (for alerting)
rate({container_name=~"comfy-.*"} |= "error" [5m])
```

## Useful Queries for Our Issues

```logql
# Model path errors (#101)
{container_name=~"comfy-.*"} |~ "No such file|model.*not found|symlink"

# Queue manager serverless errors
{container_name="comfy-queue-manager"} |= "serverless" |= "error"

# Nginx auth/routing issues
{container_name="comfy-nginx"} |~ "401|403|502|504"

# All errors across all containers
{container_name=~"comfy-.*"} |= "error" != "favicon"
```

## Grafana Integration

View logs in Grafana at `http://localhost:3001` → Explore → Select Loki data source → Enter LogQL query.

If $ARGUMENTS provided, treat as a LogQL query or log operation.
