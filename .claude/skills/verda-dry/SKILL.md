---
description: Dry — Docker TUI for managing containers on Verda.
user-invocable: true
---

Dry — Docker TUI for managing containers on Verda.

**Server:** root@95.216.229.236
**Docs:** https://moncho.github.io/dry/
**Launch:** `ssh -t root@95.216.229.236 "dry"` (needs -t for TTY)

NOTE: Dry is a TUI (terminal UI) — it requires an interactive terminal.
Claude cannot interact with it directly. Use this skill to:
1. Remind the user how to launch it
2. Suggest non-interactive alternatives for the same info

## Keybindings

| Key | Action |
|-----|--------|
| `F1` | Sort containers |
| `F2` | Toggle show all containers |
| `F5` | Refresh |
| `Enter` | Show container details |
| `l` | Show container logs |
| `s` | Show container stats |
| `i` | Inspect container |
| `r` | Restart container |
| `q` | Quit |

## Non-Interactive Alternatives (for Claude)

```bash
# Container list (like dry main screen)
ssh root@95.216.229.236 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | sort"

# Container stats (like dry 's' key)
ssh root@95.216.229.236 "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | sort"

# Container inspect (like dry 'Enter')
ssh root@95.216.229.236 "docker inspect comfy-$ARGUMENTS 2>/dev/null | python3 -m json.tool | head -50"

# Container logs (like dry 'l')
ssh root@95.216.229.236 "docker logs comfy-$ARGUMENTS --tail 30 2>&1"
```

If $ARGUMENTS provided, run the non-interactive equivalent for that container.
Otherwise tell the user to run `ssh -t root@95.216.229.236 "dry"`.
