**Project:** ComfyuME Multi-User ComfyUI Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume-v1
**Domain:** aiworkshop.art (production) / comfy.ahelme.net (staging)
**Doc Created:** 2026-02-11
**Doc Updated:** 2026-02-11

---
# Project Progress Tracker — MELLO RALPH TEAM (Autonomous QA)
**Target:** Workshop Feb 25 2026
**MAIN Repo:** comfyume-v1 (https://github.com/ahelme/comfyume-v1)
**Branch:** mello-ralph-team
**Phase:** FIX LOOP — autonomous workflow testing via Ralph Loop
---
## 0. Update Instructions

   RE: PRIORITY TASKS
   **UPDATE:**
     - WHEN NEW TASKS EMERGE
     - AT END OF SESSION - YOU MUST UPDATE/CULL TASKS

   **ALWAYS reference issues in our TWO Github Issue Trackers**
      - comfyume-v1: github.com/ahelme/comfyume-v1/issues/
      - private scripts: github.com/ahelme/comfymulti-scripts/issues/

   **FORMAT:**
          [status] [PRIORITY] [GH#s] [SHORT DESC.]
             - [DATE-CREATED] [DATE-UPDATED]
               - CONCISE NOTES
   **BE CONCISE**

   RE: Progress Reports (NEWEST AT TOP!)
     **CRITICAL DETAIL - NO FLUFF**
     **UPDATE OFTEN**
---
## 1. PRIORITY TASKS

🔴 **(CURRENT) - QA Loop: Test all 5 workflows end-to-end**
    - Created: 2026-02-11
    - See /comfyui-fix-loop skill for full protocol
    - State tracked in .claude/qa-state.json
    - Workflows to test:
      1. Flux2 Klein 9B (text → image)
      2. Flux2 Klein 4B (text → image)
      3. LTX-2 (text → video)
      4. LTX-2 Distilled (text → video)
      5. Example Workflow (basic)
    - KNOWN BLOCKER: Image delivery gap — images stay on serverless container
    - Success criteria: load, queue, progress feedback, output display, no JS errors

---

# Progress Reports

---

## Progress Report 1 - 2026-02-11 - Team created, fix loop ready

**Date:** 2026-02-11

### Team setup:
- Mello Ralph Team created with full skill structure (resume, handover, progress)
- fix loop skill created with 6-phase protocol (PR #17, #18)
- qa-state.json initialized with all 5 workflows as "untested"
- Ralph Loop recommended: `--max-iterations 50 --completion-promise "ALL_WORKFLOWS_PASSING"`

### Known state:
- 24 containers healthy on quiet-city (65.108.33.101)
- Serverless inference confirmed working (DataCrunch H200, HTTP 200 OK)
- Status banner deployed (redirect.js floating overlay)
- default_workflow_loader DISABLED (canvas null errors)
- Image delivery gap is the main unsolved problem

### Ready to start testing!

---

## Progress Report 2 - 2026-02-11 - Ralph Loop first run, credential fix

**Date:** 2026-02-11

### Changes:
- Ralph Loop plugin activated and tested — `/ralph-loop:ralph-loop` invocation confirmed working (PR #21)
- Switched QA test user from user011 → user001
- Removed hardcoded credentials from tracked skill files — now references `.env` line 367 at runtime
- qa-state.json updated: iteration 1, workflow 1 set to "testing"

### Observations:
- All 24 containers healthy on quiet-city
- QM running: serverless mode, H200-141GB-SPOT, Redis connected
- HTTP Basic Auth requires URL-encoded credentials for Chrome DevTools automation
- Ralph Loop `/help` confirms: stop hook intercepts exit, feeds same prompt back

### Next:
- Continue Ralph Loop iteration 1: test Flux2 Klein 9B workflow via Chrome DevTools
- Navigate to user001 with auth, load workflow, queue prompt, observe results

---
