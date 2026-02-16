# ComfyuME Serverless GPU Deployments
#
# 4 deployment variants: H200/B300 x spot/on-demand
# Each toggle-able via deploy_* variables (default: only H200 spot enabled).
#
# Naming: comfyume-vca-ftv-{gpu}-{pricing}
#   vca = Verda Cloud Accelerated, ftv = Film Tech Video

locals {
  deployments = {
    "h200-spot" = {
      enabled  = var.deploy_h200_spot
      gpu_name = "H200 SXM5 141GB"
      is_spot  = true
      name     = "comfyume-vca-ftv-h200-spot"
    }
    "h200-on-demand" = {
      enabled  = var.deploy_h200_on_demand
      gpu_name = "H200 SXM5 141GB"
      is_spot  = false
      name     = "comfyume-vca-ftv-h200-on-demand"
    }
    "b300-spot" = {
      enabled  = var.deploy_b300_spot
      gpu_name = "B300"
      is_spot  = true
      name     = "comfyume-vca-ftv-b300-spot"
    }
    "b300-on-demand" = {
      enabled  = var.deploy_b300_on_demand
      gpu_name = "B300"
      is_spot  = false
      name     = "comfyume-vca-ftv-b300-on-demand"
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
    min_replica_count              = var.min_replicas
    max_replica_count              = var.max_replicas
    concurrent_requests_per_replica = 1
    queue_message_ttl_seconds      = var.request_ttl

    queue_load = {
      threshold = 1
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

    entrypoint_overrides = {
      enabled    = true
      entrypoint = ["/bin/sh", "-c"]
      cmd        = [var.comfyui_start_command]
    }

    healthcheck = {
      enabled = "true"
      path    = "/system_stats"
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

    volume_mounts = [{
      type       = "shared"
      volume_id  = var.sfs_volume_id
      mount_path = "/mnt/sfs"
    }]
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
