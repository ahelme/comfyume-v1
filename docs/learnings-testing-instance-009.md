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
