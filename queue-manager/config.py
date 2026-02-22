"""
Configuration management for Queue Manager
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str
    redis_db: int = 0

    # Queue Configuration
    queue_mode: str = "fifo"
    enable_priority: bool = True
    job_timeout: int = 3600  # seconds
    max_queue_depth: int = 100

    # Inference Mode: "local" | "redis" | "serverless"
    # - local: GPU on same machine, workers poll Redis queue
    # - redis: Remote GPU via Tailscale, workers poll Redis queue
    # - serverless: Direct HTTP to Verda Serverless (auto-scaling)
    inference_mode: str = "local"

    # Serverless Configuration
    # Primary endpoint (used when serverless_active is not set or "default")
    serverless_endpoint: Optional[str] = None

    # Multi-GPU Serverless Endpoints (4 options: 2 GPUs x 2 pricing tiers)
    # Usage: Set SERVERLESS_ACTIVE to switch between endpoints
    # H200: 141GB HBM3e, 4.8 TB/s bandwidth - good for 720p/1080p/some 4K
    serverless_endpoint_h200_spot: Optional[str] = None       # €0.97/hr + VAT (workshop)
    serverless_endpoint_h200_on_demand: Optional[str] = None  # €2.80/hr + VAT (demos)
    # B300: 288GB HBM3e, 8.0 TB/s bandwidth - required for native 4K
    serverless_endpoint_b300_spot: Optional[str] = None       # €1.61/hr + VAT (cheap 4K)
    serverless_endpoint_b300_on_demand: Optional[str] = None  # €4.63/hr + VAT (premium 4K)

    # Active endpoint selector: "default" | "h200-spot" | "h200-on-demand" | "b300-spot" | "b300-on-demand"
    serverless_active: str = "default"

    # Verda API Key (required for serverless auth)
    serverless_api_key: Optional[str] = None

    # Worker configuration (for local/redis modes)
    num_workers: int = 1

    @property
    def active_serverless_endpoint(self) -> Optional[str]:
        """Get the currently active serverless endpoint based on serverless_active setting"""
        endpoints = {
            "h200-spot": self.serverless_endpoint_h200_spot,
            "h200-on-demand": self.serverless_endpoint_h200_on_demand,
            "b300-spot": self.serverless_endpoint_b300_spot,
            "b300-on-demand": self.serverless_endpoint_b300_on_demand,
        }
        return endpoints.get(self.serverless_active) or self.serverless_endpoint

    @property
    def active_gpu_type(self) -> str:
        """Get human-readable GPU type for logging/health checks"""
        if self.inference_mode != "serverless":
            return "local"
        gpu_types = {
            "h200-spot": "H200-141GB-SPOT",
            "h200-on-demand": "H200-141GB",
            "b300-spot": "B300-288GB-SPOT",
            "b300-on-demand": "B300-288GB",
        }
        return gpu_types.get(self.serverless_active, "serverless")

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 3000
    log_level: str = "INFO"
    debug: bool = False

    # Worker Configuration
    worker_heartbeat_timeout: int = 60  # seconds
    worker_poll_interval: int = 1  # seconds

    # Storage paths
    outputs_path: str = "/outputs"
    inputs_path: str = "/inputs"

    # SFS-based delivery (replaces HTTP polling for serverless)
    # When enabled, QM injects a unique prefix into workflows, POSTs to serverless,
    # then polls the SFS directory for matching output files instead of HTTP /history.
    # Fixes load-balancer routing issue where GET hits different container than POST.
    sfs_delivery_enabled: bool = True   # False = fall back to HTTP history polling
    sfs_output_dir: str = "/mnt/sfs/outputs"
    sfs_poll_interval: float = 3.0     # seconds between directory scans
    sfs_max_wait: int = 600            # max seconds to wait for output files
    sfs_settle_time: float = 2.0       # wait after first file for multi-image workflows

    # Application metadata
    app_name: str = "ComfyUI Queue Manager"
    app_version: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields in .env without validation errors
    )


# Singleton instance
settings = Settings()
