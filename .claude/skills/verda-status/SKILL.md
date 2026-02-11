---
description: Full status check of all Verda services. Run ALL of these via SSH to root@$VERDA_IP:
user-invocable: true
---

Full status check of all Verda services.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

Run ALL of these via SSH to root@$VERDA_IP:

1. **System:** `uptime && free -h | head -2 && df -h / /mnt/models-block-storage`
2. **Docker containers:** `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | sort`
3. **Monitoring services:** `systemctl is-active prometheus loki grafana-server promtail 2>/dev/null; docker ps --filter name=cadvisor --format '{{.Names}}: {{.Status}}'`
4. **Ports in use:** `ss -tlnp | grep -E ':(9090|3100|3001|8080|9080) '`
5. **Serverless status:** `python3 -c "
import os
from verda import VerdaClient
client = VerdaClient(os.environ.get('VERDA_CLIENT_ID'), os.environ.get('VERDA_CLIENT_SECRET'))
# List serverless deployments if the SDK supports it
print('Verda SDK connected')
" 2>&1 || echo "Verda SDK not configured"`

Present results in a clear summary table to the user.
