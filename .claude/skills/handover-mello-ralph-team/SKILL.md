---
description: Handover tasks at 80% context for the Mello Ralph Team (fix loop)
user-invocable: true
---

# HANDOVER TASKS TO BE PERFORMED AT 80% CONTEXT

- YOU MUST update following:
  - gh issues: analyse the FULL SESSION for ALL open issues touched, referenced, or discovered
    - update each with current status, findings, and next steps
    - include any related gh issues (VERY CONCISE)
    - use `gh issue list --repo ahelme/comfyume-v1 --state open --json number,title` to cross-check

  - .claude/qa-state.json
    - CRITICAL: save current test progress, bugs found, iteration count

  - .claude/agent_docs/progress-mello-ralph-team-dev.md
    - update with what you tested, fixed, and what's next

  - .claude/agent_docs/progress-all-teams.md
    - add 1-line commit log entries for work done this session

  - .claude/skills/resume-context-mello-ralph-team/context.md
    - (replace stale instructions with current state)

   - add, commit, push, PR

   - take a moment to feel PROUD of your engineering work :)
