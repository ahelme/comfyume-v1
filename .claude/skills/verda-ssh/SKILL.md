---
description: Run a command on the Verda production server via SSH.
user-invocable: true
---

Run a command on the Verda production server via SSH.

**Server:** root@95.216.229.236 (Verda CPU instance, aiworkshop.art)

Execute: `ssh root@95.216.229.236 "$ARGUMENTS"`

If no arguments provided, open an interactive check:
1. `ssh root@95.216.229.236 "uptime && df -h / /mnt/models-block-storage && free -h | head -2 && docker ps --format 'table {{.Names}}\t{{.Status}}' | head -5"`

Show the output to the user.
