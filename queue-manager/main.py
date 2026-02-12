"""
Queue Manager - FastAPI Application
Main entrypoint for the job queue management service

Supports three inference modes:
- local: GPU on same machine, workers poll Redis queue
- redis: Remote GPU via Tailscale, workers poll Redis queue
- serverless: Direct HTTP to Verda Serverless (auto-scaling)
"""
import logging
import asyncio
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    Job, JobSubmitRequest, JobCompletionRequest, JobFailureRequest,
    JobResponse, QueueStatus, HealthCheck, JobStatus, QueueMode, JobPriority
)
from config import settings
from redis_client import RedisClient
from websocket_manager import WebSocketManager

# HTTP client for serverless mode
serverless_client: Optional[httpx.AsyncClient] = None

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
redis_client: Optional[RedisClient] = None
ws_manager: Optional[WebSocketManager] = None
app_start_time: datetime = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, ws_manager, serverless_client

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Inference mode: {settings.inference_mode}")

    redis_client = RedisClient()
    ws_manager = WebSocketManager(redis_client)

    # Initialize serverless client if needed
    if settings.inference_mode == "serverless":
        endpoint = settings.active_serverless_endpoint
        if not endpoint:
            logger.warning("No serverless endpoint configured - serverless mode will fail!")
            logger.warning("Set SERVERLESS_ENDPOINT or SERVERLESS_ENDPOINT_H200/B300 with SERVERLESS_ACTIVE")
        else:
            # Build headers with API key if configured
            headers = {}
            if settings.serverless_api_key:
                headers["Authorization"] = f"Bearer {settings.serverless_api_key}"
                logger.info("Serverless API key configured")
            else:
                logger.warning("No SERVERLESS_API_KEY configured - requests may fail!")

            serverless_client = httpx.AsyncClient(
                base_url=endpoint,
                timeout=httpx.Timeout(300.0),  # 5 min timeout for inference
                headers=headers
            )
            logger.info(f"Serverless client initialized: {endpoint}")
            logger.info(f"Active GPU: {settings.active_gpu_type}")

    # Start background tasks
    asyncio.create_task(cleanup_task())

    logger.info("Queue Manager started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Queue Manager")
    if serverless_client:
        await serverless_client.aclose()


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS middleware - Security: Only allow specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://comfy.ahelme.net",
        "https://www.comfy.ahelme.net",
        "https://aiworkshop.art",
        "https://admin.aiworkshop.art",
        "https://*.aiworkshop.art",  # User subdomains
        "http://localhost:8080",  # For local admin dashboard testing
    ],
    allow_credentials=False,  # Disabled for security - no cookies needed
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthCheck)
@app.get("/api/health", response_model=HealthCheck, include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now(timezone.utc) - app_start_time).total_seconds()

    # Get active endpoint for serverless mode (redact full URL for security)
    endpoint_display = None
    if settings.inference_mode == "serverless" and settings.active_serverless_endpoint:
        # Show just the deployment name, not full URL
        endpoint = settings.active_serverless_endpoint
        endpoint_display = endpoint.split("//")[-1].split(".")[0] if "//" in endpoint else endpoint

    return HealthCheck(
        status="healthy" if redis_client.ping() else "unhealthy",
        version=settings.app_version,
        inference_mode=settings.inference_mode,
        active_gpu=settings.active_gpu_type,
        serverless_endpoint=endpoint_display,
        redis_connected=redis_client.ping(),
        workers_active=0,  # TODO: Track active workers
        queue_depth=redis_client.get_queue_depth(),
        uptime_seconds=int(uptime)
    )


@app.get("/api/queue/status", response_model=QueueStatus)
async def get_queue_status():
    """Get overall queue status - optimized with batched Redis calls"""
    try:
        # Performance: Get all queue stats in single pipeline call (4→1 Redis commands)
        stats = redis_client.get_all_queue_stats()

        return QueueStatus(
            mode=QueueMode(settings.queue_mode),
            pending_jobs=stats["pending"],
            running_jobs=stats["running"],
            completed_jobs=stats["completed"],
            failed_jobs=stats["failed"],
            total_workers=settings.num_workers,
            active_workers=0,  # TODO: Implement worker tracking
            queue_depth=stats["pending"]
        )
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Job Management Endpoints
# ============================================================================

async def poll_serverless_history(prompt_id: str, max_wait: int = 600, poll_interval: float = 2.0) -> dict:
    """Poll serverless /api/history/{prompt_id} until execution completes.

    Serverless cold start + model loading can block HTTP for 200+ seconds.
    With 10s per-poll timeout, we fail fast and retry often.
    max_wait=600 covers worst case: cold start + model load + inference.
    """
    if not serverless_client:
        raise HTTPException(status_code=503, detail="Serverless client not initialized")

    import time
    start_time = time.monotonic()
    poll_count = 0

    while (time.monotonic() - start_time) < max_wait:
        poll_count += 1
        elapsed = time.monotonic() - start_time
        try:
            # 10s timeout: fail fast when server is blocked by model loading
            response = await serverless_client.get(
                f"/history/{prompt_id}",
                timeout=httpx.Timeout(10.0),
            )
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    entry = history[prompt_id]
                    status = entry.get("status", {})
                    completed = status.get("completed", False)
                    status_str = status.get("status_str", "unknown")

                    # Always log when found in history (important for debugging)
                    if poll_count <= 5 or poll_count % 15 == 0 or completed:
                        outputs = entry.get("outputs", {})
                        output_summary = {
                            nid: list(nout.keys()) for nid, nout in outputs.items()
                        }
                        logger.info(
                            f"History poll #{poll_count} ({elapsed:.0f}s): "
                            f"completed={completed}, status={status_str}, "
                            f"outputs={output_summary}"
                        )
                    elif poll_count % 10 == 0:
                        logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): completed={completed}, status={status_str}")

                    if completed:
                        logger.info(f"Execution completed after {elapsed:.0f}s ({poll_count} polls)")
                        return entry
                else:
                    if poll_count <= 3 or poll_count % 30 == 0:
                        logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): prompt_id not in history. Keys: {list(history.keys())[:5]}")
            else:
                logger.warning(f"History poll #{poll_count} ({elapsed:.0f}s): HTTP {response.status_code}")
        except httpx.TimeoutException:
            # Only log periodically — timeout is expected during model loading
            if poll_count <= 2 or poll_count % 10 == 0:
                logger.info(f"History poll #{poll_count} ({elapsed:.0f}s): timeout (server busy, likely loading model)")
        except Exception as e:
            logger.warning(f"History poll #{poll_count} ({elapsed:.0f}s): error: {type(e).__name__}: {e}")

        await asyncio.sleep(poll_interval)

    raise HTTPException(status_code=504, detail=f"Serverless execution timed out after {max_wait}s ({poll_count} polls)")


async def fetch_serverless_images(history_entry: dict) -> list:
    """Download output images from serverless container based on history entry."""
    if not serverless_client:
        return []

    images = []
    outputs = history_entry.get("outputs", {})

    # Debug: log full output structure when investigating image delivery
    if not outputs:
        logger.warning(f"History entry has no outputs. Top-level keys: {list(history_entry.keys())}")
    else:
        for nid, nout in outputs.items():
            logger.info(f"Output node {nid}: keys={list(nout.keys())}, images={len(nout.get('images', []))}")

    for node_id, node_output in outputs.items():
        for img_info in node_output.get("images", []):
            filename = img_info.get("filename")
            subfolder = img_info.get("subfolder", "")
            img_type = img_info.get("type", "output")

            if not filename:
                continue

            try:
                params = {"filename": filename, "type": img_type}
                if subfolder:
                    params["subfolder"] = subfolder

                response = await serverless_client.get("/view", params=params)
                if response.status_code == 200:
                    images.append({
                        "data": response.content,
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type,
                        "node_id": node_id,
                        "content_type": response.headers.get("content-type", "image/png"),
                    })
                    logger.info(f"Downloaded image: {filename} ({len(response.content)} bytes)")
                else:
                    logger.warning(f"Failed to download {filename}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"Error downloading {filename}: {e}")

    return images


async def save_output_images(user_id: str, images: list) -> dict:
    """Save downloaded images to the shared output directory.
    Returns ComfyUI-compatible output metadata (node_id -> {images: [...]}).
    """
    output_dir = Path(settings.outputs_path) / user_id
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_outputs = {}

    for img in images:
        node_id = img["node_id"]
        filename = img["filename"]

        save_path = output_dir / filename
        save_path.write_bytes(img["data"])
        logger.info(f"Saved: {save_path}")

        if node_id not in saved_outputs:
            saved_outputs[node_id] = {"images": []}

        saved_outputs[node_id]["images"].append({
            "filename": filename,
            "subfolder": user_id,
            "type": "output",
        })

    return saved_outputs


async def submit_to_serverless(workflow: dict, user_id: str) -> dict:
    """Submit workflow to serverless, wait for completion, fetch and save output images."""
    if not serverless_client:
        raise HTTPException(
            status_code=503,
            detail="Serverless client not initialized. Check SERVERLESS_ENDPOINT."
        )

    try:
        # 1. Submit prompt to serverless ComfyUI
        logger.info(f"Sending to serverless: {len(workflow)} nodes")
        response = await serverless_client.post(
            "/prompt",
            json={"prompt": workflow, "client_id": user_id}
        )
        response.raise_for_status()
        result = response.json()
        prompt_id = result.get("prompt_id")
        logger.info(f"Serverless prompt accepted: {prompt_id}")

        if not prompt_id:
            logger.error(f"No prompt_id in serverless response: {result}")
            return result

        # 2. Poll history until execution completes
        logger.info(f"Polling for execution completion: {prompt_id}")
        history_entry = await poll_serverless_history(prompt_id)

        status = history_entry.get("status", {})
        if status.get("status_str") != "success":
            messages = status.get("messages", [])
            logger.error(f"Execution failed: {messages}")
            result["execution_error"] = messages
            return result

        logger.info(f"Execution completed successfully: {prompt_id}")

        # 3. Download output images from serverless container
        images = await fetch_serverless_images(history_entry)
        logger.info(f"Downloaded {len(images)} image(s)")

        if not images:
            logger.warning(f"No images in execution output for {prompt_id}")
            result["outputs"] = history_entry.get("outputs", {})
            return result

        # 4. Save images to shared output directory (/outputs/{user_id}/)
        saved_outputs = await save_output_images(user_id, images)

        # 5. Return complete result with output metadata
        result["outputs"] = saved_outputs
        result["execution_status"] = "success"
        return result

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Serverless inference timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"Serverless response body: {e.response.text[:500]}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Serverless submission failed: {e}")
        raise HTTPException(status_code=502, detail=f"Serverless error: {e}")


@app.post("/api/jobs", response_model=JobResponse, status_code=201)
async def submit_job(request: JobSubmitRequest):
    """Submit a new job - routes based on INFERENCE_MODE"""
    try:
        # SERVERLESS MODE: Direct HTTP to serverless endpoint (no queue)
        if settings.inference_mode == "serverless":
            logger.info(f"Serverless job from user {request.user_id}")

            # Submit directly to serverless
            result = await submit_to_serverless(request.workflow, request.user_id)

            # Create a completed job record
            job = Job(
                user_id=request.user_id,
                workflow=request.workflow,
                priority=request.priority,
                metadata=request.metadata
            )
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now(timezone.utc)

            return JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                priority=job.priority,
                created_at=job.created_at,
                started_at=job.created_at,
                completed_at=job.completed_at,
                worker_id="serverless",
                result=result,
                error=None,
                position_in_queue=None
            )

        # LOCAL/REDIS MODE: Queue-based (workers poll for jobs)
        # Check queue depth limit
        if settings.max_queue_depth > 0:
            current_depth = redis_client.get_queue_depth()
            if current_depth >= settings.max_queue_depth:
                raise HTTPException(
                    status_code=429,
                    detail=f"Queue is full (max depth: {settings.max_queue_depth})"
                )

        # Create job
        job = Job(
            user_id=request.user_id,
            workflow=request.workflow,
            priority=request.priority,
            metadata=request.metadata
        )

        # Save to Redis
        if not redis_client.create_job(job):
            raise HTTPException(status_code=500, detail="Failed to create job")

        # Get queue position
        pending_jobs = redis_client.get_pending_jobs()
        position = next((i for i, j in enumerate(pending_jobs) if j.id == job.id), None)

        logger.info(f"Job {job.id} submitted by user {job.user_id} (mode: {settings.inference_mode})")

        return JobResponse(
            id=job.id,
            user_id=job.user_id,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            started_at=None,
            completed_at=None,
            worker_id=None,
            result=None,
            error=None,
            position_in_queue=position
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status by ID"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Calculate position in queue if pending
        position = None
        if job.status == JobStatus.PENDING:
            pending_jobs = redis_client.get_pending_jobs()
            position = next((i for i, j in enumerate(pending_jobs) if j.id == job_id), None)

        return JobResponse(
            id=job.id,
            user_id=job.user_id,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            worker_id=job.worker_id,
            result=job.result,
            error=job.error,
            position_in_queue=position
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    user_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    limit: int = 100
):
    """List jobs with optional filters"""
    try:
        if user_id:
            jobs = redis_client.get_user_jobs(user_id)
        else:
            # Get from all queues
            jobs = redis_client.get_pending_jobs(limit)
            # TODO: Add running, completed, failed

        # Filter by status if specified
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Performance: Cache position lookup to avoid O(n²) - fetch once, not per job
        pending_jobs = redis_client.get_pending_jobs()
        job_positions = {j.id: i for i, j in enumerate(pending_jobs)}

        # Convert to response models
        responses = []
        for job in jobs[:limit]:
            # O(1) lookup instead of O(n) search
            position = job_positions.get(job.id) if job.status == JobStatus.PENDING else None

            responses.append(JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                priority=job.priority,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                worker_id=job.worker_id,
                result=job.result,
                error=job.error,
                position_in_queue=position
            ))

        return responses

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str):
    """Cancel a job"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status == JobStatus.RUNNING:
            # Mark as cancelled, worker will handle cleanup
            job.status = JobStatus.CANCELLED
            redis_client.update_job(job)
            logger.info(f"Job {job_id} marked for cancellation")
        elif job.status == JobStatus.PENDING:
            # Remove from queue
            redis_client.delete_job(job_id)
            logger.info(f"Job {job_id} cancelled and removed from queue")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job in {job.status} state"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.patch("/api/jobs/{job_id}/priority")
async def update_job_priority(job_id: str, priority: JobPriority):
    """Update job priority (admin/instructor only)"""
    try:
        job = redis_client.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change priority of {job.status} job"
            )

        # Update priority
        job.priority = priority
        redis_client.update_job(job)

        # Re-score in queue
        score = redis_client._get_priority_score(job)
        redis_client.redis.zadd(redis_client.QUEUE_PENDING, {job_id: score})

        logger.info(f"Updated job {job_id} priority to {priority}")

        return {"status": "success", "job_id": job_id, "priority": priority}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id} priority: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# Worker Endpoints
# ============================================================================

@app.get("/api/workers/next-job")
async def get_next_job(worker_id: str):
    """Get next job for worker to process"""
    try:
        # Update worker heartbeat
        redis_client.update_worker_heartbeat(worker_id)

        # Get next job based on queue mode
        queue_mode = QueueMode(settings.queue_mode)
        job = redis_client.get_next_job(queue_mode)

        if not job:
            return {"job": None}

        # Move to running
        redis_client.move_job_to_running(job.id, worker_id)

        logger.info(f"Assigned job {job.id} to worker {worker_id}")

        return {
            "job": {
                "id": job.id,
                "workflow": job.workflow,
                "user_id": job.user_id,
                "metadata": job.metadata
            }
        }

    except Exception as e:
        logger.error(f"Failed to get next job for worker {worker_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/workers/complete-job")
async def complete_job(job_id: str, request: JobCompletionRequest):
    """Mark job as completed - with validated result payload"""
    try:
        # Validation happens automatically via Pydantic model
        if not redis_client.move_job_to_completed(job_id, request.result):
            raise HTTPException(status_code=404, detail="Job not found")

        logger.info(f"Job {job_id} completed successfully")
        return {"status": "success", "job_id": job_id}

    except HTTPException:
        raise
    except ValueError as e:
        # Pydantic validation error
        logger.warning(f"Invalid result payload for job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/workers/fail-job")
async def fail_job(job_id: str, request: JobFailureRequest):
    """Mark job as failed - with validated error message"""
    try:
        # Validation happens automatically via Pydantic model
        if not redis_client.move_job_to_failed(job_id, request.error):
            raise HTTPException(status_code=404, detail="Job not found")

        logger.error(f"Job {job_id} failed: {request.error}")
        return {"status": "success", "job_id": job_id}

    except HTTPException:
        raise
    except ValueError as e:
        # Pydantic validation error
        logger.warning(f"Invalid error message for job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(f"pong: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


# ============================================================================
# Background Tasks
# ============================================================================

async def cleanup_task():
    """Background task to cleanup stale jobs"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            redis_client.cleanup_stale_jobs(settings.job_timeout)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Log full traceback with request context for debugging
    logger.exception(
        f"Unhandled exception in {request.method} {request.url.path}: {exc}"
    )

    # Show detailed error in development mode for faster debugging
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method
            }
        )

    # Generic response in production (security best practice)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
