# CLAUDE RESUME - COMFYUME (MELLO TEAM ONE)

**DATE**: 2026-02-11

---

## CONTEXT

**We are Mello Team One.** Main dev team. Branch: `main`.

**Production:** aiworkshop.art runs on quiet-city (65.108.33.101), a Verda CPU instance.

**Current state:** PRODUCTION LIVE. 24 containers healthy. Serverless inference confirmed working.
Main blocker: output images stay on serverless container — never reach user's browser.

**All code committed, server in sync (6714c79). No deployment drift.**

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** — Project instructions (Critical Instructions #4 and #5 are NEW)
2. **`.claude/agent_docs/progress-mello-team-one-dev.md`** (top ~100 lines) — Priority tasks + Report 47
3. **`git log --oneline -10`** — Recent commits

---

## IMMEDIATE NEXT STEPS

1. **Run fix loop** (the main goal of this handover):
   ```
   /ralph-loop "/comfyui-fix-loop" --max-iterations 50 --completion-promise "ALL_WORKFLOWS_PASSING"
   ```
   This tests all 5 workflows via Chrome DevTools, debugs issues with curiosity, fixes via git flow.

2. **The BIG unsolved problem — image delivery:**
   - Serverless GPU generates images but they're saved on the remote container's filesystem
   - ComfyUI `/prompt` returns only `{prompt_id, number, node_errors}` — NOT images
   - Images normally come via WebSocket, but QM is the HTTP client, not the user's browser
   - Need to figure out how to get images back (S3 upload? WebSocket relay? HTTP response?)

3. **Other pending:**
   - Complete app flow doc (#8), infrastructure config map (#9)
   - Investigate .env variable warnings (#7) — y1w, HUFr7, etc.
   - Run setup-monitoring.sh (Prometheus, Grafana, Loki)

---

## KEY ARCHITECTURE (quick reference)

```
Browser → redirect.js intercepts Queue Prompt
  → POST /api/jobs → nginx → queue-manager:3000
  → QM submit_to_serverless() → POST to DataCrunch H200 /prompt
  → Response: {prompt_id, number, node_errors} (IMMEDIATE, async)
  → QM returns JobResponse with status:completed to browser
  → redirect.js shows floating status banner
  → BUT: images are on serverless container, NOT in UI
```

**Key files:**
| File | Purpose |
|------|---------|
| `comfyume-extensions/queue_redirect/web/redirect.js` | Job submission + GPU progress banner |
| `comfyume-extensions/extensions.conf` | Enable/disable extensions (queue_redirect ON, loader OFF) |
| `queue-manager/main.py` | Job routing to serverless |
| `comfyui-frontend/Dockerfile` | Build context is project root (.) |
| `comfyui-frontend/docker-entrypoint.sh` | Config-driven extension deployment |
| `scripts/deploy.sh` | Git-based deploy: push → pull → rebuild → recreate |
| `.claude/qa-state.json` | fix loop state (persists between Ralph Loop iterations) |

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — CLAUDE.md rule #5)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

---

## SESSION START CHECKLIST

- [ ] `git status` — should be clean
- [ ] SSH to Verda: `ssh root@65.108.33.101 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c healthy'` (expect 24)
- [ ] Read `.claude/qa-state.json` for fix loop state
