# --------------------------------------------------------------------------
# Container image
# --------------------------------------------------------------------------

variable "worker_image" {
  description = "Container image for ComfyUI serverless workers"
  type        = string
  default     = "ghcr.io/ahelme/comfyume-worker:v0.11.0"
}

# --------------------------------------------------------------------------
# SFS volume (shared filesystem for models + outputs)
# --------------------------------------------------------------------------

variable "sfs_volume_id" {
  description = "Verda shared volume ID for SFS mount (models, outputs, cache)"
  type        = string
  # No default — must be set per environment (prod vs clone)
}

# --------------------------------------------------------------------------
# Hugging Face token (injected as container env var)
# --------------------------------------------------------------------------

variable "hf_token" {
  description = "Hugging Face API token for gated model access"
  type        = string
  sensitive   = true
  default     = ""
}

# --------------------------------------------------------------------------
# Scaling defaults
# --------------------------------------------------------------------------

variable "min_replicas" {
  description = "Minimum replicas (0 = scale to zero when idle)"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum concurrent replicas"
  type        = number
  default     = 10
}

variable "scale_down_delay" {
  description = "Seconds to wait before scaling down an idle replica"
  type        = number
  default     = 300
}

variable "request_ttl" {
  description = "Max seconds a request can run before timeout"
  type        = number
  default     = 36000
}

# --------------------------------------------------------------------------
# Deployment toggles — all 4 exist in production (defaults match live)
# --------------------------------------------------------------------------

variable "deploy_h200_spot" {
  description = "Create the H200 spot deployment"
  type        = bool
  default     = true
}

variable "deploy_h200_on_demand" {
  description = "Create the H200 on-demand deployment"
  type        = bool
  default     = true
}

variable "deploy_b300_spot" {
  description = "Create the B300 spot deployment"
  type        = bool
  default     = true
}

variable "deploy_b300_on_demand" {
  description = "Create the B300 on-demand deployment"
  type        = bool
  default     = true
}

# --------------------------------------------------------------------------
# Location
# --------------------------------------------------------------------------

variable "location" {
  description = "Verda datacenter location"
  type        = string
  default     = "FIN-01"
}
