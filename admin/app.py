"""
Admin Dashboard V2 - Comprehensive Management UI for ComfyUI Workshop

Phase 1: System Status, Container Management (Issue #65)
Phase 2: GPU Deployment Switching (Issue #66)
Phase 3: Storage & R2 Management (Issue #67)
Phase 4: Templates & Models Management (Issue #88)
Phase 4b: Model Download Engine (Issue TBD)
"""
import asyncio
import logging
import secrets
import shutil
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import httpx

# Optional: Docker SDK for container management
try:
    import docker
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
except Exception:
    docker_client = None
    DOCKER_AVAILABLE = False

# Optional: Redis for direct status checks
try:
    import redis as redis_lib
    REDIS_LIB_AVAILABLE = True
except ImportError:
    REDIS_LIB_AVAILABLE = False

# Optional: boto3 for R2 storage management
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
QUEUE_MANAGER_URL = os.getenv("QUEUE_MANAGER_URL", "http://queue-manager:3000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_secure_password")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
ENV_FILE_PATH = os.getenv("ENV_FILE_PATH", "/app/project.env")

# R2 Configuration
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKETS = [
    "comfyume-model-vault-backups",
    "comfyume-cache-backups",
    "comfyume-worker-container-backups",
    "comfyume-user-files-backups",
]

# Model Download Configuration
HF_TOKEN = os.getenv("HF_TOKEN", "")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
MODELS_BASE_PATH = Path("/models")

# Isolate mode — when ON, blocks all /api/* except /api/admin/isolate
# Use for fault isolation: enable isolate mode, then test individual features
isolate_mode = os.getenv("ADMIN_ISOLATE_MODE", "false").lower() == "true"

# GPU Deployment options (serverless via Verda)
GPU_DEPLOYMENTS = {
    "h200-spot": {
        "name": "H200 Spot",
        "gpu": "H200 SXM5",
        "vram": "141GB HBM3e",
        "price_eur": 0.97,
        "price_label": "\u20ac0.97/hr",
        "type": "spot",
        "best_for": "Workshop, testing, cost-sensitive",
        "bandwidth": "4.8 TB/s",
    },
    "h200-on-demand": {
        "name": "H200 On-Demand",
        "gpu": "H200 SXM5",
        "vram": "141GB HBM3e",
        "price_eur": 2.80,
        "price_label": "\u20ac2.80/hr",
        "type": "on-demand",
        "best_for": "Important demos, guaranteed availability",
        "bandwidth": "4.8 TB/s",
    },
    "b300-spot": {
        "name": "B300 Spot",
        "gpu": "B300 SXM6",
        "vram": "288GB HBM3e",
        "price_eur": 1.61,
        "price_label": "\u20ac1.61/hr",
        "type": "spot",
        "best_for": "4K experimentation, cheap 4K",
        "bandwidth": "8.0 TB/s",
    },
    "b300-on-demand": {
        "name": "B300 On-Demand",
        "gpu": "B300 SXM6",
        "vram": "288GB HBM3e",
        "price_eur": 4.63,
        "price_label": "\u20ac4.63/hr",
        "type": "on-demand",
        "best_for": "Boss demo 4K, critical 4K production",
        "bandwidth": "8.0 TB/s",
    },
}

app = FastAPI(title="ComfyUI Admin Dashboard V2", version="2.0.0")

# HTTP Basic Auth
security = HTTPBasic()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify admin credentials using constant-time comparison"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        logger.warning(f"Failed login attempt: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# HTTP client for queue manager
http_client = httpx.AsyncClient(timeout=10.0)

# Redis client for direct status checks
redis_direct = None
if REDIS_LIB_AVAILABLE and REDIS_PASSWORD:
    try:
        redis_direct = redis_lib.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=3,
            socket_connect_timeout=3,
        )
    except Exception as e:
        logger.warning(f"Redis direct connection failed: {e}")


# Load dashboard HTML at startup
DASHBOARD_HTML = ""
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
if os.path.exists(dashboard_path):
    with open(dashboard_path, "r") as f:
        DASHBOARD_HTML = f.read()
else:
    DASHBOARD_HTML = "<html><body><h1>Dashboard HTML not found</h1></body></html>"
    logger.warning(f"Dashboard HTML not found at {dashboard_path}")


@app.get("/", response_class=HTMLResponse)
async def dashboard(username: str = Depends(verify_admin)):
    """Serve the admin dashboard"""
    return HTMLResponse(content=DASHBOARD_HTML)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)"""
    return {"status": "healthy", "service": "admin-dashboard", "version": "2.0.0"}


# ============================================================================
# Isolate Mode (#75)
# ============================================================================

@app.get("/api/admin/isolate")
async def get_isolate_status():
    """Current isolate mode state (no auth — frontend reads on load)"""
    return {"active": isolate_mode}


@app.post("/api/admin/isolate")
async def set_isolate_status(request: Request, username: str = Depends(verify_admin)):
    """Toggle isolate mode at runtime"""
    global isolate_mode
    body = await request.json()
    isolate_mode = bool(body.get("active", False))
    logger.info(f"Isolate mode {'ACTIVE' if isolate_mode else 'off'} — set by {username}")
    return {"active": isolate_mode}


@app.middleware("http")
async def isolate_gate(request: Request, call_next):
    """Block /api/* endpoints (except /api/admin/isolate) when isolate mode is active"""
    path = request.url.path
    if isolate_mode and path.startswith("/api/") and not path.startswith("/api/admin/isolate"):
        return JSONResponse(
            status_code=503,
            content={"detail": "Isolate mode is active. All features are disabled. Toggle off via the dashboard header."},
        )
    return await call_next(request)


# ============================================================================
# System Status (Phase 1 - Issue #65)
# ============================================================================

@app.get("/api/system/status")
async def system_status(username: str = Depends(verify_admin)):
    """Overall system health: Redis, Queue Manager, Serverless"""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {},
        "docker_available": DOCKER_AVAILABLE,
    }

    # Redis status
    redis_ok = False
    redis_info = {}
    if redis_direct:
        try:
            redis_ok = redis_direct.ping()
            mem_info = redis_direct.info("memory")
            client_info = redis_direct.info("clients")
            redis_info = {
                "used_memory_human": mem_info.get("used_memory_human", "unknown"),
                "connected_clients": client_info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
    result["services"]["redis"] = {"healthy": redis_ok, "info": redis_info}

    # Queue Manager status
    qm_ok = False
    qm_data = {}
    try:
        resp = await http_client.get(f"{QUEUE_MANAGER_URL}/health")
        if resp.status_code == 200:
            qm_ok = True
            qm_data = resp.json()
    except Exception as e:
        logger.error(f"Queue manager check failed: {e}")
    result["services"]["queue_manager"] = {"healthy": qm_ok, "info": qm_data}

    # Queue stats
    try:
        resp = await http_client.get(f"{QUEUE_MANAGER_URL}/api/queue/status")
        if resp.status_code == 200:
            result["queue"] = resp.json()
    except Exception:
        result["queue"] = None

    # Disk usage
    usage = shutil.disk_usage("/")
    result["disk"] = {
        "total_gb": round(usage.total / (1024**3), 1),
        "used_gb": round(usage.used / (1024**3), 1),
        "free_gb": round(usage.free / (1024**3), 1),
        "percent_used": round(usage.used / usage.total * 100, 1),
    }

    return result


# ============================================================================
# Container Management (Phase 1 - Issue #65)
# ============================================================================

@app.get("/api/containers")
async def list_containers(username: str = Depends(verify_admin)):
    """List Docker containers (filtered to comfy- prefix)"""
    if not DOCKER_AVAILABLE:
        return {"error": "Docker not available. Mount /var/run/docker.sock to enable.", "containers": []}

    try:
        containers = docker_client.containers.list(all=True, filters={"name": "comfy"})
        result = []
        for c in containers:
            result.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "state": c.attrs.get("State", {}).get("Status", "unknown"),
                "image": c.image.tags[0] if c.image.tags else str(c.image.id[:12]),
                "created": c.attrs.get("Created", ""),
                "health": c.attrs.get("State", {}).get("Health", {}).get("Status", "none"),
            })
        # Sort: services first (redis, queue-manager, admin), then users
        result.sort(key=lambda x: (
            0 if "redis" in x["name"] else
            1 if "queue" in x["name"] else
            2 if "admin" in x["name"] else
            3 if "nginx" in x["name"] else
            4,
            x["name"]
        ))
        return {"containers": result}
    except Exception as e:
        logger.error(f"Container list failed: {e}")
        return {"error": str(e), "containers": []}


@app.post("/api/containers/{container_name}/restart")
async def restart_container(container_name: str, username: str = Depends(verify_admin)):
    """Restart a container (restricted to comfy- prefix)"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Docker not available")
    if not container_name.startswith("comfy-"):
        raise HTTPException(status_code=403, detail="Can only manage comfy- containers")

    try:
        container = docker_client.containers.get(container_name)
        container.restart(timeout=30)
        logger.info(f"Container {container_name} restarted by {username}")
        return {"status": "restarted", "container": container_name}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containers/{container_name}/stop")
async def stop_container(container_name: str, username: str = Depends(verify_admin)):
    """Stop a container (restricted to comfy- prefix)"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Docker not available")
    if not container_name.startswith("comfy-"):
        raise HTTPException(status_code=403, detail="Can only manage comfy- containers")

    try:
        container = docker_client.containers.get(container_name)
        container.stop(timeout=30)
        logger.info(f"Container {container_name} stopped by {username}")
        return {"status": "stopped", "container": container_name}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/containers/{container_name}/start")
async def start_container(container_name: str, username: str = Depends(verify_admin)):
    """Start a stopped container (restricted to comfy- prefix)"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Docker not available")
    if not container_name.startswith("comfy-"):
        raise HTTPException(status_code=403, detail="Can only manage comfy- containers")

    try:
        container = docker_client.containers.get(container_name)
        container.start()
        logger.info(f"Container {container_name} started by {username}")
        return {"status": "started", "container": container_name}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/containers/{container_name}/logs")
async def container_logs(container_name: str, lines: int = 100, username: str = Depends(verify_admin)):
    """Get container logs (restricted to comfy- prefix)"""
    if not DOCKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Docker not available")
    if not container_name.startswith("comfy-"):
        raise HTTPException(status_code=403, detail="Can only manage comfy- containers")

    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=lines, timestamps=True).decode("utf-8", errors="replace")
        return {"container": container_name, "logs": logs}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GPU Deployment Switching (Phase 2 - Issue #66)
# ============================================================================

@app.get("/api/gpu/status")
async def gpu_status(username: str = Depends(verify_admin)):
    """Get current GPU deployment status"""
    current = {
        "inference_mode": "unknown",
        "active_gpu": "unknown",
        "serverless_active": "unknown",
    }

    # Get live status from queue manager
    try:
        resp = await http_client.get(f"{QUEUE_MANAGER_URL}/health")
        if resp.status_code == 200:
            data = resp.json()
            current.update({
                "inference_mode": data.get("inference_mode", "unknown"),
                "active_gpu": data.get("active_gpu", "unknown"),
                "serverless_endpoint": data.get("serverless_endpoint"),
                "status": data.get("status", "unknown"),
                "queue_depth": data.get("queue_depth", 0),
            })
    except Exception as e:
        logger.error(f"GPU status check failed: {e}")

    # Also read .env for SERVERLESS_ACTIVE
    try:
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SERVERLESS_ACTIVE="):
                        current["serverless_active"] = line.split("=", 1)[1]
                    elif line.startswith("INFERENCE_MODE="):
                        current["inference_mode_env"] = line.split("=", 1)[1]
    except Exception:
        pass

    return {
        "current": current,
        "deployments": GPU_DEPLOYMENTS,
    }


@app.post("/api/gpu/switch")
async def switch_gpu(body: dict, username: str = Depends(verify_admin)):
    """Switch GPU deployment: update .env and restart queue-manager"""
    mode = body.get("mode", "")

    if mode == "local":
        inference_mode = "local"
        serverless_active = "default"
    elif mode in GPU_DEPLOYMENTS:
        inference_mode = "serverless"
        serverless_active = mode
    else:
        valid = list(GPU_DEPLOYMENTS.keys()) + ["local"]
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}. Valid: {valid}")

    # Update .env file
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r") as f:
                lines = f.readlines()

            new_lines = []
            found_inference = False
            found_active = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("INFERENCE_MODE="):
                    new_lines.append(f"INFERENCE_MODE={inference_mode}\n")
                    found_inference = True
                elif stripped.startswith("SERVERLESS_ACTIVE="):
                    new_lines.append(f"SERVERLESS_ACTIVE={serverless_active}\n")
                    found_active = True
                else:
                    new_lines.append(line)

            if not found_inference:
                new_lines.append(f"INFERENCE_MODE={inference_mode}\n")
            if not found_active:
                new_lines.append(f"SERVERLESS_ACTIVE={serverless_active}\n")

            with open(ENV_FILE_PATH, "w") as f:
                f.writelines(new_lines)

            logger.info(f"GPU switched to {mode} by {username}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update .env: {e}")
    else:
        logger.warning(f".env file not found at {ENV_FILE_PATH}")

    # Restart queue-manager to apply new config
    restart_result = "skipped (no Docker)"
    if DOCKER_AVAILABLE:
        try:
            qm = docker_client.containers.get("comfy-queue-manager")
            qm.restart(timeout=30)
            restart_result = "restarted"
            logger.info("Queue manager restarted after GPU switch")
        except Exception as e:
            restart_result = f"failed: {e}"
            logger.error(f"Queue manager restart failed: {e}")

    return {
        "status": "switched",
        "mode": mode,
        "inference_mode": inference_mode,
        "serverless_active": serverless_active,
        "queue_manager_restart": restart_result,
    }


# ============================================================================
# Storage Management (Phase 3 - Issue #67)
# ============================================================================

@app.get("/api/storage/disk")
async def storage_disk(username: str = Depends(verify_admin)):
    """Disk usage breakdown by directory"""
    usage = shutil.disk_usage("/")

    dirs = {}
    check_paths = [
        ("/outputs", "User Outputs"),
        ("/inputs", "User Inputs"),
        ("/models", "Models"),
        ("/workflows", "Workflows"),
    ]

    for path, label in check_paths:
        if os.path.exists(path):
            try:
                total = 0
                count = 0
                for f in Path(path).rglob("*"):
                    if f.is_file():
                        total += f.stat().st_size
                        count += 1
                dirs[label] = {
                    "path": path,
                    "size_gb": round(total / (1024**3), 2),
                    "size_human": _human_size(total),
                    "file_count": count,
                }
            except PermissionError:
                dirs[label] = {"path": path, "error": "permission denied"}
        else:
            dirs[label] = {"path": path, "error": "not mounted"}

    return {
        "disk": {
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "percent_used": round(usage.used / usage.total * 100, 1),
        },
        "directories": dirs,
    }


@app.get("/api/storage/r2")
async def storage_r2(username: str = Depends(verify_admin)):
    """R2 bucket sizes and object counts"""
    if not BOTO3_AVAILABLE or not R2_ENDPOINT:
        return {"error": "R2 not configured (set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)", "buckets": []}

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )

        buckets = []
        for bucket_name in R2_BUCKETS:
            try:
                total_size = 0
                total_objects = 0
                paginator = s3.get_paginator("list_objects_v2")
                for page in paginator.paginate(Bucket=bucket_name):
                    for obj in page.get("Contents", []):
                        total_size += obj["Size"]
                        total_objects += 1

                buckets.append({
                    "name": bucket_name,
                    "objects": total_objects,
                    "size_gb": round(total_size / (1024**3), 2),
                    "size_human": _human_size(total_size),
                    "status": "ok",
                })
            except Exception as e:
                buckets.append({
                    "name": bucket_name,
                    "error": str(e),
                    "status": "error",
                })

        return {"buckets": buckets}
    except Exception as e:
        return {"error": str(e), "buckets": []}


@app.get("/api/storage/browse")
async def storage_browse(path: str = "/", username: str = Depends(verify_admin)):
    """Browse directory contents (restricted to allowed roots)"""
    allowed_roots = ["/outputs", "/inputs", "/models", "/workflows"]

    clean_path = os.path.normpath(path)

    # Security: prevent directory traversal
    if ".." in clean_path:
        raise HTTPException(status_code=403, detail="Directory traversal not allowed")

    if not any(clean_path.startswith(root) for root in allowed_roots) and clean_path != "/":
        raise HTTPException(status_code=403, detail="Access restricted to: /outputs, /inputs, /models, /workflows")

    if clean_path == "/":
        entries = []
        for root in allowed_roots:
            exists = os.path.exists(root)
            entries.append({
                "name": root.lstrip("/"),
                "type": "directory",
                "path": root,
                "exists": exists,
            })
        return {"path": "/", "entries": entries}

    if not os.path.exists(clean_path):
        raise HTTPException(status_code=404, detail=f"Path not found: {clean_path}")

    if not os.path.isdir(clean_path):
        stat = os.stat(clean_path)
        return {
            "path": clean_path,
            "type": "file",
            "size": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }

    entries = []
    try:
        with os.scandir(clean_path) as scanner:
            for entry in sorted(scanner, key=lambda e: (not e.is_dir(), e.name)):
                info = {
                    "name": entry.name,
                    "type": "directory" if entry.is_dir() else "file",
                    "path": entry.path,
                }
                if entry.is_file():
                    try:
                        stat = entry.stat()
                        info["size"] = stat.st_size
                        info["size_human"] = _human_size(stat.st_size)
                        info["modified"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    except (PermissionError, OSError):
                        info["error"] = "stat failed"
                entries.append(info)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"path": clean_path, "entries": entries}


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


# ============================================================================
# Queue Proxy (proxies to queue-manager for frontend use)
# ============================================================================

@app.get("/api/queue/status")
async def proxy_queue_status(username: str = Depends(verify_admin)):
    """Proxy queue status from queue-manager"""
    try:
        response = await http_client.get(f"{QUEUE_MANAGER_URL}/api/queue/status")
        return response.json()
    except Exception as e:
        logger.error(f"Queue status proxy failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/queue/jobs")
async def proxy_jobs(limit: int = 50, username: str = Depends(verify_admin)):
    """Proxy job list from queue-manager"""
    try:
        response = await http_client.get(f"{QUEUE_MANAGER_URL}/api/jobs?limit={limit}")
        return response.json()
    except Exception as e:
        logger.error(f"Jobs proxy failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.delete("/api/queue/jobs/{job_id}")
async def proxy_cancel_job(job_id: str, username: str = Depends(verify_admin)):
    """Proxy job cancellation to queue-manager"""
    try:
        response = await http_client.delete(f"{QUEUE_MANAGER_URL}/api/jobs/{job_id}")
        if response.status_code == 204:
            return {"status": "cancelled", "job_id": job_id}
        return JSONResponse(status_code=response.status_code, content=response.json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/queue/jobs/{job_id}/priority")
async def proxy_update_priority(job_id: str, body: dict, username: str = Depends(verify_admin)):
    """Proxy priority update to queue-manager"""
    try:
        response = await http_client.patch(
            f"{QUEUE_MANAGER_URL}/api/jobs/{job_id}/priority",
            json=body
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Templates & Models Management (Phase 4 - Issue #88)
# ============================================================================

# Node types that use specific model directories when properties.models is absent
_FALLBACK_DIRS = {
    "UNETLoader": "diffusion_models",
    "CheckpointLoaderSimple": "checkpoints",
}


def _extract_models_from_workflow(data: dict) -> dict:
    """Extract template names and model dependencies from a workflow JSON."""
    templates = []
    models_seen = set()  # (directory, filename) for dedup
    models = []

    # Collect all nodes: top-level + subgraph nodes
    all_nodes = list(data.get("nodes", []))
    subgraphs = data.get("definitions", {}).get("subgraphs", [])
    for sg in subgraphs:
        templates.append({"name": sg.get("name", "Unnamed")})
        all_nodes.extend(sg.get("nodes", []))

    for node in all_nodes:
        node_type = node.get("type", "")
        props = node.get("properties", {})
        prop_models = props.get("models")

        if prop_models and isinstance(prop_models, list):
            for m in prop_models:
                key = (m.get("directory", ""), m.get("name", ""))
                if key not in models_seen and key[1]:
                    models_seen.add(key)
                    models.append({
                        "filename": m["name"],
                        "directory": m.get("directory", ""),
                        "url": m.get("url"),
                    })
        elif node_type in _FALLBACK_DIRS:
            wv = node.get("widgets_values", [])
            if wv and isinstance(wv, list) and isinstance(wv[0], str) and wv[0]:
                directory = _FALLBACK_DIRS[node_type]
                key = (directory, wv[0])
                if key not in models_seen:
                    models_seen.add(key)
                    models.append({
                        "filename": wv[0],
                        "directory": directory,
                        "url": None,
                    })

    return {"templates": templates, "models": models}


def _check_model_on_disk(directory: str, filename: str) -> tuple:
    """Check if a model file exists on disk; return (exists, size_bytes)."""
    model_path = Path("/models") / directory / filename
    if model_path.is_file():
        try:
            size = model_path.stat().st_size
            return True, size
        except OSError:
            return True, None
    return False, None


@app.get("/api/templates/scan")
async def templates_scan(username: str = Depends(verify_admin)):
    """Scan workflow JSONs, extract model deps, check disk presence."""
    workflows_dir = Path("/workflows")
    results = []

    if not workflows_dir.is_dir():
        return {"workflows": [], "disk": {}, "error": "/workflows not mounted"}

    for wf_path in sorted(workflows_dir.glob("*.json")):
        if wf_path.name.startswith("."):
            continue
        try:
            with open(wf_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            results.append({
                "filename": wf_path.name,
                "error": str(e),
                "templates": [],
                "models": [],
                "models_total": 0,
                "models_on_disk": 0,
                "models_missing": 0,
            })
            continue

        extracted = _extract_models_from_workflow(data)
        enriched_models = []
        on_disk_count = 0

        for m in extracted["models"]:
            on_disk, size = _check_model_on_disk(m["directory"], m["filename"])
            if on_disk:
                on_disk_count += 1
            enriched_models.append({
                **m,
                "on_disk": on_disk,
                "file_size": size,
                "file_size_human": _human_size(size) if size else None,
            })

        total = len(enriched_models)
        results.append({
            "filename": wf_path.name,
            "templates": extracted["templates"],
            "models": enriched_models,
            "models_total": total,
            "models_on_disk": on_disk_count,
            "models_missing": total - on_disk_count,
        })

    # Disk usage for /models mount
    disk_info = {}
    try:
        usage = shutil.disk_usage("/models")
        disk_info = {
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
        }
    except OSError:
        try:
            usage = shutil.disk_usage("/")
            disk_info = {
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
            }
        except OSError:
            pass

    return {"workflows": results, "disk": disk_info}


@app.get("/api/templates/models")
async def templates_models(username: str = Depends(verify_admin)):
    """Deduplicated list of all models across all workflows with on-disk status."""
    workflows_dir = Path("/workflows")
    all_models = {}  # key: (directory, filename) -> model info

    if not workflows_dir.is_dir():
        return {"models": [], "error": "/workflows not mounted"}

    for wf_path in sorted(workflows_dir.glob("*.json")):
        if wf_path.name.startswith("."):
            continue
        try:
            with open(wf_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        extracted = _extract_models_from_workflow(data)
        for m in extracted["models"]:
            key = (m["directory"], m["filename"])
            if key not in all_models:
                on_disk, size = _check_model_on_disk(m["directory"], m["filename"])
                all_models[key] = {
                    **m,
                    "on_disk": on_disk,
                    "file_size": size,
                    "file_size_human": _human_size(size) if size else None,
                    "used_by": [wf_path.name],
                }
            else:
                if wf_path.name not in all_models[key]["used_by"]:
                    all_models[key]["used_by"].append(wf_path.name)
                # Prefer a URL if one is found and existing entry has none
                if not all_models[key].get("url") and m.get("url"):
                    all_models[key]["url"] = m["url"]

    return {"models": list(all_models.values())}


# ============================================================================
# Model Download Engine (Phase 4b)
# ============================================================================

# Download state — single admin user, in-memory is sufficient
_download_state: Dict[str, Any] = {
    "active": False,
    "cancel_requested": False,
    "current_file": None,
    "current_directory": None,
    "bytes_downloaded": 0,
    "bytes_total": 0,
    "files_completed": 0,
    "files_total": 0,
    "files_failed": 0,
    "log": [],
    "error": None,
    "started_at": None,
}
_download_lock = asyncio.Lock()
_download_task: Optional[asyncio.Task] = None


def _append_log(message: str):
    """Add timestamped log line to download state."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {message}"
    _download_state["log"].append(line)
    # Keep log bounded
    if len(_download_state["log"]) > 500:
        _download_state["log"] = _download_state["log"][-300:]
    logger.info(f"[download] {message}")


def _reset_download_state():
    """Clear state for a new download session."""
    _download_state.update({
        "active": False,
        "cancel_requested": False,
        "current_file": None,
        "current_directory": None,
        "bytes_downloaded": 0,
        "bytes_total": 0,
        "files_completed": 0,
        "files_total": 0,
        "files_failed": 0,
        "log": [],
        "error": None,
        "started_at": None,
    })


async def _check_hf_gated(url: str) -> Dict[str, Any]:
    """Check if a HuggingFace URL is gated (requires license acceptance)."""
    result = {
        "accessible": False,
        "gated": False,
        "needs_token": False,
        "model_page": None,
        "content_length": None,
    }

    if not url or "huggingface.co" not in url:
        # Non-HF URL — just check if reachable
        try:
            resp = await http_client.head(url, follow_redirects=True, timeout=15.0)
            result["accessible"] = resp.status_code == 200
            cl = resp.headers.get("content-length")
            if cl:
                result["content_length"] = int(cl)
        except Exception:
            pass
        return result

    # Extract model page from HF resolve URL
    # e.g. https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/...
    try:
        parts = url.split("/resolve/")
        if len(parts) >= 2:
            result["model_page"] = parts[0]
    except Exception:
        pass

    # Try without token first
    try:
        resp = await http_client.head(url, follow_redirects=True, timeout=15.0)
        if resp.status_code == 200:
            result["accessible"] = True
            cl = resp.headers.get("content-length")
            if cl:
                result["content_length"] = int(cl)
            return result
        elif resp.status_code in (401, 403):
            result["gated"] = True
        # 302 to login page also indicates gating
    except Exception:
        pass

    # Try with HF_TOKEN if available
    if HF_TOKEN and result["gated"]:
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            resp = await http_client.head(url, headers=headers, follow_redirects=True, timeout=15.0)
            if resp.status_code == 200:
                result["accessible"] = True
                result["needs_token"] = True
                cl = resp.headers.get("content-length")
                if cl:
                    result["content_length"] = int(cl)
            elif resp.status_code in (401, 403):
                # Token present but not authorized — user needs to accept license
                result["needs_token"] = True
        except Exception:
            pass
    elif result["gated"]:
        result["needs_token"] = True

    return result


async def _download_single_file(url: str, directory: str, filename: str) -> bool:
    """Download a single file with resume support. Returns True on success."""
    target_dir = MODELS_BASE_PATH / directory
    target_dir.mkdir(parents=True, exist_ok=True)
    final_path = target_dir / filename
    temp_path = target_dir / f".{filename}.download"

    _download_state["current_file"] = filename
    _download_state["current_directory"] = directory

    # Resume support — check existing temp file
    existing_bytes = 0
    if temp_path.exists():
        existing_bytes = temp_path.stat().st_size
        _append_log(f"Resuming {filename} from {_human_size(existing_bytes)}")

    headers = {}
    if existing_bytes > 0:
        headers["Range"] = f"bytes={existing_bytes}-"
    if HF_TOKEN and "huggingface.co" in url:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as dl_client:
            async with dl_client.stream("GET", url, headers=headers, follow_redirects=True) as resp:
                if resp.status_code == 416:
                    # Range not satisfiable — file already complete
                    if temp_path.exists():
                        temp_path.rename(final_path)
                    _append_log(f"Already complete: {filename}")
                    return True

                if resp.status_code not in (200, 206):
                    _append_log(f"HTTP {resp.status_code} for {filename}")
                    _download_state["files_failed"] += 1
                    return False

                # Determine total size
                if resp.status_code == 206:
                    # Partial content — parse Content-Range
                    cr = resp.headers.get("content-range", "")
                    if "/" in cr:
                        try:
                            total = int(cr.split("/")[-1])
                            _download_state["bytes_total"] = total
                        except (ValueError, IndexError):
                            pass
                else:
                    # Fresh download — reset existing bytes
                    existing_bytes = 0
                    cl = resp.headers.get("content-length")
                    if cl:
                        _download_state["bytes_total"] = int(cl)

                _download_state["bytes_downloaded"] = existing_bytes
                mode = "ab" if resp.status_code == 206 else "wb"

                with open(temp_path, mode) as f:
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        if _download_state["cancel_requested"]:
                            _append_log(f"Cancelled during {filename}")
                            return False
                        f.write(chunk)
                        _download_state["bytes_downloaded"] += len(chunk)

        # Atomic rename
        temp_path.rename(final_path)
        return True

    except Exception as e:
        _append_log(f"Error downloading {filename}: {e}")
        _download_state["files_failed"] += 1
        return False


async def _run_download_session(models: List[Dict[str, str]]):
    """Sequential download of a list of models."""
    _download_state["active"] = True
    _download_state["files_total"] = len(models)
    _download_state["started_at"] = datetime.now(timezone.utc).isoformat()
    _append_log(f"Starting download session: {len(models)} file(s)")

    for i, model in enumerate(models):
        if _download_state["cancel_requested"]:
            _append_log("Download session cancelled by user")
            break

        filename = model["filename"]
        directory = model["directory"]
        url = model["url"]

        _append_log(f"[{i+1}/{len(models)}] Downloading {directory}/{filename}")
        _download_state["bytes_downloaded"] = 0
        _download_state["bytes_total"] = 0

        success = await _download_single_file(url, directory, filename)
        if success:
            _download_state["files_completed"] += 1
            size_path = MODELS_BASE_PATH / directory / filename
            if size_path.exists():
                _append_log(f"Completed: {filename} ({_human_size(size_path.stat().st_size)})")
            else:
                _append_log(f"Completed: {filename}")

    # Summary
    completed = _download_state["files_completed"]
    failed = _download_state["files_failed"]
    total = _download_state["files_total"]
    cancelled = _download_state["cancel_requested"]

    if cancelled:
        summary = f"Cancelled: {completed}/{total} completed, {failed} failed"
    elif failed > 0:
        summary = f"Done with errors: {completed}/{total} completed, {failed} failed"
    else:
        summary = f"All {completed} file(s) downloaded successfully"

    _append_log(summary)
    _download_state["active"] = False
    _download_state["current_file"] = None
    _download_state["current_directory"] = None

    # Send ntfy notification
    await _send_ntfy(summary, is_error=(failed > 0))


async def _send_ntfy(message: str, is_error: bool = False):
    """Send push notification via ntfy.sh."""
    if not NTFY_TOPIC:
        return
    try:
        headers = {
            "Title": "ComfyuME Model Download",
            "Priority": "high" if is_error else "default",
            "Tags": "warning" if is_error else "white_check_mark",
        }
        await http_client.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            content=message,
            headers=headers,
            timeout=10.0,
        )
        logger.info(f"ntfy notification sent: {message}")
    except Exception as e:
        logger.warning(f"ntfy send failed: {e}")


@app.get("/api/models/check")
async def models_check(username: str = Depends(verify_admin)):
    """All models with on-disk + HF gated status."""
    workflows_dir = Path("/workflows")
    all_models: Dict[tuple, Dict] = {}

    if not workflows_dir.is_dir():
        return {"models": [], "summary": {}, "error": "/workflows not mounted"}

    for wf_path in sorted(workflows_dir.glob("*.json")):
        if wf_path.name.startswith("."):
            continue
        try:
            with open(wf_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        extracted = _extract_models_from_workflow(data)
        for m in extracted["models"]:
            key = (m["directory"], m["filename"])
            if key not in all_models:
                on_disk, size = _check_model_on_disk(m["directory"], m["filename"])
                all_models[key] = {
                    **m,
                    "on_disk": on_disk,
                    "file_size": size,
                    "file_size_human": _human_size(size) if size else None,
                }
            if not all_models[key].get("url") and m.get("url"):
                all_models[key]["url"] = m["url"]

    # Check gated status for missing models with URLs
    models_list = list(all_models.values())
    for m in models_list:
        if not m["on_disk"] and m.get("url"):
            gated_info = await _check_hf_gated(m["url"])
            m["gated_info"] = gated_info
        else:
            m["gated_info"] = None

    # Detect orphaned models (on disk but not referenced by any workflow)
    orphaned = []
    referenced_keys = set(all_models.keys())
    models_root = Path("/models")
    if models_root.is_dir():
        for subdir in sorted(models_root.rglob("*")):
            if subdir.is_file() and subdir.suffix in (".safetensors", ".ckpt", ".pt", ".pth", ".bin"):
                rel = subdir.relative_to(models_root)
                parts = rel.parts
                if len(parts) >= 2:
                    directory = str(Path(*parts[:-1]))
                    filename = parts[-1]
                else:
                    directory = ""
                    filename = parts[0]
                if (directory, filename) not in referenced_keys:
                    try:
                        size = subdir.stat().st_size
                    except OSError:
                        size = None
                    orphaned.append({
                        "filename": filename,
                        "directory": directory,
                        "file_size": size,
                        "file_size_human": _human_size(size) if size else None,
                    })

    # Summary
    total = len(models_list)
    on_disk = sum(1 for m in models_list if m["on_disk"])
    missing = total - on_disk
    downloadable = sum(
        1 for m in models_list
        if not m["on_disk"] and m.get("url") and m.get("gated_info", {}) and m["gated_info"].get("accessible")
    )
    gated_needs_action = sum(
        1 for m in models_list
        if not m["on_disk"] and m.get("gated_info") and m["gated_info"].get("gated") and not m["gated_info"].get("accessible")
    )

    return {
        "models": models_list,
        "orphaned": orphaned,
        "summary": {
            "total": total,
            "on_disk": on_disk,
            "missing": missing,
            "downloadable": downloadable,
            "gated_needs_action": gated_needs_action,
            "hf_token_set": bool(HF_TOKEN),
            "orphaned": len(orphaned),
        },
    }


@app.delete("/api/models/delete")
async def models_delete(body: dict, username: str = Depends(verify_admin)):
    """Delete a model file. Body: {directory, filename}."""
    directory = body.get("directory", "")
    filename = body.get("filename", "")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")
    # Security: resolve and verify path is within /models
    target = (Path("/models") / directory / filename).resolve()
    if not str(target).startswith(str(Path("/models").resolve())):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    size = target.stat().st_size
    target.unlink()
    logger.info(f"[delete] Deleted {directory}/{filename} ({_human_size(size)})")
    return {"deleted": f"{directory}/{filename}", "size": size, "size_human": _human_size(size)}


@app.post("/api/models/download", status_code=202)
async def models_download(body: dict = None, username: str = Depends(verify_admin)):
    """Start a download session. Body: {models: [{filename, directory, url}]} or omit for all missing."""
    global _download_task

    if _download_state["active"]:
        raise HTTPException(status_code=409, detail="Download already in progress")

    if body and body.get("models"):
        models = body["models"]
    else:
        # Auto-detect all missing models with download URLs
        check_result = await models_check(username)
        models = [
            {"filename": m["filename"], "directory": m["directory"], "url": m["url"]}
            for m in check_result["models"]
            if not m["on_disk"]
            and m.get("url")
            and m.get("gated_info", {})
            and m["gated_info"].get("accessible")
        ]

    if not models:
        raise HTTPException(status_code=400, detail="No downloadable models found")

    # Validate each model has required fields
    for m in models:
        if not m.get("filename") or not m.get("url"):
            raise HTTPException(status_code=400, detail=f"Model missing filename or url: {m}")

    _reset_download_state()
    _download_task = asyncio.create_task(_run_download_session(models))

    return {"status": "started", "files": len(models)}


@app.get("/api/models/download/status")
async def models_download_status(username: str = Depends(verify_admin)):
    """Snapshot of current download state."""
    return {
        "active": _download_state["active"],
        "cancel_requested": _download_state["cancel_requested"],
        "current_file": _download_state["current_file"],
        "current_directory": _download_state["current_directory"],
        "bytes_downloaded": _download_state["bytes_downloaded"],
        "bytes_total": _download_state["bytes_total"],
        "files_completed": _download_state["files_completed"],
        "files_total": _download_state["files_total"],
        "files_failed": _download_state["files_failed"],
        "error": _download_state["error"],
        "started_at": _download_state["started_at"],
        "log_lines": len(_download_state["log"]),
    }


@app.get("/api/models/download/stream")
async def models_download_stream(request: Request, username: str = Depends(verify_admin)):
    """SSE stream for real-time download progress."""

    async def event_generator():
        last_log_idx = 0
        last_bytes = 0

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Send new log lines
            current_log = _download_state["log"]
            if len(current_log) > last_log_idx:
                for line in current_log[last_log_idx:]:
                    yield {"event": "log", "data": line}
                last_log_idx = len(current_log)

            # Send progress update if bytes changed
            current_bytes = _download_state["bytes_downloaded"]
            if current_bytes != last_bytes or _download_state["active"]:
                progress_data = json.dumps({
                    "current_file": _download_state["current_file"],
                    "current_directory": _download_state["current_directory"],
                    "bytes_downloaded": _download_state["bytes_downloaded"],
                    "bytes_total": _download_state["bytes_total"],
                    "files_completed": _download_state["files_completed"],
                    "files_total": _download_state["files_total"],
                    "files_failed": _download_state["files_failed"],
                })
                yield {"event": "progress", "data": progress_data}
                last_bytes = current_bytes

            # Check if download finished
            if not _download_state["active"] and _download_state["started_at"]:
                if _download_state["error"]:
                    yield {"event": "error", "data": _download_state["error"]}
                else:
                    complete_data = json.dumps({
                        "files_completed": _download_state["files_completed"],
                        "files_total": _download_state["files_total"],
                        "files_failed": _download_state["files_failed"],
                        "cancelled": _download_state["cancel_requested"],
                    })
                    yield {"event": "complete", "data": complete_data}
                break

            # If no download ever started, just wait briefly then check again
            if not _download_state["started_at"]:
                await asyncio.sleep(1)
                continue

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.post("/api/models/download/cancel")
async def models_download_cancel(username: str = Depends(verify_admin)):
    """Cancel the current download session."""
    if not _download_state["active"]:
        raise HTTPException(status_code=400, detail="No active download to cancel")

    _download_state["cancel_requested"] = True
    _append_log("Cancel requested — stopping after current chunk")
    return {"status": "cancel_requested"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, log_level="info")
