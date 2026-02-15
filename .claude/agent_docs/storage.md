# Verda Storage Options

Reference for storage options on Verda GPU cloud.

## Shared File System (SFS) -- Recommended

- Cost: ~EUR 0.01168/h for 50GB (~$14 AUD/month)
- Network-attached (NFS), mount from any instance
- No provisioning gotchas - just mount and go
- Multiple instances can share same storage
- Mount: `mount -t nfs <sfs-endpoint>:/share /mnt/sfs`
- Structure: `/mnt/sfs/models/` (ComfyUI models), `/mnt/sfs/outputs/` (serverless image output), `/mnt/sfs/cache/` (container, config, scripts)
- **Permissions:** `/mnt/sfs/outputs/` must be `chmod 1777` — serverless containers run as uid 1000, not root
- **Why SFS for outputs:** Serverless containers are load-balanced — HTTP GET to a different instance returns 404. SFS is shared NFS, visible to all containers + app server

## Block Storage -- Alternative

- Cheaper but riskier
- CRITICAL: Gets WIPED if attached during instance provisioning! See CLAUDE.md "CRITICAL: Attaching Block Storage"
- Must use shutdown-attach-boot workflow for existing data
- Only one instance can use it at a time
- Good for scratch disk
