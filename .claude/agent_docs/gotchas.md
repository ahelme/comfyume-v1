# Gotchas -- Known Issues, Pitfalls, Workarounds

For critical gotchas see CLAUDE.md "CRITICAL GOTCHAS" section.

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
