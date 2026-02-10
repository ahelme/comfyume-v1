---
description: Please pull latest changes from main into the current branch.
user-invocable: true
---

Please pull latest changes from main into the current branch.

**Steps:**
1. Run `git fetch origin main`
2. Show me what's new: `git log --oneline HEAD..origin/main`
3. If there are new commits, merge with `git merge origin/main`
4. Report result (clean merge, conflicts, or already up to date)
