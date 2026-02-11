---
description: OpenTofu guide — open-source Terraform alternative for Verda IaC.
user-invocable: true
---

OpenTofu guide — open-source Terraform alternative for Verda IaC.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Docs:** https://opentofu.org/docs/language/
**Modules:** https://search.opentofu.org/modules/
**Verda Provider:** https://docs.verda.com/infrastructure-as-code/opentofu/getting-started
**Installed on:** root@$VERDA_IP (via snap)

## Key Differences from Terraform

- Command: `tofu` instead of `terraform`
- Registry: `registry.opentofu.org/verda-cloud/verda` (or Terraform registry works too)
- HCL syntax, provider config, resource definitions are IDENTICAL
- MPL 2.0 license (vs Terraform BSL)

## Provider Config (OpenTofu Registry)

```hcl
terraform {
  required_providers {
    verda = {
      source  = "registry.opentofu.org/verda-cloud/verda"
      version = "~> 1.0"
    }
  }
}
```

## CLI Commands

```bash
tofu init      # Download providers
tofu plan      # Preview changes
tofu apply     # Execute changes
tofu destroy   # Tear down resources
tofu state list  # List managed resources
tofu import    # Import existing resources
tofu fmt       # Format HCL files
tofu validate  # Validate config
```

## Config Location on Verda

`/root/tofu/` — main IaC directory
- `main.tf` — provider + resources
- `variables.tf` — input variables
- `outputs.tf` — output values
- `.terraform/` — downloaded providers (auto-created by `tofu init`)

## Quick Start

```bash
ssh root@$VERDA_IP "cd /root/tofu && tofu init && tofu plan"
```

If $ARGUMENTS provided, treat as a specific OpenTofu question or operation.
