---
description: Please update the team progress file and central progress file.
user-invocable: true
---

Please update the team progress file and central progress file.

**Detect team from project directory:**
- `/home/dev/projects/testing-mello-team-one` → `.claude/agent_docs/progress-mello-team-one-dev.md`
- `/home/dev/projects/testing-mello-scripts-team` → `.claude/agent_docs/progress-mello-scripts-team-dev.md`
- `/home/dev/projects/testing-mello-admin-panel-team` → `.claude/agent_docs/progress-mello-admin-panel-team-dev.md`
- `/home/dev/comfyume` → `.claude/agent_docs/progress-verda-team-one-dev.md`

**Steps:**
1. Identify which team progress file matches the current working directory
2. Update that team's progress file with recent work done this session
3. Update `.claude/agent_docs/progress-all-teams.md` with 1-line-per-commit entries
4. **Update relevant GitHub issues** — add a comment to any GH issues worked on this session with a concise status update (what was done, what's pending). Use `gh issue comment <number> --body "..."`. If an issue is now fully resolved, close it with `gh issue close <number>`.
5. Show me what was added before committing
