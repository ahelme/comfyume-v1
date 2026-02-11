---
description: Manage Verda serverless containers. Uses the Verda Python SDK on the Verda server.
user-invocable: true
---

Manage Verda serverless containers. Uses the Verda Python SDK on the Verda server.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP
**Docs:** https://docs.verda.com/containers/overview
**SDK:** https://github.com/verda-cloud/sdk-python

**Current serverless endpoints (from .env):**
- H200 Spot: `https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot`
- H200 On-Demand: `https://containers.datacrunch.io/comfyume-vca-ftv-h200-on-demand`
- B300 Spot: `https://containers.datacrunch.io/comfyume-vca-ftv-b300-spot`
- B300 On-Demand: `https://containers.datacrunch.io/comfyume-vca-ftv-b300-on-demand`
- Active: `SERVERLESS_ACTIVE=h200-spot`
- API Key: `SERVERLESS_API_KEY` in .env

**Operations (via SSH + Python):**

1. **List deployments:**
```bash
ssh root@$VERDA_IP 'source /root/.bashrc && python3 << PYEOF
import os
from verda import VerdaClient
client = VerdaClient(os.environ["VERDA_CLIENT_ID"], os.environ["VERDA_CLIENT_SECRET"])
for d in client.containers.get_deployments():
    c = d.containers[0]
    eo = c.entrypoint_overrides
    print(d.name + ": " + str(eo.cmd)[:100])
PYEOF'
```

2. **Check container health:** Call the endpoint directly:
```bash
ssh root@$VERDA_IP "curl -s -H 'Authorization: Bearer \$SERVERLESS_API_KEY' https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/health 2>&1 || echo 'No health endpoint'"
```

3. **View container logs:** Check Verda console or use SDK if supported.

4. **OpenTofu management:** See `/verda-terraform` or `/verda-open-tofu` for IaC-based container management.

If $ARGUMENTS is provided, treat it as a specific operation (list, health, logs, restart).
Otherwise show current deployment status.
