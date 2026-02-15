---
description: "Autonomous fix loop: test ComfyUI workflows via Chrome DevTools, diagnose issues, engineer solutions via git flow, deploy, verify, repeat."
user-invocable: true
---

# ComfyUI Fix Loop

You are an autonomous engineering agent fixing ComfyUI workflows on aiworkshop.art.
Your goal: make the Flux2 Klein 9B workflow run successfully with full native UI feedback, including image output.

**IMPORTANT: This skill is designed for use with Ralph Loop.**
Run: `/ralph-loop "/comfyui-fix-loop" --max-iterations 50 --completion-promise "ALL_WORKFLOWS_PASSING"`
Or run standalone — follow the loop manually.

---

## CONTEXT MANAGEMENT

Ralph Loop naturally resets context between iterations (stop hook feeds the same prompt back).
Your state persists in `.claude/qa-state.json` — read it FIRST every iteration.

**SAVE STATE FREQUENTLY:**
- Update qa-state.json after EVERY phase (not just at the end)
- If you're about to make a complex change, save state BEFORE starting
- If context feels large (you've been reading many files), save state and let the iteration end
- Git commit early and often — your work survives context resets

**KEEP ITERATIONS FOCUSED:**
- One workflow per iteration maximum
- If a bug requires deep investigation, that's one iteration
- If the fix requires changes + deploy + re-test, that can be a second iteration
- Don't try to test all 5 workflows in one iteration

---

## MINDSET

**STOP. BREATHE. THINK.**

You are NOT in a rush. You are a curious engineer exploring a system.
When you find a bug:
1. Observe it fully — read every error, check every log
2. Understand WHY it happens — trace the code path
3. Consider multiple approaches — don't jump to the first fix
4. Sleep on it (metaphorically) — re-read your analysis before coding
5. Fix at the source — not a quick hack
6. Test that the fix works — don't assume

**DO NOT:**
- Rush to fix something you don't understand
- SCP files directly to the server (use `./scripts/deploy.sh`)
- Skip reading the code before modifying it
- Make multiple changes at once — one fix, one test, one commit

---

## SCOPE

Test this ONE workflow ONLY:

| # | Workflow | Type | File |
|---|---------|------|------|
| 1 | Flux2 Klein 9B | Text → Image | `flux2_klein_9b_text_to_image.json` |

**Success criteria for EACH workflow (all must pass):**
- [ ] Workflow loads onto canvas (all nodes visible, no missing node errors)
- [ ] Queue Prompt button responds (click → visible feedback)
- [ ] Status banner shows progress ("Sending to GPU..." → "Processing..." → "Complete!")
- [ ] Job reaches QM and is sent to serverless (check QM logs)
- [ ] Output appears in ComfyUI UI (image preview or video player)
- [ ] No uncaught errors in browser console
- [ ] Queue history shows the completed job

---

## LOOP PROTOCOL

### Phase 0: CONTEXT LOAD (every iteration start)

**Do this FIRST, silently, without stopping for user input.**

```
1. Read resume context (DO NOT invoke the skill interactively — just read the file):
   Read: .claude/skills/resume-context-mello-ralph-team/context.md
   Read: CLAUDE.md (skim Critical Instructions)

2. Read QA state:
   Read: .claude/qa-state.json

3. Increment iteration counter in qa-state.json

4. Continue IMMEDIATELY to Phase 1 — do NOT ask the user anything.
```

### Phase 1: OBSERVE — Check current state

Before testing anything, understand where things stand.

```
1. Check container health:
   SSH: docker ps --format "table {{.Names}}\t{{.Status}}" | grep comfy | sort

3. Check QM is healthy:
   SSH: docker logs comfy-queue-manager 2>&1 | grep -v "GET /health" | tail -10

4. Check git status — are we in sync?
   Local: git status
   Compare local HEAD with server HEAD
```

### Phase 2: TEST — Try the next workflow

Pick the next untested workflow from the state file (or start with #1).

```
1. Navigate to test user (user001):
   → Read credentials from `.env` line 367 (USER_CREDENTIALS_USER001)
   → URL-encode the password, then use: https://user001:<encoded-pass>@aiworkshop.art/user001/
   → Use Chrome DevTools: navigate_page

2. Take a snapshot of the page
   → Use Chrome DevTools: take_snapshot

3. Check browser console for errors
   → Use Chrome DevTools: list_console_messages

4. Load the workflow:
   - Click the Load button in ComfyUI toolbar
   - Navigate to the workflow file
   - Click Load/Open
   → Use Chrome DevTools: click, take_snapshot

5. Verify nodes loaded on canvas:
   → Take snapshot, look for node elements
   → Check console for "missing node" errors

6. Click Queue Prompt (Run button):
   → Use Chrome DevTools: click

7. WAIT and OBSERVE:
   - Watch for status banner ("Sending to GPU...")
   - Check console for [QueueRedirect] messages
   - Wait for completion or error (up to 5 minutes for cold start)
   → Use Chrome DevTools: list_console_messages, take_snapshot

8. Check server-side:
   → SSH: docker logs comfy-queue-manager 2>&1 | grep -v "GET /health" | tail -20

9. Verify output:
   - Look for image/video preview in the UI
   - Check if output appeared in the correct node
   → Use Chrome DevTools: take_snapshot, take_screenshot
```

### Phase 3: DIAGNOSE — When a test fails

**Do NOT skip this phase. Do NOT rush to fix.**

```
1. COLLECT ALL EVIDENCE:
   - Browser console errors (full stack trace)
   - Network requests (failed fetches, 4xx/5xx responses)
   - QM logs (job received? sent to serverless? response?)
   - Container logs for the user (docker logs comfy-user001)
   - Current state of the page (snapshot + screenshot)

2. TRACE THE CODE PATH:
   - Read the relevant source file(s) — don't guess
   - Follow the data flow step by step
   - Identify exactly WHERE the failure occurs

3. IDENTIFY ROOT CAUSE:
   - Write down: "The bug is: [X] because [Y]"
   - Write down: "The fix should be: [Z]"
   - Consider: could this fix break something else?
   - Consider: is this a symptom or the actual root cause?

4. DOCUMENT in qa-state.json:
   {
     "current_workflow": 1,
     "bug_found": "description of bug",
     "root_cause": "analysis of why",
     "proposed_fix": "what I plan to change",
     "files_to_modify": ["list of files"]
   }
```

### Phase 4: FIX — Apply the fix via git flow

**One fix per commit. One test per fix.**

```
1. Make sure you're on the `mello-ralph-team` branch:
   git checkout mello-ralph-team || git checkout -b mello-ralph-team

2. Create a fix branch off it:
   git checkout -b fix/qa-[short-description]

3. Make the MINIMAL change needed
   - Read the file first (always!)
   - Change only what's necessary
   - If touching comfyume-extensions/, update extensions.conf if needed

3. Test locally if possible (syntax check, logic review)

4. Commit with clear message:
   git add [specific files]
   git commit -m "fix: [what] (#[issue])"

6. Deploy via git flow:
   git push origin fix/qa-[short-description]
   gh pr create --base mello-ralph-team --title "..." --body "..."
   gh pr merge --merge --delete-branch
   git checkout mello-ralph-team && git pull
   ./scripts/deploy.sh

6. Wait for containers to be healthy (check deploy output)
```

### Phase 5: VERIFY — Re-test the same workflow

Go back to Phase 2 and re-test the SAME workflow.
- If it passes: update qa-state.json, move to next workflow
- If it still fails: go back to Phase 3 with new evidence

### Phase 6: ADVANCE — Move to next workflow

When a workflow passes all criteria:
```
1. Update qa-state.json:
   - Mark current workflow as PASSED
   - Record what was tested and any fixes applied
   - Move to next workflow number

2. Check: are ALL 5 workflows passing?
   - If YES: output <promise>ALL_WORKFLOWS_PASSING</promise>
   - If NO: go to Phase 2 with the next workflow
```

---

## QA STATE FILE

Maintain state between iterations at `.claude/qa-state.json`:

```json
{
  "last_updated": "2026-02-11T18:00:00Z",
  "iteration": 1,
  "current_workflow": 1,
  "workflows": {
    "1_flux2_klein_9b": { "status": "untested" },
    "2_flux2_klein_4b": { "status": "untested" },
    "3_ltx2_video": { "status": "untested" },
    "4_ltx2_distilled": { "status": "untested" },
    "5_example": { "status": "untested" }
  },
  "bugs_found": [],
  "fixes_applied": [],
  "known_issues": [
    "Image delivery gap: serverless GPU generates images but they stay on remote container",
    "ComfyUI /prompt returns {prompt_id, number} — images come via WebSocket which we don't relay",
    "Status banner shows progress but output images don't appear in UI yet"
  ]
}
```

Workflow statuses: `untested` → `testing` → `blocked:[reason]` → `passed`

---

## KNOWN ARCHITECTURE

For reference when debugging:

```
User Browser
  → Queue Prompt click
  → redirect.js intercepts (comfyume-extensions/queue_redirect/)
  → POST /api/jobs (absolute URL → nginx → queue-manager:3000)
  → QM submit_to_serverless() → POST to Verda H200
  → Verda ComfyUI processes workflow
  → Response: {prompt_id, number, node_errors} (NO images!)
  → QM wraps in JobResponse, returns to browser
  → redirect.js shows status banner
  → BUT: images are on serverless container, not in UI
```

**Key files:**
- `comfyume-extensions/queue_redirect/web/redirect.js` — job submission + UI feedback
- `comfyume-extensions/default_workflow_loader/web/loader.js` — auto-load (DISABLED)
- `queue-manager/main.py` — job routing to serverless
- `queue-manager/config.py` — serverless endpoint config
- `comfyui-frontend/Dockerfile` — build with extensions
- `comfyui-frontend/docker-entrypoint.sh` — config-driven extension deployment
- `comfyume-extensions/extensions.conf` — enable/disable extensions

**Deploy:** `./scripts/deploy.sh` (NEVER SCP)

**Server:** root@65.108.33.101, project at /home/dev/comfyume-v1

---

## COMPLETION CRITERIA

Output `<promise>ALL_WORKFLOWS_PASSING</promise>` ONLY when ALL of these are true:
1. Flux2 Klein 9B loads correctly on canvas
2. Flux2 Klein 9B submits to serverless GPU via Queue Prompt
3. Flux2 Klein 9B shows progress in the UI (status banner minimum)
4. Flux2 Klein 9B displays output (image) in ComfyUI's native preview
5. No uncaught JS errors in browser console
6. All fixes are committed via git flow (no deployment drift)
7. qa-state.json shows Flux2 Klein 9B as "passed"

Criteria #4 (output display) requires solving the image delivery gap — this is an architectural fix, not a quick patch. You ARE expected to implement it. Do not mark it as "blocked" and move on. This is the core work.

---

## IF YOU'RE STUCK

After 10 iterations on the SAME bug without progress:
1. Document everything you've tried in qa-state.json
2. Create a GitHub issue with full diagnosis
3. Mark the workflow as `blocked:[issue-number]`
4. Move to the next workflow — don't spin forever on one problem
5. At iteration 40+, write a summary of all progress and blockers

**Remember:** getting 4 out of 5 workflows to criteria 1-3 is better than infinite-looping on one.
