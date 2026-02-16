# ComfyuME Infrastructure — OpenTofu / Verda (ex. DataCrunch)
#
# Manages serverless GPU container deployments for workshop inference.
# State: local file (terraform.tfstate) — gitignored, lives on execution host.
# Auth: VERDA_CLIENT_ID + VERDA_CLIENT_SECRET env vars (never in .tf files).

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    verda = {
      source  = "verda-cloud/verda"
      version = "~> 1.1"
    }
  }
}

# Provider reads VERDA_CLIENT_ID and VERDA_CLIENT_SECRET from environment.
provider "verda" {}
