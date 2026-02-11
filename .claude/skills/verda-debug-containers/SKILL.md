---
description: Comprehensive container debugging playbook for ComfyuME on Verda.
user-invocable: true
---

Comprehensive container debugging playbook for ComfyuME on Verda.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP
**Issues:** #101 (model paths), #103 (SFS architecture)

Use this when debugging container issues — especially model loading, SFS mounts, and serverless inference.

## Step 1: Check Container Health

```bash
ssh root@$VERDA_IP "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'unhealthy|Restarting|Exited' || echo 'All containers healthy'"
```

## Step 2: Check Model Paths & Mounts

```bash
# Volume mounts for a specific container
ssh root@$VERDA_IP "docker inspect comfy-queue-manager --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{println}}{{end}}'"

# Check SFS/block storage mounts
ssh root@$VERDA_IP "mount | grep -E '/mnt/sfs|/mnt/models' && ls /mnt/models-block-storage/models/shared/ 2>/dev/null | head -10"

# Check model files exist
ssh root@$VERDA_IP "ls -la /mnt/models-block-storage/models/shared/latent_upscale_models/ 2>/dev/null && ls -la /mnt/models-block-storage/models/shared/upscale_models/ 2>/dev/null"

# Check extra_model_paths.yaml
ssh root@$VERDA_IP "cat /mnt/models-block-storage/extra_model_paths.yaml 2>/dev/null || echo 'No yaml on block storage'"
```

## Step 3: Query Loki for Errors (if Loki running)

```bash
# Model path errors
ssh root@$VERDA_IP "curl -s -G 'localhost:3100/loki/api/v1/query_range' --data-urlencode 'query={container_name=~\"comfy-.*\"} |~ \"No such file|symlink|model.*not found|upscale_models|latent_upscale\"' --data-urlencode 'limit=20' --data-urlencode 'start=$(date -d '1 hour ago' +%s)000000000' | python3 -m json.tool | head -50"

# Queue manager serverless errors
ssh root@$VERDA_IP "curl -s -G 'localhost:3100/loki/api/v1/query_range' --data-urlencode 'query={container_name=\"comfy-queue-manager\"} |= \"serverless\"' --data-urlencode 'limit=20' | python3 -m json.tool | head -50"
```

## Step 4: Check Prometheus Container Metrics (if Prometheus running)

```bash
# Container filesystem usage (detect empty mounts)
ssh root@$VERDA_IP "curl -s 'localhost:9090/api/v1/query?query=container_fs_usage_bytes{name=~\"comfy-.*\"}' | python3 -m json.tool | head -30"

# Container restart count
ssh root@$VERDA_IP "curl -s 'localhost:9090/api/v1/query?query=container_start_time_seconds{name=~\"comfy-.*\"}' | python3 -m json.tool | head -30"
```

## Step 5: Check Serverless Container (via Verda SDK)

```bash
# List deployments with startup commands
ssh root@$VERDA_IP 'source /root/.bashrc && python3 << PYEOF
import os
from verda import VerdaClient
client = VerdaClient(os.environ["VERDA_CLIENT_ID"], os.environ["VERDA_CLIENT_SECRET"])
for d in client.containers.get_deployments():
    c = d.containers[0]
    eo = c.entrypoint_overrides
    print(d.name)
    print("  cmd: " + str(eo.cmd))
    print("  mounts: " + str(c.volume_mounts))
    print("  env: " + str(c.env))
    print()
PYEOF'

# Test serverless endpoint directly
ssh root@$VERDA_IP "curl -s -w '\nHTTP %{http_code}\n' -H 'Authorization: Bearer \$(grep SERVERLESS_API_KEY /home/dev/comfyume/.env | cut -d= -f2)' https://containers.datacrunch.io/comfyume-vca-ftv-h200-spot/health 2>&1"
```

**Verda SDK key methods:**
- `client.containers.get_deployments()` — list all deployments
- `client.containers.get_deployment_by_name("name")` — get specific deployment
- `client.containers.update_deployment("name", ...)` — update config
- `client.containers.get_deployment_status("name")` — check status
- `client.containers.get_deployment_replicas("name")` — check replicas
- `client.containers.get_deployment_environment_variables("name")` — get env vars

**Important:** Env vars require `source /root/.bashrc` before SDK calls.

## Step 6: Docker Logs (Recent Errors)

```bash
# Queue manager errors (last 50 lines)
ssh root@$VERDA_IP "docker logs comfy-queue-manager --tail 50 2>&1 | grep -iE 'error|fail|exception|timeout'"

# Nginx errors
ssh root@$VERDA_IP "docker logs comfy-nginx --tail 50 2>&1 | grep -iE '502|504|error'"

# Admin panel errors
ssh root@$VERDA_IP "docker logs comfy-admin --tail 30 2>&1 | grep -iE 'error|traceback'"
```

## Known Issues Reference

- **#101**: yaml key `latent_upscale_models` maps to wrong folder type `upscale_models` on REAL SFS
- **#103**: REAL SFS (NFS) accessible from serverless container but NOT from CPU instance; block storage renamed to `/mnt/models-block-storage`
- **Root cause**: Container logs show `Adding extra search path upscale_models /mnt/sfs/models/shared/latent_upscale_models`

If $ARGUMENTS provided, focus on that specific area. Otherwise run the full playbook.
