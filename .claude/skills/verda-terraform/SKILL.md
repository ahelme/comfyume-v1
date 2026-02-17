---
description: Terraform/IaC guide for managing Verda infrastructure.
user-invocable: true
---

Terraform/IaC guide for managing Verda infrastructure.

**Docs:** https://docs.verda.com/infrastructure-as-code/terraform
**Provider:** `verda-cloud/verda` v1.1.1 (Terraform Registry)
**Tool:** OpenTofu v1.11.5 (`tofu` command)

## Where Things Live

| Location | What | Notes |
|----------|------|-------|
| `infrastructure/` (repo) | `.tf` files (committed) | Source of truth for all deployments |
| `infrastructure/.terraform.lock.hcl` | Provider version lock (committed) | Pins exact provider checksums |
| `infrastructure/terraform.tfvars` | Secrets (gitignored) | Copy from `terraform.tfvars.example` |
| Verda server `/root/.bashrc` | `VERDA_CLIENT_ID`, `VERDA_CLIENT_SECRET` | Also needed locally as env vars |

## Local Setup

```bash
# 1. Set credentials (get from Verda console > API Keys)
export VERDA_CLIENT_ID="your-client-id"
export VERDA_CLIENT_SECRET="your-client-secret"

# 2. Copy example vars and fill in values
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
# Edit terraform.tfvars — set sfs_volume_id, hf_token, deployment toggles

# 3. Init (downloads provider)
cd infrastructure && tofu init

# 4. Plan (preview changes — ALWAYS do this first)
tofu plan

# 5. Apply (make changes — review plan output first)
tofu apply
```

## Provider Config

```hcl
terraform {
  required_version = ">= 1.11.0"
  required_providers {
    verda = {
      source  = "verda-cloud/verda"
      version = "~> 1.1"
    }
  }
}
provider "verda" {}  # reads VERDA_CLIENT_ID + VERDA_CLIENT_SECRET env vars
```

## Supported Resources

| Resource | Purpose |
|----------|---------|
| `verda_container` | Serverless GPU deployments (H200/B300) |
| `verda_instance` | CPU/GPU instances |
| `verda_volume` | Block storage volumes |
| `verda_ssh_key` | SSH keys |
| `verda_startup_script` | Instance startup scripts |
| `verda_serverless_job` | Batch GPU jobs |
| `verda_container_registry_credentials` | Private registry auth |

**NOT managed by provider:** SFS (shared filesystem) — must use Verda console/API.

## Common Operations

```bash
cd infrastructure

# Preview changes (ALWAYS before apply)
tofu plan

# Apply changes
tofu apply

# Show current state
tofu state list
tofu state show verda_container.worker["h200-spot"]

# Import existing deployment into state
tofu import 'verda_container.worker["h200-spot"]' <deployment-id>

# Detect drift (compare actual vs desired)
tofu plan  # any unexpected changes = drift

# Destroy a specific deployment
tofu destroy -target='verda_container.worker["h200-spot"]'
```

## Container Schema (key attributes)

```hcl
resource "verda_container" "example" {
  name    = "deployment-name"
  is_spot = true

  compute = { name = "H200 SXM5 141GB", size = 1 }

  scaling = {
    min_replica_count = 0
    max_replica_count = 10
    concurrent_requests_per_replica = 1
    queue_message_ttl_seconds = 36000
    queue_load = { threshold = 1 }
    scale_up_policy = { delay_seconds = 0 }
    scale_down_policy = { delay_seconds = 300 }
  }

  containers = [{
    image = "ghcr.io/ahelme/comfyume-worker:v0.11.0"
    exposed_port = 8188
    entrypoint_overrides = {
      enabled = true
      entrypoint = ["/bin/sh", "-c"]
      cmd = ["python3 main.py --listen 0.0.0.0 --port 8188"]
    }
    healthcheck = { enabled = "true", path = "/system_stats", port = "8188" }
    env = [{ name = "KEY", type = "plain", value_or_reference_to_secret = "val" }]
    volume_mounts = [{ type = "shared", volume_id = "vol-id", mount_path = "/mnt/sfs" }]
  }]
}
```

## Auth

Env vars required:
- `VERDA_CLIENT_ID` — from Verda console > API Keys
- `VERDA_CLIENT_SECRET` — from Verda console > API Keys

On Verda server: set in `/root/.bashrc`
Locally: export before running `tofu` commands

If $ARGUMENTS provided, treat as a specific Terraform question or operation.
Otherwise show this reference.
