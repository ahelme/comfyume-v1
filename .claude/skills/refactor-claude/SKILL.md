---
description: Refactor the project's CLAUDE.md file using Progressive Disclosure — splitting it into a concise root file and modular agent_docs.
user-invocable: true
---

Refactor the project's CLAUDE.md file using Progressive Disclosure — splitting it into a concise root file and modular agent_docs.

## Background

Claude Code injects CLAUDE.md with a system reminder saying "this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task." This means Claude will ignore large CLAUDE.md files full of task-specific detail. The solution is Progressive Disclosure: keep CLAUDE.md concise and universally applicable, and move task-specific detail into separate files that Claude reads only when needed.

## Principles

1. **CLAUDE.md = Onboarding only.** It should answer: WHAT (tech, stack, structure), WHY (purpose), HOW (key commands, verification). Nothing else.
2. **Less is more.** Fewer instructions = higher compliance. Only universally applicable rules belong in CLAUDE.md.
3. **Pointers not copies.** Don't put code snippets in docs — they go stale. Use `file:line` references to point Claude to authoritative source code.
4. **Progressive Disclosure.** Task-specific knowledge lives in `.claude/agent_docs/` with self-descriptive filenames. CLAUDE.md lists them with 1-line descriptions so Claude can decide which to read.
5. **IF APPLICABLE.** Not every project needs every module. Only create modules that have meaningful content for this project.

## Steps

1. **Read CLAUDE.md in full.** Understand every section and its purpose.

2. **Identify modules.** Group related sections into candidate modules. Use the examples below as a starting point, but adapt to what the project actually contains:

   ```
   .claude/agent_docs/
     - critical_rules.md                 — Non-negotiable rules, user preferences, session checklist
     - architecture.md                   — System design, server roles, code flow diagrams
     - service_communication_patterns.md — API contracts, queue protocols, inter-service messaging (IF APPLICABLE)
     - project_structure.md              — File tree, key directories, critical file locations
     - project_management.md             — Git workflow, commit conventions, issue tracking, progress updates
     - code_conventions.md               — Style guide, naming, patterns, linting rules (IF APPLICABLE)
     - building_the_project.md           — Build steps, dependencies, Docker images (IF APPLICABLE)
     - running_tests.md                  — Test commands, test structure, CI pipeline (IF APPLICABLE)
     - infrastructure.md                 — Servers, storage, Docker, networking
     - security.md                       — Auth, firewall, SSL, VPN, secrets management
     - deployment.md                     — Deploy/restore procedures, prerequisites, scripts
     - database_schema.md                — Schema, migrations, query patterns (IF APPLICABLE)
     - models_and_data.md                — ML models, datasets, data pipelines (IF APPLICABLE)
     - monitoring.md                     — Observability stack, dashboards, alerting
     - gotchas.md                        — Known issues, pitfalls, workarounds
   ```

3. **Assess each candidate.** For each module ask: "Does this project have enough content for this to be its own file?" If not, merge it into a related module or skip it.

4. **Draft the new CLAUDE.md.** It should contain ONLY:
   - Project identity (name, repo, domain, dates) — 5 lines max
   - What this project is — 2-3 sentences
   - Quick links (production URL, health check, admin, API) — if applicable
   - Key commands (build, test, start, deploy) — the HOW
   - The module index: a list of `.claude/agent_docs/*` files with 1-line descriptions
   - Critical rules that MUST be in root (e.g., "never push to main", "update progress on commit") — keep to absolute minimum

5. **Write each module file.** For each:
   - Use a clear header with the module's purpose
   - Migrate content from old CLAUDE.md verbatim (don't rewrite working instructions)
   - Replace inline code snippets with `file:line` pointers where possible
   - Remove stale/outdated content (flag it to the user first)
   - Keep each file focused — if it covers two unrelated topics, split further

6. **Cross-reference check.** Ensure nothing was lost. Every section from the old CLAUDE.md must appear in exactly one module (or be intentionally dropped with user agreement).

7. **Present the plan.** Before writing any files, show the user:
   - Proposed module list with content summary
   - Any sections you recommend dropping (stale, outdated, redundant)
   - Any sections you're unsure how to categorize
   - Get user approval before proceeding

8. **Implement.** Write the new CLAUDE.md and all module files using Write/Edit tools.

9. **Verify.** Read back each file to confirm correctness. Ensure CLAUDE.md's module index matches the actual files created.

## Important

- Do NOT create empty or near-empty module files. Merge thin topics into related modules.
- Do NOT rewrite working instructions. Migrate them as-is, only reformatting for consistency.
- Do NOT add boilerplate, emojis, or filler text to the modules.
- Flag any content that looks outdated and ask the user before removing it.
- The goal is a CLAUDE.md under ~80 lines that gives Claude everything it needs to orient itself and find deeper context on demand.
