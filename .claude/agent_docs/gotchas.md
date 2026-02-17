# Gotchas -- Known Issues, Pitfalls, Workarounds

For critical gotchas see CLAUDE.md "CRITICAL GOTCHAS" section.

## Verda SFS Console Rename → Pseudopath Change Risk

Renaming a Verda SFS console name (e.g. adding `PROD_` prefix) may cause the **pseudopath to change on next shutdown/remount**. The pseudopath is used in NFS mount commands across all restore scripts. If it changes, mounts silently fail.

**After any SFS console rename or instance reboot:**
1. Check current pseudopath in Verda console
2. Update `VERDA_MODELS_SFS_PSEUDOPATH` in both `.env` files
3. Update mount commands in `restore-verda-instance*.sh` and `setup-verda-solo-script.sh`
4. Update `infrastructure-registry.md` S-03 and S-04 fields

**Renamed 2026-02-15:** `SFS-Model-Vault-22-Jan-01-4xR2NHBi` → `PROD_SFS-Model-Vault-22-Jan-01-4xR2NHBi`. Pseudopath may change from `/SFS-Model-Vault-22-Jan-01-4xR2NHBi-c3d75d76` on next reboot.

## Verda SFS Requires "Share Settings" Per Instance

SFS volumes must be explicitly shared with each instance via Verda console ("share settings"). Being in the same location (FIN-01) is not enough — mount will fail with "No such file or directory" until the instance is added to the SFS share list.

## Verda Rebrand (ex. DataCrunch)

Verda was previously called "DataCrunch". The rebrand means:
- **ALL docs, code comments, specs** must reference **Verda**, not DataCrunch
- **API endpoint URLs** may still use `containers.datacrunch.io` — verify current domain before updating URLs
- **When writing new docs**: always use "Verda". First mention in standalone docs: "Verda (ex. DataCrunch)"
- **Check for stale refs**: search for `DataCrunch` / `datacrunch` across the entire codebase when touching related files

## Issue #54 RESOLVED: Workflow Save/Load Now Working

**Issue #54: Workflow save/load was broken** -- POST to userdata API returned 405 through nginx

**Root Cause:** nginx `proxy_pass` with trailing slash (`http://backend/;`) decodes URL-encoded characters. ComfyUI requires encoded slashes (`%2F`) in path parameters like `/userdata/workflows%2Ffile.json`.

**Fix Applied (2026-02-05):**
1. Created `/etc/nginx/conf.d/comfyui-userdata-maps.conf` with maps that extract paths from `$request_uri` (preserves encoding)
2. Updated all user location blocks to use `proxy_pass http://backend$userXXX_raw_path$is_args$args;`

**Reference:** [ComfyUI PR #6376](https://github.com/comfyanonymous/ComfyUI/pull/6376)

**Files:**
- `/etc/nginx/conf.d/comfyui-userdata-maps.conf` - Map definitions (live server)
- `nginx/conf.d/comfyui-userdata-maps.conf` - Map definitions (repo)
- `nginx/docker-entrypoint.sh` - Updated to generate maps for containerized nginx

## Health Checks Require Dependencies

**Dockerfile must include:**
- `curl` - Health check uses `CMD ["curl", "-f", "http://localhost:8188/"]`
- `libgomp1` - Required for torchaudio (audio nodes), prevents libgomp.so.1 errors
- `requests` (Python) - Required by frontend (added to requirements.txt in v0.11.0)

**Symptoms if missing:**
- No curl: Health checks timeout after 60s, containers marked unhealthy
- No libgomp1: Audio nodes import errors (non-fatal but noisy logs)
- No requests: `ModuleNotFoundError: No module named 'requests'` on startup

## Silent Failures on Large File Operations

**Why this matters:** Operations report success while actually failing. Hours wasted redownloading, deploying apps that won't work, discovering missing data at critical moments.

**Root causes:**
- **Disk space issues**: /tmp full -> silent failure
- **Silent failures**: AWS CLI returns success even when operations fail
- **Incomplete backups**: Assumed complete, weren't verified
- **Lack of verification**: No immediate check of results after operations

**How to avoid:**

1. **Check disk space FIRST** -- run `disk-check.sh` before any large operation (or `disk-check.sh --block` to abort if >90% full):
   ```bash
   df -h /tmp /mnt/sfs  # before any large operation
   ```

2. **Use adequate temp space**:
   ```bash
   TMPDIR=/mnt/sfs/tmp  # for large downloads
   ```

3. **Verify immediately after operations**:
   ```bash
   find /target -type f | wc -l  # file count
   du -sh /target                # total size
   ```

4. **Compare source vs destination**:
   ```bash
   aws s3 ls --recursive | wc -l  # source count
   find /local -type f | wc -l     # dest count
   ```

5. **Use checksums**: Generate md5sums for all files and verify

6. **Manifest-driven operations**: Create expected file list FIRST, then verify against it

7. **Explicit verification in scripts**: Don't trust exit codes alone - check actual results
