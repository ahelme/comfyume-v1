# ComfyuME Container Orchestration & Command Scenarios

**Created:** 2026-02-01
**Session:** 23
**Status:** Research Complete - Implementation Pending

---

## 🎯 Key Findings

### Architecture Pattern Discovery

**comfy-multi AND comfyume BOTH support dual deployment modes:**

1. **Single-Server Mode** - All services on one machine (frontends + worker)
2. **Dual-Server Mode** - Split architecture (frontends on VPS + worker on GPU cloud)

### Critical Components Location

| Component | Repository | Branch | Owner |
|-----------|------------|--------|-------|
| **Frontend v0.11.0** | comfyume | mello-track | Mello Team ✅ |
| **Worker v0.11.0** | comfyume | verda-track | Verda Team ✅ |
| **Queue Manager** | comfyume | mello-track | Copied (stable) ✅ |
| **Admin Dashboard** | comfyume | mello-track | Copied (stable) ✅ |

**CRITICAL:** Verda team has created worker container on `verda-track` branch!

---

## 🚨 Current Problem: Confusing `--cpu` Flag

### What `--cpu` Flag ACTUALLY Does

```python
# In ComfyUI's model_management.py
if args.cpu:
    device = torch.device('cpu')  # No GPU access
else:
    device = torch.device('cuda')  # GPU-enabled
```

**Behavioral Impact:**
- ✅ Prevents CUDA initialization
- ✅ Allows UI to run without GPU
- ❌ Very slow for inference (CPU-only generation)
- ⚠️ Name is MISLEADING! (Issue #25 in comfy-multi)

### Current Usage (Misleading Names)

```dockerfile
# Frontend Dockerfile (Line 62)
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--cpu"]
# Comment says: "CPU mode" but really means "no inference capability"
```

---

## 💡 Proposed Flag System (Clear & Descriptive)

### New Flag Architecture

| Flag | Where Used | Actual Meaning | Use Case |
|------|-----------|----------------|----------|
| `--frontend-testing` | Mello (no GPU) | UI only, no inference | Testing workflows locally |
| `--dual-server` | Mello (default) | UI only, expects remote worker | Production frontends |
| `--single-server-gpu` | Any server with GPU | UI + GPU inference | All-in-one deployment |
| `--single-server-cpu` | Any server | UI + slow CPU inference | Dev/testing only |

**Worker containers:** Run without any flag (always GPU-enabled)

---

## 📊 Deployment Scenarios

### Scenario 1: Frontend Testing (Current Need - Session 23)

```bash
# On mello (no GPU) - just validating workflows
cd /home/dev/projects/comfyume
docker run -p 8199:8188 comfyume-frontend:v0.11.0 \
  python main.py --frontend-testing

# What happens:
# ✅ UI loads
# ✅ Workflows validate
# ❌ Can't actually generate (no worker)
```

### Scenario 2: Single-Server Mode (GPU Machine)

```bash
# On a machine with GPU (e.g., Verda CPU instance + serverless)
docker compose up -d  

# Services started:
# - frontends (--dual-server OR no flag if inference local)
# - queue-manager
# - redis
# - worker-1 (GPU-enabled, no --cpu flag)

# Environment:
REDIS_HOST=redis  # Default (local Docker network)
```

### Scenario 3: Dual-Server Mode (Production)

```bash
# Server 1: Mello VPS (no GPU)
cd /home/dev/projects/comfyume
git checkout mello-track
docker compose up -d  
# Starts: frontends (--dual-server), queue-manager, redis, admin

# Server 2: Verda GPU Cloud
cd /home/dev/projects/comfyume
git checkout verda-track
REDIS_HOST=100.99.216.71 docker compose up -d worker-1
# Starts: worker-1 only (GPU-enabled)
```

### Scenario 4: Verda CPU Instance + Serverless GPU

```bash
# Verda CPU instance (cheap, always-on)
docker compose up -d
# Starts: frontends, queue-manager, redis, admin
# NO worker-1 (serverless handles inference)

# Serverless GPU workers (auto-scale 0→N)
# Configured via INFERENCE_PROVIDER=modal/runpod/verda
# Workers spin up based on queue depth
```

---

## 🔧 Command Execution Hierarchy

### Where Commands Are Set

```
1. Dockerfile CMD (default)
   ├─ comfyui-frontend/Dockerfile: CMD [..., "--cpu"]
   └─ comfyui-worker/start-worker.sh: python main.py (no --cpu)

2. docker-compose.yml (can override)
   ├─ user001-020: image: (inherits Dockerfile CMD)
   └─ worker-1: CMD ["/workspace/start-worker.sh"]

3. Manual override
   └─ docker run ... <custom-command>
```

### How System Knows Local vs Remote

**Not via code - via configuration:**

```yaml
# Worker service
environment:
  - REDIS_HOST=${REDIS_HOST:-redis}
  #              ^^^^^^^^           ^^^^^ Local (single-server)
  #              From .env          Default
```

| Deployment | REDIS_HOST Value | Where Services Run |
|------------|------------------|-------------------|
| **Single-Server** | `redis` | All on one machine |
| **Dual-Server** | `100.99.216.71` | Frontends on mello, worker on Verda |

---

## 🎯 Implementation Requirements

### 1. Worker Must Support CPU AND GPU

**Why:**
- Not all models require GPU (many run on CPU)
- Verda CPU instances may be used with serverless GPU
- Single-server mode flexibility

**Implementation:**
```bash
# Worker should detect GPU availability
if nvidia-smi &>/dev/null; then
  python main.py --listen 0.0.0.0  # GPU mode
else
  python main.py --listen 0.0.0.0 --cpu  # CPU fallback
fi
```

### 2. Clear Flag Nomenclature (Issue #25 → comfyume)

**Changes needed:**
- Replace `--cpu` with `--frontend-testing` in frontend Dockerfile
- Add deployment mode flags: `--single-server-*`, `--dual-server`
- Update all documentation
- Update CLAUDE.md gotchas section

### 3. Orchestration Options

**Current: Manual (No Orchestration)**
```bash
# Step 1: SSH to mello
./scripts/start.sh

# Step 2: SSH to Verda
docker compose up -d worker-1
```

**Option A: SSH-based Script**
```bash
# scripts/start-all.sh on mello
docker compose up -d  # Local services
ssh verda 'cd /root/comfyume && docker compose up -d worker-1'
```

**Option B: Docker Swarm**
- Multi-host orchestration
- Automatic service placement
- Built-in load balancing

**Option C: Keep Manual**
- Simpler
- More control
- Verda is ephemeral (delete when not needed)

---

## 📝 Related Issues

- **comfy-multi #25** - Rename CPU/GPU mode terminology
- **comfyume #17** - Update workflow templates (IN PROGRESS - Session 23)
- **comfyume #7** - Team coordination channel

---

## ✅ Next Steps (Session 23+)

1. ✅ Document architecture findings (this file!)
2. Create GitHub Issue: Container Orchestration & Flags
3. Run /CLAUDE-HANDOVER to capture session
4. Test workflows with `--frontend-testing` flag
5. Coordinate with Verda team on worker integration
