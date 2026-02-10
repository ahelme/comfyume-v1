# Git Workflow & Project Management

## Commit Guidelines

Use conventional commit format:
```
feat: add queue manager REST API endpoints
fix: resolve nginx routing for user/20
docs: update admin guide with priority override
test: add integration tests for worker
```

No boasting in commit messages.

## When to Commit

- End of each major feature
- Before trying risky changes
- End of each session
- When tests pass
- Always update progress files after commits (use `/update-progress`)

## Task Management

- **ALWAYS reference GitHub issue numbers** (e.g., #15, #22, #13)
- **DO NOT use internal task numbers** (no Task #1, Task #2, etc.)
- **If no GitHub issue exists**, create one first before tracking work

## Issue Tracking

- **ComfyuME v1 (active)**: https://github.com/ahelme/comfyume-v1/issues
- **ComfyuME (original)**: https://github.com/ahelme/comfyume/issues
- **Private Scripts Repo**: https://github.com/ahelme/comfymulti-scripts/issues
- **gh CLI gotcha:** `gh issue view` fails with "Projects (classic) deprecated" error. Use `--json` flag instead: `gh issue view 8 --json title,body,state`
