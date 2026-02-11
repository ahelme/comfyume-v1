# Issue #39: Infrastructure Load Test - Design Thinking

**Date:** 2026-02-01
**Issue:** https://github.com/ahelme/comfyume/issues/39
**Context:** Independent infrastructure testing without GPU workers

---

## Problem Analysis

We need to validate the 20-user infrastructure can:
1. Start all containers successfully (batched)
2. Accept job submissions from all users
3. Maintain proper isolation
4. Stay within resource limits
5. Handle the queue correctly (even if jobs don't process)

## User Empathy Notes

**User:** Aeon, workshop instructor
**Context:** 2 weeks before workshop, validating infrastructure
**Pain Points:**
- Needs confidence system works BEFORE spending money on GPU workers
- Limited DevOps experience - needs clear feedback
- Time pressure - can't debug obscure failures
- High stakes - paying professional filmmakers will be using this

**Quality of Life Needs:**
- Clear, actionable error messages
- Visual confirmation of success at each step
- Automated validation (not manual checking)
- Easy cleanup if things go wrong
- Documentation that matches reality

## Current State Assessment

**What Exists:**
- ✅ `init-user-data.sh` - Creates user directories
- ✅ `generate-user-compose.sh` - Generates container config
- ✅ `load-test.sh` - Submits jobs
- ✅ `monitor-queue.sh` - Real-time monitoring
- ✅ `validate-load-test.sh` - Automated validation
- ✅ `docs/testing-guide.md` - Documentation

**What's Missing:**
1. **Per-user output/input directories** - Not created by init script
2. **Orchestration script** - No single "run the test" command
3. **Clear test reporting** - Validation script doesn't generate summary report
4. **Cleanup automation** - No "reset" script
5. **Pre-flight checks** - No validation that prerequisites are met

## Design Approach #1: Minimal Fix

**Just fix the obvious issues:**
- Add output/input directory creation to `init-user-data.sh`
- Run the test manually following the documented steps
- Document any issues found

**Pros:**
- Quick
- Low risk
- Follows existing patterns

**Cons:**
- Doesn't improve user experience
- Still requires manual coordination
- No clear "did it work?" answer

## Design Approach #2: Comprehensive Test Orchestrator

**Create a master test script that:**
1. Validates prerequisites
2. Starts containers in correct order
3. Waits for health checks
4. Runs load test
5. Validates results
6. Generates report
7. Offers cleanup

**Structure:**
```bash
scripts/run-infrastructure-test.sh
  ├─ Pre-flight checks
  ├─ Start infrastructure
  ├─ Wait for healthy
  ├─ Run load test
  ├─ Validate results
  ├─ Generate report
  └─ Cleanup option
```

**Pros:**
- Single command to run
- Clear pass/fail result
- Professional report
- Less room for user error
- Easier to reproduce issues

**Cons:**
- More code to maintain
- Might hide useful details
- Could be inflexible

## Design Approach #3: Guided Interactive Test

**Create an interactive script that:**
- Walks user through each step
- Waits for user confirmation
- Shows what's happening
- Asks if user wants to continue
- Explains what each step validates

**Pros:**
- Educational
- User stays in control
- Easy to debug
- Builds confidence

**Cons:**
- Slower
- Requires user attention
- Not fully automated
- Hard to run in CI later

## Synthesis: Best of All Worlds

**Hybrid Approach:**

1. **Fix the foundation** (Approach #1)
   - Update `init-user-data.sh` to create ALL required directories
   - Ensure scripts work as documented

2. **Add orchestration** (Approach #2)
   - Create `scripts/test-infrastructure.sh` master script
   - Generates detailed report file
   - Returns clear exit code

3. **Keep flexibility** (Approach #3)
   - Support both automated and manual modes
   - Verbose output option
   - Step-by-step mode for debugging

**Key Features:**
- ✅ Pre-flight validation (Docker running, images exist, etc.)
- ✅ Automated test execution
- ✅ Real-time progress updates
- ✅ Comprehensive report generation
- ✅ Clean exit codes for scripting
- ✅ Optional cleanup
- ✅ Preserves existing scripts (composable)

## Maintainer Perspective

**What would annoy me in 6 months:**
- Scripts that don't clean up after themselves
- Hard-coded values that should be configurable
- No way to run just one piece
- Report files scattered everywhere
- No timestamps on test runs
- Can't tell what version was tested

**Solutions:**
- Timestamped report files in `test-reports/`
- All scripts idempotent
- Each script works standalone AND as part of orchestration
- Clear naming: `test-infrastructure.sh` (orchestrator) vs `load-test.sh` (component)
- Version info in reports

## User Flow Perspective

**Ideal flow:**
```bash
$ ./scripts/test-infrastructure.sh
════════════════════════════════════════════════════════════════
  ComfyUme Infrastructure Test (Issue #39)
  2026-02-01 17:00:00
════════════════════════════════════════════════════════════════

[✓] Pre-flight checks passed
[✓] Docker is running
[✓] Images available: comfyume-frontend:v0.11.0
[✓] User directories initialized (20 users)

Starting infrastructure test...

[1/6] Starting Redis and Queue Manager...
  └─ Waiting for health checks... ✓ (12s)

[2/6] Starting 20 user containers (batched)...
  └─ Batch 1 (user001-005)... ✓ (45s)
  └─ Batch 2 (user006-010)... ✓ (38s)
  └─ Batch 3 (user011-015)... ✓ (41s)
  └─ Batch 4 (user016-020)... ✓ (39s)
  └─ Total: 20/20 containers healthy (2m43s)

[3/6] Submitting test jobs (100 jobs = 5 per user)...
  └─ Submitted: 100/100 ✓ (3s)

[4/6] Validating queue management...
  └─ Queue depth: 100 ✓
  └─ All jobs pending (expected - no workers) ✓

[5/6] Validating user isolation...
  └─ User directories: 20/20 ✓
  └─ Output directories: 20/20 ✓
  └─ Custom nodes: 20/20 ✓

[6/6] Validating resource limits...
  └─ Memory usage: avg 1.2G, max 1.8G (limit: 2G) ✓
  └─ No container crashes ✓

════════════════════════════════════════════════════════════════
  TEST PASSED ✓
════════════════════════════════════════════════════════════════

Report: test-reports/infrastructure-test-2026-02-01-170000.txt

Cleanup queue (100 pending jobs)? [y/N]
```

**What feels obtuse:**
- Having to check multiple terminal windows
- No persistence of results (lost on terminal close)
- Unclear what "healthy" means
- No indication of progress during long waits

**Quality of life improvements:**
- Progress bars for long operations
- Estimated time remaining
- Saved report file
- Optional cleanup prompt
- Clear next steps in output

## Product Design Perspective

**Is this the best it can be?**

Current plan is good but could add:
- JSON report option (for CI/tooling)
- Quiet mode (just exit code + report file)
- Watch mode (continuous validation)
- Comparison against baseline

**Are corners being cut?**

Need to ensure:
- Error messages are actionable
- Reports include version information
- Cleanup is thorough
- Resource monitoring is accurate

## Senior Developer Perspective

**Observations:**
- Good: Using existing scripts (composition over duplication)
- Watch out: Avoid tight coupling between orchestrator and components
- Consider: Exit codes - use standard conventions (0=success, 1=failure, 2=partial)
- Think about: Parallel execution where safe (health checks can be polled concurrently)
- Security: None of these scripts should require sudo
- Performance: Avoid polling loops that hammer the API

**Recommendations:**
- Use `set -euo pipefail` in all scripts
- Validate all user inputs
- Don't assume file paths
- Handle interruption gracefully (trap EXIT)
- Log to file AND stdout

## Final Decision: Hybrid Orchestrator

**What we'll build:**

1. **Fix foundation first:**
   - Update `init-user-data.sh` to create inputs/outputs per user
   - Test each existing script works standalone

2. **Create orchestrator:**
   - `scripts/test-infrastructure.sh` - master test script
   - Validates prerequisites
   - Runs test sequence
   - Generates report
   - Offers cleanup

3. **Enhance reporting:**
   - Update `validate-load-test.sh` to output more detail
   - Create `test-reports/` directory structure
   - Include timestamps, versions, metrics

4. **Documentation:**
   - Update `docs/testing-guide.md` with new workflow
   - Add troubleshooting section with common issues
   - Include example reports

**Why this solution:**
- Respects user's time (one command vs many)
- Builds confidence (clear pass/fail)
- Aids debugging (detailed reports)
- Maintains flexibility (components still work standalone)
- Professional output (suitable for documentation/records)
- Follows existing patterns (bash scripts, Docker compose)
- Minimal new dependencies (standard Unix tools)

## Implementation Checklist

- [ ] Update `init-user-data.sh` - add inputs/outputs directories
- [ ] Create `test-reports/.gitkeep`
- [ ] Create `scripts/test-infrastructure.sh` - main orchestrator
- [ ] Enhance `validate-load-test.sh` - better reporting
- [ ] Test on clean system
- [ ] Update `docs/testing-guide.md`
- [ ] Run full test suite
- [ ] Generate example report
- [ ] Create PR
- [ ] Get review feedback

---

**Next Step:** Create detailed implementation plan
