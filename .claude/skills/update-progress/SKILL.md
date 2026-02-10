---
description: Please update the team progress file and central progress file.
user-invocable: true
---

Please update the team progress file and central progress file.

**Detect team from project directory:**
- `/home/dev/projects/comfyume` → `.claude/agent_docs/progress-mello-team-one-dev.md`
- `/home/dev/projects/testing-scripts/comfyume` → `.claude/agent_docs/progress-testing-scripts-team-dev.md`
- `/home/dev/projects/comfyume-admin-panel-team/comfyume` → `.claude/agent_docs/progress-admin-panel-team-dev.md`
- `/home/dev/comfyume` → `.claude/agent_docs/progress-verda-team-one-dev.md`

**Steps:**
1. Identify which team progress file matches the current working directory
2. Update that team's progress file with recent work done this session
3. Update `.claude/agent_docs/progress-all-teams.md` with 1-line-per-commit entries
4. Show me what was added before committing
