---
description: Run a command on the Verda production server via SSH.
user-invocable: true
---

Run a command on the Verda production server via SSH.

**First:** Read `VERDA_PUBLIC_IP` from `.env` in the project root. Use it as `$VERDA_IP` below.

**Server:** root@$VERDA_IP (Verda CPU instance, aiworkshop.art)

Execute: `ssh root@$VERDA_IP "$ARGUMENTS"`

If no arguments provided, open an interactive check:
1. `ssh root@$VERDA_IP "uptime && df -h / /mnt/models-block-storage && free -h | head -2 && docker ps --format 'table {{.Names}}\t{{.Status}}' | head -5"`

Show the output to the user.
