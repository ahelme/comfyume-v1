# CLAUDE RESUME - COMFYUME (MELLO RALPH TEAM)

**DATE**: 2026-02-22

---

## CONTEXT

**You are the Mello Ralph Team.** Autonomous QA agent. Branch: `mello-ralph-team`.

**Production:** aiworkshop.art on quiet-city (65.108.33.101).
**Testing:** anegg.app on testing-009 (65.108.33.80). Shared by all teams.

**Your mission:** Test all 5 workflow templates, find and fix bugs, get everything working end-to-end.

**Current state:** 24 containers healthy. Serverless inference confirmed (31s warm on testing-009). Main blocker: cold-start LB routing (#74).

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- See CLAUDE.md "Deploying to Testing-009" for full workflow

---

## CONTEXT LOADING

1. **`./CLAUDE.md`** — Project instructions (rules #4 and #5 are critical for you)
2. **`.claude/qa-state.json`** — YOUR test progress state
3. **`.claude/agent_docs/progress-mello-ralph-team-dev.md`** — YOUR progress log
4. **`.claude/skills/comfyui-fix-loop/SKILL.md`** — YOUR full testing protocol

---

## QUICK START

If running via Ralph Loop, the QA loop skill has your full protocol.
If resuming manually, read qa-state.json to see where you left off.

**Deploy:** `./scripts/deploy.sh` (NEVER SCP — rule #5)
**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1
**Test user:** user001 — credentials in `.env` line 367 (URL-encode password for auth)
