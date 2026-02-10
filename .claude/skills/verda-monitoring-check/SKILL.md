---
description: Quick health check of the full monitoring stack on Verda.
user-invocable: true
---

Quick health check of the full monitoring stack on Verda.

Run ALL of these via SSH to root@95.216.229.236 in a single command:

```bash
ssh root@95.216.229.236 'echo "=== PROMETHEUS ===" && curl -sf localhost:9090/-/healthy && echo " OK" || echo " FAIL"; echo "=== LOKI ===" && curl -sf localhost:3100/ready && echo " OK" || echo " FAIL"; echo "=== GRAFANA ===" && curl -sf localhost:3001/api/health && echo "" || echo " FAIL"; echo "=== CADVISOR ===" && docker ps --filter name=cadvisor --format "{{.Status}}" || echo "NOT RUNNING"; echo "=== PROMTAIL ===" && systemctl is-active promtail; echo "=== PROMETHEUS TARGETS ===" && curl -s localhost:9090/api/v1/targets | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\"  {t[\"labels\"][\"job\"]}: {t[\"health\"]}\") for t in d[\"data\"][\"activeTargets\"]]" 2>/dev/null || echo "  Cannot fetch targets"; echo "=== LOKI LOG INGESTION ===" && curl -s localhost:3100/loki/api/v1/label/container_name/values | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"  Containers indexed: {len(d.get(\\\"data\\\",[]))}\")" 2>/dev/null || echo "  Cannot query labels"; echo "=== DISK ===" && du -sh /var/lib/prometheus/ /tmp/loki/ /var/lib/grafana/ 2>/dev/null'
```

Present results as a clean status table:

| Service | Status |
|---------|--------|
| Prometheus (:9090) | OK/FAIL |
| Loki (:3100) | OK/FAIL |
| Grafana (:3001) | OK/FAIL |
| cAdvisor (:8081) | running/stopped |
| Promtail | active/inactive |

Also show Prometheus scrape targets and monitoring data disk usage.
