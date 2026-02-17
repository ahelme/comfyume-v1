---
description: OpenTofu guide — open-source Terraform alternative for Verda IaC.
user-invocable: true
---

OpenTofu guide — open-source Terraform alternative for Verda IaC.

**Docs:** https://opentofu.org/docs/language/
**Verda Provider:** `verda-cloud/verda` v1.1.1
**Version installed:** v1.11.5 (on Mello + Verda)

## Key Differences from Terraform

- Command: `tofu` instead of `terraform`
- Registry: uses Terraform registry transparently (`verda-cloud/verda`)
- HCL syntax, provider config, resource definitions are IDENTICAL
- MPL 2.0 license (vs Terraform BSL)

## Project Layout

```
infrastructure/          # .tf files — committed to git
  providers.tf           # Provider config (verda-cloud/verda ~> 1.1)
  variables.tf           # Input variables with defaults
  containers.tf          # Serverless GPU deployments (H200/B300 x spot/on-demand)
  terraform.tfvars       # Secrets — GITIGNORED, copy from .example
  terraform.tfvars.example  # Template for secrets
  .terraform.lock.hcl    # Provider version lock — COMMITTED
  .terraform/            # Downloaded providers — GITIGNORED
```

## Workflow

```bash
cd infrastructure

# Set credentials (from Verda console > API Keys)
export VERDA_CLIENT_ID="..."
export VERDA_CLIENT_SECRET="..."

# First time: copy and fill in vars
cp terraform.tfvars.example terraform.tfvars

# Standard workflow
tofu init       # Download providers (first time / after provider change)
tofu validate   # Check config syntax
tofu plan       # Preview changes — ALWAYS before apply
tofu apply      # Execute changes (confirms interactively)
```

## CLI Commands

```bash
tofu init      # Download providers
tofu plan      # Preview changes (drift detection)
tofu apply     # Execute changes
tofu destroy   # Tear down resources
tofu state list  # List managed resources
tofu state show  # Show specific resource details
tofu import    # Import existing resources into state
tofu fmt       # Format HCL files
tofu validate  # Validate config syntax
```

## Import Existing Deployments

```bash
# Import the H200 spot deployment
tofu import 'verda_container.worker["h200-spot"]' <deployment-id>

# Get deployment IDs from Verda console or SDK
```

If $ARGUMENTS provided, treat as a specific OpenTofu question or operation.
