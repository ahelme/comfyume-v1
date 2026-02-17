# ComfyuME Serverless GPU Deployments
#
# !!! DANGER — NEVER RUN tofu plan / tofu apply FROM MELLO OR AGAINST PRODUCTION !!!
# !!! OpenTofu commands ONLY on a NEW TESTING server instance.                    !!!
# !!! Edit .tf files here, commit via git flow, apply ONLY on a new testing server. !!!
#
# 4 deployment variants: H200/B300 x spot/on-demand
# All 4 exist in production. Toggle via deploy_* variables.
#
# Naming: comfyume-vca-ftv-{gpu}-{pricing}
#   vca = Verda Cloud Accelerated, ftv = Film Tech Video
#
# DRIFT AUDIT (2026-02-16):
#   This file reflects ACTUAL live production state.
#   Intentional fixes (e.g. adding --output-directory to all deployments)
#   should be made in a SEPARATE commit with tofu plan review.

locals {
  # Base startup command — includes --output-directory for SFS-based image delivery (#54, #70)
  base_cmd = [
    "python3", "/workspace/ComfyUI/main.py",
    "--listen", "0.0.0.0",
    "--port", "8188",
    "--extra-model-paths-config", "/mnt/sfs/extra_model_paths.yaml",
    "--verbose"
  ]

  # All deployments use --output-directory to write images to SFS
  full_cmd = concat(local.base_cmd, ["--output-directory", "/mnt/sfs/outputs"])

  deployments = {
    "h200-spot" = {
      enabled  = var.deploy_h200_spot
      gpu_name = "H200"
      is_spot  = true
      name     = "comfyume-vca-ftv-h200-spot"
      cmd      = local.full_cmd
    }
    "h200-on-demand" = {
      enabled  = var.deploy_h200_on_demand
      gpu_name = "H200"
      is_spot  = false
      name     = "comfyume-vca-ftv-h200-on-demand"
      cmd      = local.full_cmd
    }
    "b300-spot" = {
      enabled  = var.deploy_b300_spot
      gpu_name = "B300"
      is_spot  = true
      name     = "comfyume-vca-ftv-b300-spot"
      cmd      = local.full_cmd
    }
    "b300-on-demand" = {
      enabled  = var.deploy_b300_on_demand
      gpu_name = "B300"
      is_spot  = false
      name     = "comfyume-vca-ftv-b300-on-demand"
      cmd      = local.full_cmd
    }
  }

  # Only create deployments that are enabled
  active_deployments = {
    for k, v in local.deployments : k => v if v.enabled
  }
}

resource "verda_container" "worker" {
  for_each = local.active_deployments

  name    = each.value.name
  is_spot = each.value.is_spot

  compute = {
    name = each.value.gpu_name
    size = 1
  }

  scaling = {
    min_replica_count               = var.min_replicas
    max_replica_count               = var.max_replicas
    concurrent_requests_per_replica = 1
    queue_message_ttl_seconds       = var.request_ttl
    deadline_seconds                = var.request_ttl  # Live: matches TTL (36000)

    queue_load = {
      threshold = 2  # Live value (was 1 in initial .tf)
    }

    scale_up_policy = {
      delay_seconds = 0
    }

    scale_down_policy = {
      delay_seconds = var.scale_down_delay
    }
  }

  containers = [{
    image        = var.worker_image
    exposed_port = 8188

    # Live: entrypoint=null, cmd=list of args (exec-style, no shell wrapper)
    entrypoint_overrides = {
      enabled = true
      cmd     = each.value.cmd
    }

    # Live: healthcheck path is "/" (not /system_stats)
    healthcheck = {
      enabled = "true"
      path    = "/"
      port    = "8188"
    }

    env = [
      {
        name                        = "HF_HOME"
        type                        = "plain"
        value_or_reference_to_secret = "/mnt/sfs/cache/huggingface"
      },
      {
        name                        = "HF_TOKEN"
        type                        = "plain"
        value_or_reference_to_secret = var.hf_token
      }
    ]

    # Live: 3 volume mounts (scratch, memory, shared)
    volume_mounts = [
      {
        type       = "scratch"
        mount_path = "/data"
      },
      {
        type       = "memory"
        mount_path = "/dev/shm"
        size_in_mb = 64
      },
      {
        type       = "shared"
        volume_id  = var.sfs_volume_id
        mount_path = "/mnt/sfs"
      }
    ]
  }]
}

# --------------------------------------------------------------------------
# Outputs — endpoint URLs for .env / queue-manager config
# --------------------------------------------------------------------------

output "deployment_endpoints" {
  description = "Endpoint URLs for each active deployment"
  value = {
    for k, v in verda_container.worker : k => v.endpoint_base_url
  }
}

output "deployment_names" {
  description = "Deployment names for reference"
  value = {
    for k, v in verda_container.worker : k => v.name
  }
}
