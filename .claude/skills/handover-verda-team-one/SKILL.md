---
description: Handover tasks at 80% context for Verda Team One
user-invocable: true
---

# HANDOVER TASKS TO BE PERFORMED AT 80% CONTEXT

- YOU MUST update following:
    - gh issues: analyse the FULL SESSION for ALL open issues touched, referenced, or discovered
        - update each with current status, findings, and next steps
        - include any related gh issues (VERY CONCISE - JUST INFO NEEDED/HELPFUL/RELEVANT)
        - use `gh issue list --repo ahelme/comfyume-v1 --state open --json number,title` to cross-check
    - .claude/agent_docs/progress-verda-team-one-dev.md
        - **MANDATORY:** Clean up Task Management section
            - Remove completed/outdated tasks
            - Add current work with correct issue numbers
            - Verify all issue references are accurate
            - Discuss with user before finalizing
    - .claude/agent_docs/progress-all-teams.md
        - add 1-line commit log entries for work done this session
    - .claude/skills/resume-context-verda-team-one/context.md
        - (replace stale instructions)
    - check code has been commented effectively
    - add, commit, push
    - PR at end of any major block of work
