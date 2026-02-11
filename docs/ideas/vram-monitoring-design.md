# VRAM Monitoring Design - Initial Thoughts

**Created:** 2026-01-31
**Issue:** comfyume #4
**Author:** Claude (Verda Team)

---

## User Context

**Who:** Workshop instructor (Sarah) managing 20 filmmakers
**Situation:** Live workshop with expensive GPU time ($4/hr H100)
**Juggling:**
- Teaching content delivery
- Budget management
- Supporting 20 participants with varying tech skills
- Maintaining system stability

**Pain Point:** ComfyUI v0.11.0 uses more memory. A participant starts a huge LTX-2 19B video job, GPU runs out of memory, system crashes. Workshop stops, 19 people wait, instructor is embarrassed, GPU time wasted.

**Need:** System gracefully rejects jobs that would OOM, rather than crashing.

---

## What Already Exists

### 1. Worker.py Pattern (comfy-multi)
- Clean separation: worker polls queue → processes job → reports back
- Good error handling with try/catch
- Structured logging
- Graceful shutdown
- **NO VRAM checking currently**

### 2. Queue Manager Data Models
Already has fields for GPU memory:
```python
class WorkerStatus(BaseModel):
    gpu_memory_used: Optional[int] = None  # MB
    gpu_memory_total: Optional[int] = None  # MB
```

**Implication:** Queue manager EXPECTS workers to report VRAM!
**Opportunity:** We should populate these fields as part of integration.

### 3. Test Infrastructure
Tests already mock gpu_memory values:
```python
"gpu_memory_used": 8192
gpu_memory_total=81920
```

**Implication:** This is a planned feature, partially implemented.

### 4. Deployment Scripts
Already use nvidia-smi for GPU detection:
```bash
scripts/setup.sh: nvidia-smi --query-gpu=name --format=csv
scripts/test.sh: nvidia-smi --query-gpu=count --format=csv
```

**Pattern to follow:** These scripts show the nvidia-smi query pattern.

---

## Design Principles from Codebase Analysis

### 1. **Fail-Safe Philosophy**
From worker.py error handling:
- Try operation → log error → mark job failed → continue
- Never crash the worker
- Always report status back to queue

**Apply to VRAM:** If VRAM check fails, should we fail-open (accept job) or fail-closed (reject job)?

**Decision:** Fail-open (like the issue suggests)
- Workshop scenario: Better to try than block
- If monitoring breaks, don't halt all work
- Let ComfyUI handle its own OOM if monitoring unavailable

### 2. **Simple, Testable Components**
Worker.py is ~300 lines, single responsibility
ComfyUIClient is separate class
Each function does one thing

**Apply to VRAM:**
- Separate module (vram_monitor.py)
- Pure functions (no global state)
- Easy to mock for testing

### 3. **Environment-Driven Config**
Worker uses env vars for all config:
```python
COMFYUI_TIMEOUT = int(os.getenv("COMFYUI_TIMEOUT", "300"))
```

**Apply to VRAM:**
- Safety margin configurable via env
- Enable/disable monitoring via env
- VRAM estimates configurable

### 4. **Logging > Silent Failures**
Every operation logged with context
Errors include job_id, user_id for debugging

**Apply to VRAM:**
- Log every VRAM decision
- Include available, required, job context
- Make it easy to debug "why was my job rejected?"

---

## Initial Design: Simple nvidia-smi Wrapper

### Core Functions

```python
def get_available_vram() -> Optional[int]:
    """Query nvidia-smi, return MB free or None if fails"""

def check_vram_sufficient(required_mb: int, safety_margin_mb: int = 2048) -> bool:
    """Check if enough VRAM for job (fail-open on error)"""

def get_vram_stats() -> Optional[Dict]:
    """Detailed stats for health endpoint and monitoring"""
```

### Integration Points

**1. Worker.process_job() - Before Queueing**
```python
# Current: Just queue immediately
prompt_id = self.comfyui.queue_prompt(workflow)

# Proposed: Check first
if not check_vram_sufficient(job.get('estimated_vram', 8192)):
    self.fail_job(job_id, "Insufficient VRAM")
    return False

prompt_id = self.comfyui.queue_prompt(workflow)
```

**2. Worker Heartbeat - Report Status**
```python
# Add VRAM stats to worker status messages
stats = get_vram_stats()
report_to_queue_manager({
    'worker_id': self.worker_id,
    'gpu_memory_used': stats['used_mb'],
    'gpu_memory_total': stats['total_mb']
})
```

**3. Optional Health Endpoint**
```python
# For debugging and monitoring
GET /health/vram
→ {"total_mb": 81920, "used_mb": 24000, "free_mb": 57920, "usage_percent": 29.3}
```

---

## Questions & Considerations

### Q1: Where do VRAM estimates come from?

**Issue suggests:**
```python
VRAM_ESTIMATES = {
    'flux2-klein-9b': 18432,
    'flux2-klein-4b': 8192,
    'ltx2-19b': 24576,
    'default': 8192
}
```

**Problem:** How does job know which model it's using?

**Options:**

**A) Frontend sets estimate in job metadata**
```python
# User selects "LTX-2 19B" workflow
submit_job({
    'workflow': {...},
    'metadata': {
        'model_type': 'ltx2-19b',
        'estimated_vram': 24576
    }
})
```
✅ Accurate per workflow
❌ Requires frontend changes (Mello Team territory!)

**B) Worker analyzes workflow JSON**
```python
def estimate_vram_from_workflow(workflow: Dict) -> int:
    # Parse workflow, look for checkpoint nodes
    for node in workflow.values():
        if node['class_type'] == 'CheckpointLoaderSimple':
            checkpoint = node['inputs']['ckpt_name']
            if 'ltx-2-19b' in checkpoint:
                return 24576
    return 8192  # Default
```
✅ No frontend changes needed
❌ Fragile (depends on workflow structure)
❌ Mixes concerns (worker shouldn't parse workflows)

**C) Start with default, add estimates later**
```python
# Phase 1: Just use default safety margin
required = job.get('metadata', {}).get('estimated_vram', 8192)

# Phase 2: Frontend adds estimates (coordination with Mello)
# Phase 3: Maybe add workflow analysis as fallback
```
✅ Simple to start
✅ Allows iteration
✅ Doesn't block current work

**Recommendation:** Option C - Start simple, iterate.

### Q2: What safety margin is appropriate?

**Issue suggests:** 2GB (2048 MB)

**Analysis:**
- H100 has 80GB total
- LTX-2 19B uses ~24GB
- 2GB margin = 8% buffer
- Leaves room for:
  - System overhead
  - CUDA kernels
  - Temporary tensors during execution

**Seems reasonable!** But make it configurable:
```python
VRAM_SAFETY_MARGIN = int(os.getenv("VRAM_SAFETY_MARGIN_MB", "2048"))
```

### Q3: Should monitoring be optional?

**Scenarios where it might fail:**
- No GPU (testing on CPU)
- nvidia-smi not in PATH
- Permission issues
- nvidia-smi hangs (rare but possible)

**Approach:**
```python
ENABLE_VRAM_MONITORING = os.getenv("ENABLE_VRAM_MONITORING", "true").lower() == "true"

if ENABLE_VRAM_MONITORING:
    if not check_vram_sufficient(...):
        reject_job()
else:
    # Skip VRAM check
    proceed_with_job()
```

✅ Allows disabling for testing
✅ Allows disabling if nvidia-smi broken
✅ Default enabled (safe for production)

---

## Alignment Check

### Does this align with existing patterns?

✅ **Separate module** - Like ComfyUIClient class
✅ **Environment config** - Like COMFYUI_TIMEOUT
✅ **Fail-safe** - Like error handling in worker.py
✅ **Logging** - Follows logger.info/warning/error pattern
✅ **Pure functions** - Stateless, testable
✅ **No modification of ComfyUI** - Stays in worker layer

### Any gotchas or blindspots?

**1. Multi-GPU systems**
Current design assumes single GPU (uses first GPU)
```bash
nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits
# Returns first GPU only
```

**Fix for later:**
```bash
nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits --id=0
```

**2. Race conditions**
VRAM check → time passes → job starts → VRAM might be used by other process

**Mitigation:**
- Safety margin helps
- Check is best-effort, not guarantee
- Real protection is ComfyUI's own error handling

**3. Concurrent jobs**
Worker processes one job at a time currently
Future: Multiple workers might compete for same GPU

**Solution:**
- Document assumption: one worker per GPU
- If multi-worker needed, add locking or coordinator

### Am I rewriting anything that exists?

❌ No VRAM monitoring currently exists
✅ WorkerStatus model already has fields (we're filling them in)
✅ nvidia-smi already used in scripts (we're reusing pattern)

### Best practices?

✅ **Type hints** - Use Optional[int], Dict[str, Any]
✅ **Docstrings** - Every function
✅ **Error handling** - Try/except with logging
✅ **Configuration** - Environment variables
✅ **Testing** - Mock subprocess, test logic

### Simpler way?

**Could we just set ComfyUI memory limits?**
```python
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

❌ Doesn't prevent jobs from being queued
❌ Jobs would still fail, just differently
✅ VRAM monitoring is better UX (reject upfront vs fail mid-execution)

**Current design is simplest that solves problem.**

---

## Alternative Approaches

Let me sketch 3 alternatives...

### Alternative A: GPU Manager Service

**Idea:** Separate service tracks GPU state, workers query it

```
┌──────────────┐
│ GPU Manager  │ ← Tracks VRAM, job allocations
└──────────────┘
       ↑
       │ Query before job
┌──────────────┐
│  Worker 1-3  │
└──────────────┘
```

**Pros:**
- Centralized VRAM tracking
- Handles multi-GPU, multi-worker
- Could do sophisticated scheduling

**Cons:**
- Over-engineered for current need (1 worker)
- New service to maintain
- More moving parts = more failure modes
- Coordination overhead

**Verdict:** Overkill for workshop scenario

### Alternative B: ComfyUI Plugin

**Idea:** Custom node that checks VRAM before execution

```python
class VRAMCheckNode:
    def execute(self, estimated_vram):
        if not sufficient_vram(estimated_vram):
            raise Exception("Insufficient VRAM")
        return ()
```

**Pros:**
- Inside ComfyUI (native integration)
- Could be per-workflow configurable

**Cons:**
- Modifies ComfyUI (violates "upstream dependency" principle!)
- Requires workflow changes
- Still needs nvidia-smi wrapper
- Mixes concerns (GPU management in workflow layer)

**Verdict:** Violates architectural principles

### Alternative C: Queue Manager Pre-Screening

**Idea:** Queue manager checks worker VRAM before assigning job

```python
# Queue manager
def assign_job_to_worker():
    workers = get_available_workers()
    for worker in workers:
        if worker.gpu_memory_free > job.estimated_vram:
            assign(job, worker)
```

**Pros:**
- Centralized job assignment
- Could optimize across workers
- Clean separation

**Cons:**
- Queue manager doesn't have direct GPU access
- Still needs workers to report VRAM
- Stale data problem (VRAM changes between reports)
- Adds latency to job assignment

**Verdict:** Good for multi-worker, but still needs worker-side monitoring!

---

## Hybrid Approach (Best of All Worlds)

After thinking through alternatives, I see a **staged approach:**

**Phase 1 (Now - Issue #4):**
Worker-side VRAM check before queueing to ComfyUI
- Simple, local decision
- No network calls
- Immediate feedback

**Phase 2 (Later - Integration):**
Worker reports VRAM in heartbeat to queue manager
- Populates WorkerStatus.gpu_memory_used
- Admin dashboard shows GPU status
- Monitoring/alerting possible

**Phase 3 (Future - Multi-worker):**
Queue manager uses VRAM stats for job assignment
- Picks worker with most free VRAM
- Load balancing across GPUs
- Optimal resource utilization

**This gives:**
✅ Immediate protection (Phase 1)
✅ Observability (Phase 2)
✅ Future scalability (Phase 3)
✅ Each phase has clear value
✅ No big-bang rewrite

---

## Maintainer Perspective

**Me as future maintainer:**

**Pet Peeves to Avoid:**
- ❌ Magic numbers (2048 MB hardcoded)
- ❌ Silent failures (if nvidia-smi breaks)
- ❌ No logging (why was job rejected?)
- ❌ Complex dependencies (just subprocess!)
- ❌ Platform assumptions (only Linux)

**Make Life Easier:**
- ✅ Environment config for tuning
- ✅ Verbose logging for debugging
- ✅ Simple fallback (fail-open)
- ✅ Clear error messages
- ✅ Easy to test (mock subprocess)
- ✅ Documented assumptions

**Specific considerations:**

1. **When nvidia-smi is slow:**
   Add timeout to subprocess.run()
   ```python
   result = subprocess.run(..., timeout=5)
   ```

2. **When logs fill up:**
   Use appropriate log levels
   ```python
   logger.debug("VRAM check...")  # Normal operation
   logger.warning("Insufficient VRAM")  # Actionable
   logger.error("nvidia-smi failed")  # Problem
   ```

3. **When estimates are wrong:**
   Make it obvious in logs
   ```python
   logger.info(f"Job estimated {est}MB, actual used {used}MB")
   ```

---

## User Experience Flow

**Scenario: Filmmaker submits large job**

1. User clicks "Generate Video" with LTX-2 19B workflow
2. Frontend submits job to queue-manager
3. Worker picks up job
4. **NEW:** Worker checks VRAM (15GB available, needs 24GB + 2GB)
5. **NEW:** Worker rejects job: "Insufficient GPU memory"
6. Job marked as FAILED with clear error
7. User sees: "Not enough GPU memory. Try shorter video or smaller model."

**User sees:** Clear feedback, knows what went wrong, can adjust

**Alternative (no monitoring):**
1-3. Same
4. Worker queues job to ComfyUI
5. ComfyUI starts processing
6. ComfyUI crashes with OOM
7. Worker detects crash, marks failed
8. User sees: "System error" (cryptic!)

**VRAM monitoring flow is better UX!**

---

## Product Designer Perspective

**Is this solution the best it can be?**

**Good:**
✅ Prevents system crashes (stability)
✅ Clear error messages (usability)
✅ Configurable safety (flexibility)
✅ No UI changes needed (fast to ship)

**Potential improvements:**

1. **Estimated wait time**
   "Not enough memory. GPU busy. Try again in 5 minutes."
   → Gives user actionable guidance
   → Requires queue depth analysis (future work)

2. **Suggest alternatives**
   "LTX-2 19B needs 24GB. Try LTX-2 Distilled (12GB) instead?"
   → Requires workflow analysis
   → Better handled in frontend (Mello Team)

3. **Auto-retry when VRAM frees up**
   Job waits in queue for VRAM instead of failing
   → More complex state management
   → Nice-to-have, not MVP

**For MVP:** Current design is solid. Improvements can wait.

**Corners cut?**
- No multi-GPU support (don't need it yet)
- No workflow analysis (frontend can provide estimates)
- No fancy scheduling (FIFO is fine)

**These aren't "cut corners", they're smart scope management!**

---

## Senior Developer Review (20 years experience)

**What stands out:**

**Good:**
- Simple solution to real problem ✅
- Leverages existing tools (nvidia-smi) ✅
- Aligns with codebase patterns ✅
- Fail-safe defaults ✅
- Room to grow ✅

**Could be better:**

1. **Testing strategy needs thought**
   - How to test on CPU machine?
   - How to mock nvidia-smi?
   - How to test edge cases (nvidia-smi hangs)?

   **Plan:**
   - Mock subprocess.run in tests
   - Test with canned nvidia-smi outputs
   - Test timeout behavior

2. **Error messages could be more actionable**
   ```python
   # Weak
   "Insufficient VRAM"

   # Better
   "Insufficient GPU memory: need 26GB (24GB + 2GB safety), only 15GB available"
   ```

3. **Consider adding a dry-run mode**
   ```python
   VRAM_CHECK_DRY_RUN = os.getenv("VRAM_CHECK_DRY_RUN", "false") == "true"

   if dry_run:
       logger.warning(f"DRY RUN: Would reject job (need {req}MB, have {avail}MB)")
       return True  # Allow anyway
   ```

   **Why:** Test in production without blocking real work

**Overall:** Solid design. Ship it!

---

## Final Decision

After all this analysis, here's the plan:

### What We're Building

**vram_monitor.py** with three functions:

1. `get_available_vram()` → Optional[int]
   - Query nvidia-smi
   - Return free VRAM in MB
   - Return None on error (fail-safe)
   - 5 second timeout

2. `check_vram_sufficient(required_mb, safety_margin_mb)` → bool
   - Check if enough VRAM
   - Log decision with context
   - Fail-open on nvidia-smi error
   - Configurable safety margin

3. `get_vram_stats()` → Optional[Dict]
   - Total, used, free, percent
   - For health endpoints
   - For worker status reporting

### Integration with Worker

**worker.py changes (Issue #3 will handle this):**
```python
from vram_monitor import check_vram_sufficient

def process_job(self, job):
    # Check VRAM before queueing
    estimated_vram = job.get('metadata', {}).get('estimated_vram', 8192)
    if not check_vram_sufficient(estimated_vram):
        self.fail_job(job_id, "Insufficient GPU memory")
        return False

    # Proceed with job...
```

### Configuration

**Environment variables:**
```bash
ENABLE_VRAM_MONITORING=true          # Enable/disable
VRAM_SAFETY_MARGIN_MB=2048           # Default 2GB
VRAM_CHECK_TIMEOUT_SECONDS=5         # nvidia-smi timeout
VRAM_DEFAULT_ESTIMATE_MB=8192        # Fallback if not specified
```

### Testing

```python
def test_vram_check_sufficient():
    # Mock subprocess with plenty of VRAM
    assert check_vram_sufficient(8192) == True

def test_vram_check_insufficient():
    # Mock subprocess with low VRAM
    assert check_vram_sufficient(80000) == False

def test_vram_check_fails_open():
    # Mock subprocess.run raising exception
    assert check_vram_sufficient(8192) == True  # Fail-open!
```

---

## Why This Solution?

**Compared to alternatives:**
- Simpler than GPU Manager Service
- Respects "upstream dependency" principle (vs ComfyUI plugin)
- Provides immediate protection (vs queue manager only)
- Allows future enhancement (hybrid approach)

**Fits the context:**
- Workshop scenario (single worker, known models)
- Budget conscious (prevent wasted GPU crashes)
- User experience (clear error messages)

**Maintainable:**
- Small, focused module
- Well-tested
- Configurable
- Clear logging

**Follows best practices:**
- Type hints
- Docstrings
- Error handling
- Environment config
- Fail-safe defaults

**This is the right solution!** 🎯

---

## Next Steps

1. ✅ Design complete (this doc)
2. → Implement vram_monitor.py
3. → Write tests
4. → Update worker.py integration (Issue #3)
5. → Test on Verda GPU instance
6. → Document in issue

Let's build it! 🚀
