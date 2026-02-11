**Project:** ComfyUI Multi-User Workshop Platform
**Repo:** github.com/ahelme/comfyume
**Team:** Verda Team
**Doc Created:** 2026-01-31
**Doc Updated:** 2026-01-31

---

# Implementation Plan - Verda Team Worker Rebuild

## Context

Rebuilding ComfyUI worker container for v0.11.0 in clean new repo (comfyume).
**NOT a migration** - copying proven components from comfy-multi and updating for v0.11.0.

**Parent Issues:**
- Master: comfyume #1 (MASTER: Rebuild ComfyUI v0.11.0)
- Context: comfy-multi #29 (Architecture Design)
- Coordination: comfyume #7 (Mello/Verda Team collaboration)

---

## Available Tools

**Discovered Skills:**
1. `issue:issue` - Analyze and fix GitHub issues (sequential, focused)
2. `feature-dev:feature-dev` - Analyze codebase and implement features
3. `tasks-phase:tasks-phase` - Multi-agent parallel orchestration
4. `superpowers:brainstorming` - Explore design decisions
5. `superpowers:writing-plans` - Document architecture

---

## Implementation Approach: Hybrid Strategy

### Phase 1: Foundation Components (Issues #4, #3, #2)
**Tool:** `/issue` skill (sequential, well-defined tasks)

**Sequence:**
1. **Issue #4**: VRAM monitoring script
   - No dependencies, start immediately
   - Creates `vram_monitor.py`
   - nvidia-smi wrapper with safety margin
   - Estimated: 1 hour

2. **Issue #3**: Integrate worker.py
   - Depends on #4 (VRAM hooks)
   - Copy from comfy-multi/comfyui-worker/worker.py
   - Add VRAM monitoring integration
   - API endpoints stable v0.9.2→v0.11.0 (minimal changes)
   - Estimated: 30 minutes

3. **Issue #2**: Build Dockerfile
   - Depends on #3 (includes worker.py)
   - Copy from comfy-multi/comfyui-worker/Dockerfile
   - Update base: FROM comfyanonymous/comfyui:v0.11.0
   - Keep working GPU setup (CUDA, nvidia-docker)
   - Add missing deps: curl, libgomp1, requests
   - Estimated: 1-2 hours

**Why `/issue` skill?**
- Well-defined requirements
- Clear acceptance criteria
- Sequential dependencies
- Good tracking per issue

---

### Phase 2: Integration (Issue #5)
**Tool:** `/feature-dev` skill OR `/issue` skill

**Task:** Configure timeouts (900s/1800s)
- Analyze timeout patterns from comfy-multi
- Update docker-compose.yml health checks
- Configure nginx proxy timeouts
- Update worker.py job timeouts
- Estimated: 30 minutes

**Why feature-dev?**
- Pattern analysis across multiple files
- Comprehensive timeout strategy
- Learns from existing implementation

**Alternative:** Continue with `/issue` skill if workflow is smooth

---

### Phase 3: Testing (Issue #6)
**Tool:** Manual with user

**Task:** Deploy and validate on Verda H100
- Requires actual GPU instance
- Test GPU detection (nvidia-smi)
- Test Redis queue connection (Tailscale VPN)
- Run end-to-end workflow
- Interactive troubleshooting
- Estimated: 1-2 hours

**Why manual?**
- Needs real hardware
- Interactive validation
- User controls Verda instance

---

## Critical Constraints

### 1. setup-verda-solo-script.sh Compatibility (MUST PRESERVE!)

**Project Structure:**
```
~/comfyume/                          # MUST match comfy-multi structure
├── comfyui-worker/                  # NOT comfyui-worker-v2!
│   ├── Dockerfile
│   ├── docker-compose.yml           # Contains worker-1 service
│   ├── worker.py
│   └── vram_monitor.py
├── data/
│   ├── models -> /mnt/sfs/models    # Symlink (script creates)
│   ├── outputs -> /mnt/scratch/outputs
│   └── inputs -> /mnt/scratch/inputs
└── .env
```

**Docker Commands (Unchanged):**
```bash
cd ~/comfyume/comfyui-worker/
sudo docker compose up -d worker-1
```

**Service Names (Unchanged):**
- Image: `comfyui-worker`
- Service: `worker-1`

**Setup Script Changes:**
- ONLY path updates: `/home/dev/comfy-multi` → `/home/dev/comfyume`
- Everything else identical

---

### 2. Backup & Copy Principle (NEVER Rewrite!)

**DO:**
✅ Copy existing working code from comfy-multi
✅ Make targeted updates for v0.11.0 compatibility
✅ Keep GPU configuration intact
✅ Preserve Redis patterns
✅ Test incrementally

**DON'T:**
❌ Write code from scratch
❌ "Improve" working components
❌ Change architecture unnecessarily
❌ Skip copying proven solutions

**Why?**
- 75% of code works as-is
- GPU setup is fragile (weeks to perfect)
- Redis/Tailscale patterns proven
- Only 25% needs v0.11.0 updates

---

### 3. Worker API Stability (Key Discovery!)

**STABLE Endpoints (v0.9.2 → v0.11.0):**
- `/prompt` - Submit workflow
- `/queue` - Queue status
- `/ws` - WebSocket updates
- `/history` - Job history
- `/api/userdata` - User files

**Impact:**
- worker.py needs MINIMAL changes
- Only add VRAM monitoring hooks
- No API translation layer needed for worker
- Significantly reduces implementation scope

---

### 4. Division of Labor

**Verda Team (us):**
- Worker container (Issues #2-6)
- VRAM monitoring
- GPU configuration
- Queue connection testing

**Mello Team:**
- Frontend containers
- Services (queue-manager, admin, nginx)
- Workflow storage paths
- JavaScript extensions

**Both Teams:**
- Integration testing (Phase 3)
- End-to-end validation

**Don't Cross Streams!**
- Stick to our scope
- Coordinate via Issue #7
- No frontend work until integration phase

---

## Success Criteria

**Issue #4 (VRAM Monitoring):**
- [ ] Script exists: `comfyui-worker/vram_monitor.py`
- [ ] Calls nvidia-smi successfully
- [ ] Returns available VRAM with safety margin
- [ ] Handles errors gracefully
- [ ] Documented and tested

**Issue #3 (worker.py):**
- [ ] Copied from comfy-multi
- [ ] VRAM monitoring integrated
- [ ] API calls unchanged (stable endpoints)
- [ ] Redis connection preserved
- [ ] Commented and documented

**Issue #2 (Dockerfile):**
- [ ] Base image: comfyanonymous/comfyui:v0.11.0
- [ ] GPU setup preserved (CUDA, nvidia-docker)
- [ ] Dependencies added: curl, libgomp1, requests
- [ ] worker.py and vram_monitor.py included
- [ ] Health check functional
- [ ] Builds successfully

**Issue #5 (Timeouts):**
- [ ] docker-compose.yml health checks: 900s/1800s
- [ ] nginx proxy timeouts configured
- [ ] worker.py job timeouts set
- [ ] Consistent across all components

**Issue #6 (Testing):**
- [ ] Deploys on Verda H100
- [ ] GPU detected (nvidia-smi)
- [ ] Redis connection works (Tailscale)
- [ ] Test workflow completes
- [ ] No errors in logs

---

## Immediate Next Step

### Start with Issue #4: VRAM Monitoring Script

**Why this first?**
1. **No blockers** - Can start immediately
2. **Small scope** - Clear, focused task (1 hour)
3. **Foundation** - Needed by worker.py
4. **Learning** - Tests our workflow
5. **Quick win** - Builds momentum

**Two Options:**

**Option A: Use `/issue` skill (RECOMMENDED)**
```bash
/issue https://github.com/ahelme/comfyume/issues/4
```

**Option B: Manual implementation**
```bash
1. Read comfy-multi worker (check for existing VRAM code)
2. Create ~/comfyume/comfyui-worker/vram_monitor.py
3. Implement nvidia-smi wrapper
4. Test on Verda CPU instance
5. Document in Issue #4
6. Commit to comfyume verda-track branch
```

---

## Git Workflow

**Branches:**
- `verda-track` in comfyume repo (our work)
- `mello-track` in comfyume repo (Mello Team)
- Both merge to `main` after Phase 3 testing

**Commits:**
```bash
# After each issue completion
cd ~/comfyume
git add -A
git commit -m "feat: implement VRAM monitoring script (Issue #4)"
git push origin verda-track
```

**PR Strategy:**
- Create PR after Issue #2 (Dockerfile complete)
- OR after full Phase 2 (all worker components)
- Review with Aeon before merging

---

## Coordination Protocol

**Check Issue #7 Regularly:**
- Mello Team posts updates there
- We post our progress
- Ask questions, share blockers
- Like email - check before starting work

**Update Progress File:**
- `progress-verda-dev.md` in comfy-multi repo
- Document decisions, discoveries, commits
- Update after each issue completion

**Handover Documentation:**
- Update CLAUDE-RESUME before context limit
- Keep CLAUDE.md HANDOVER section current
- Commit frequently, push often

---

## Timeline Estimate

**Phase 1: Foundation (Issues #4, #3, #2)**
- VRAM monitoring: 1 hour
- worker.py integration: 30 min
- Dockerfile: 1-2 hours
- **Total: 2.5-3.5 hours**

**Phase 2: Integration (Issue #5)**
- Timeout configuration: 30 min
- **Total: 30 minutes**

**Phase 3: Testing (Issue #6)**
- Deploy and validate: 1-2 hours
- **Total: 1-2 hours**

**Grand Total: 4-6 hours**

Aligns with original estimate of 2-3 hours per component (slightly conservative).

---

## Risk Mitigation

**Risk: GPU setup breaks during rebuild**
- Mitigation: Copy Dockerfile exactly, minimal changes
- Fallback: Restore from comfy-multi and debug differences

**Risk: worker.py API changes missed**
- Mitigation: API endpoints confirmed stable by Mello analysis
- Fallback: Test thoroughly with queue-manager mock

**Risk: Setup script incompatibility**
- Mitigation: Match directory structure exactly
- Validation: Test script changes in Issue #6

**Risk: Scope creep**
- Mitigation: Stick to issue requirements, no extras
- Division of labor: No frontend work

---

## References

**Documentation:**
- comfyume Issue #1 (Master task breakdown)
- comfy-multi #29 (Architecture context)
- comfyume Issue #7 (Team coordination)
- progress-verda-dev.md (Session history)

**Source Code:**
- comfy-multi/comfyui-worker/ (copy from here)
- setup-verda-solo-script.sh (compatibility requirements)
- docs/architecture-information-flow-map.md (system overview)

**Analysis:**
- docs/critique-holistic-v0.8.2-to-v0.11.1.md (Mello Team research)
- Worker API stability findings (endpoints unchanged)

---

**Ready to start!** 🚀

**Next command:**
```bash
/issue https://github.com/ahelme/comfyume/issues/4
```
