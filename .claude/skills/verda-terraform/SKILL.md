---
description: Terraform/IaC guide for managing Verda infrastructure.
user-invocable: true
---

Terraform/IaC guide for managing Verda infrastructure.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Docs:** https://docs.verda.com/infrastructure-as-code/terraform
**Provider:** `verda-cloud/verda` (Terraform Registry)
**Installed on:** root@$VERDA_IP (via OpenTofu, `tofu` command)

## Provider Config

```hcl
terraform {
  required_providers {
    verda = {
      source  = "verda-cloud/verda"
      version = "~> 1.0"
    }
  }
}

provider "verda" {
  # Uses VERDA_CLIENT_ID and VERDA_CLIENT_SECRET env vars
}
```

## Supported Resources

**Compute:** `verda_instance`, `verda_ssh_key`, `verda_startup_script`
**Storage:** `verda_volume`
**Containers:** Serverless deployments, batch jobs, registry credentials

## Common Operations

```bash
# Initialize (downloads provider)
ssh root@$VERDA_IP "cd /root/tofu && tofu init"

# Preview changes
ssh root@$VERDA_IP "cd /root/tofu && tofu plan"

# Apply changes
ssh root@$VERDA_IP "cd /root/tofu && tofu apply -auto-approve"

# List managed resources
ssh root@$VERDA_IP "cd /root/tofu && tofu state list"

# Import existing resource
ssh root@$VERDA_IP "cd /root/tofu && tofu import verda_instance.main <instance-id>"
```

## Auth

Env vars set in `/root/.bashrc`:
- `VERDA_CLIENT_ID`
- `VERDA_CLIENT_SECRET`

If $ARGUMENTS provided, treat as a specific Terraform question or operation.
Otherwise show this reference.
