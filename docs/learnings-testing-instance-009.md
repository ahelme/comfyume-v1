**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art · staging.aiworkshop.art · testing.aiworkshop.art
**Doc Created:** 2026-02-17
**Doc Updated:** 2026-02-17

# Learnings: Testing Instance 009 (anegg.app)

GitHub Issue: #70
Instance: intelligent-rain-shrinks-fin-01 (65.108.33.80)

## Root Cause: Serverless LB Routing Breaks HTTP Polling (#66)

Verda's load balancer routes each HTTP request to a **different container instance**. When QM calls `POST /prompt` to submit a job, then polls `GET /history/{prompt_id}`, the GET request hits a different container that has no record of the job. Result: empty history, image never retrieved.

**Mitigation with `concurrent_requests_per_replica=1`:** With a single replica, all HTTP requests route to the same instance. HTTP polling should work as-is in this configuration.

**Long-term fix:** SFS-based delivery. Workers write images to `/mnt/sfs/outputs/`, QM watches/polls SFS directly instead of HTTP `/history/`.

## Fix: `--output-directory` Missing on 3/4 Deployments (#54)

Only `h200-spot` had `--output-directory /mnt/sfs/outputs` in its startup command. The other 3 deployments (h200-on-demand, b300-spot, b300-on-demand) wrote to container-local storage, which is ephemeral and lost on scale-down.

**Fix:** Updated `infrastructure/containers.tf` to use `full_cmd` (with `--output-directory`) for all 4 deployments.

## SFS Pseudopath Gotcha

SFS pseudopaths (e.g., `/CLONESFS-Model-Vault-16-Feb-97Es5EBC-aa95d549`) do NOT correspond to Verda IDs and **can change on reboot/remount**. Every mount command must use the current pseudopath.

The CLONE_SFS pseudopath was verified 2026-02-17: `/CLONESFS-Model-Vault-16-Feb-97Es5EBC-aa95d549`

## SFS Share Settings Requirement

SFS volumes must be explicitly shared with each new instance via Verda console "share settings". Without this, the mount command will fail with permission errors.

## Restore Script: Hardcoded Production Values

The restore script (`restore-verda-instance-comfyume-v1.sh`) hardcodes:
- Hostname, instance ID, IP (quiet-city production)
- Domain (aiworkshop.art)
- SSH identity keys (production)
- PUB_KEY_VERDA (old production host key)

**Solution:** Created `-testing.sh` variant with instance 009 values.

## CORS: QM Needs anegg.app Origin

Queue Manager's CORS `allow_origins` must include `https://anegg.app` for the testing domain. Without it, browser requests from anegg.app are blocked by CORS policy.

## LB Routing: Actually Works with Warm Containers

**Correction to original hypothesis:** The HTTP polling approach works when the serverless container is warm. After model loading completes (~5 min cold start), the container stays alive and the LB routes history polls to the correct container.

- **Cold start (first job):** ~307s (5 min model loading + inference). Poll #113 found result.
- **Warm container (subsequent jobs):** ~18s. Poll #10 found result.

The `concurrent_requests_per_replica=1` setting means the POST occupies the container, and GETs may route elsewhere during model loading. Once the model is loaded and the container is idle between polls, routing stabilizes.

## SFS Volume Mismatch Between Environments

Serverless containers mount **PROD_SFS** (configured via `sfs_volume_id` in terraform.tfvars). Testing instance mounts **CLONE_SFS**. These are different volumes. Images written to `/mnt/sfs/outputs/` by serverless containers appear on PROD_SFS, not CLONE_SFS.

**Impact:** SFS-based image delivery (Strategy 1 in QM fetch code) won't work on testing. HTTP `/view` fallback (Strategy 2) works when the container is still alive.

**For production:** Both app server and serverless mount the same PROD_SFS, so SFS delivery would work.

## Permissions: `/outputs/user001` Must Be Writable

The QM container runs as `uid=1000 (queuemanager)`. The host `/mnt/scratch/outputs/` directory must be `chmod 777` and user subdirectories must be pre-created or the parent must allow creation.

**Fix:** `chmod -R 777 /mnt/scratch/outputs/` after provisioning.

## Restore Script: Clones Wrong Repo

The restore script clones `comfy-multi` (old repo) instead of `comfyume-v1` (current). After restore, must manually fix the git remote:
```bash
git remote set-url origin https://github.com/ahelme/comfyume-v1.git
git fetch origin && git checkout <branch>
```

## nginx .htpasswd: Must Be a File Before Docker Start

Docker creates a directory mount if the target file doesn't exist on the host. If `.htpasswd` is missing when containers start, Docker creates a directory at that path, which causes `pread() failed (21: Is a directory)`. The file must exist before `docker compose up`.

## Frontend Container: `requests` Module

ComfyUI v0.11.0 requires `requests` in `frontend_management.py`. The Dockerfile has `pip install ... requests` but if the image was built from the old repo, this may be missing. Rebuild from the correct branch.

## Nginx CORS: Hardcoded Origin

`nginx/nginx.conf` hardcodes `Access-Control-Allow-Origin "https://aiworkshop.art"`. For testing with a different domain, this must be updated (changed to `$http_origin` for flexibility).
