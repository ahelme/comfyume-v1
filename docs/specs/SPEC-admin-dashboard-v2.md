# SPEC: Admin Dashboard v2.0

**Project:** ComfyUI Multi-User Workshop Platform
**Author:** Claude + User
**Created:** 2026-02-05
**Status:** DRAFT - Awaiting Review

---

## Overview

Comprehensive admin dashboard for managing the ComfyuME platform, including infrastructure monitoring, user management, deployment switching, and container orchestration.

## Current State

- Basic admin dashboard at `/admin`
- Shows: instance status (20 users), shared models list
- No real-time monitoring
- No deployment management
- No storage visibility

## Proposed Features

### 1. Infrastructure Overview Panel

**Server Status Cards:**
| Metric | Source | Display |
|--------|--------|---------|
| Mello VPS Status | systemd/docker | 🟢 Online / 🔴 Offline |
| Verda Instance | Verda API | 🟢 Running / 🟡 Stopped / ⚫ None |
| Serverless Status | Container endpoint health | 🟢 Ready / 🟡 Cold / 🔴 Error |
| Redis | redis-cli ping | 🟢 Connected / 🔴 Disconnected |
| Tailscale VPN | tailscale status | 🟢 Connected / 🔴 Disconnected |

**OS & Version Info:**
```
┌─────────────────────────────────────────────────────────┐
│ System Information                                       │
├─────────────────────────────────────────────────────────┤
│ Mello OS:     Ubuntu 24.04 LTS (6.8.0-94-generic)       │
│ Verda OS:     Ubuntu 22.04 LTS (if running)             │
│ Docker:       27.4.1                                     │
│ Nginx:        1.24.0                                     │
│ Redis:        7.2.4                                      │
│ Python:       3.11.x                                     │
│ ComfyUI:      v0.11.0                                    │
│ Node.js:      (if applicable)                            │
└─────────────────────────────────────────────────────────┘
```

### 2. Storage Monitoring Panel

**Mello Storage:**
| Mount | Used | Total | % | Bar |
|-------|------|-------|---|-----|
| `/` (root) | 45GB | 80GB | 56% | ████████░░░░ |
| `/home/dev` | 32GB | 80GB | 40% | ██████░░░░░░ |

**Verda Storage (when running):**
| Mount | Used | Total | % | Bar |
|-------|------|-------|---|-----|
| SFS `/mnt/sfs` | 85GB | 100GB | 85% | ██████████░░ |
| Block (scratch) | 12GB | 50GB | 24% | ███░░░░░░░░░ |
| OS disk | 28GB | 50GB | 56% | ███████░░░░░ |

**R2 Cloud Storage:**
| Bucket | Size | Objects |
|--------|------|---------|
| comfyume-model-vault-backups | 45GB | 12 |
| comfyume-cache-backups | 3.2GB | 8 |
| comfyume-user-files-backups | 1.1GB | 156 |
| comfyume-worker-container-backups | 2.5GB | 2 |

**Directory Breakdown (expandable):**
```
📁 /mnt/sfs/models/ (77GB)
├── 📁 checkpoints/ (52GB)
│   ├── ltx-2-19b-dev-fp8.safetensors (27GB)
│   └── ...
├── 📁 text_encoders/ (20GB)
│   ├── gemma_3_12B_it.safetensors (12GB)
│   └── qwen_3_8b_fp8mixed.safetensors (8GB)
├── 📁 vae/ (320MB)
├── 📁 loras/ (1.2GB)
└── 📁 latent_upscale_models/ (500MB)
```

### 3. User Management Panel

**Active Users Grid:**
| User | Status | Last Active | Current Workflow | Queue Jobs |
|------|--------|-------------|------------------|------------|
| user001 | 🟢 Active | 2m ago | flux2_klein_9b | 2 pending |
| user002 | 🟡 Idle | 15m ago | - | 0 |
| user003 | ⚫ Offline | 2h ago | - | 0 |
| ... | | | | |

**Container Status per User:**
- Health check status (healthy/unhealthy/starting)
- Memory usage
- CPU usage
- Uptime
- Last restart time

**Actions:**
- 🔄 Restart container
- 🔌 Stop container
- 📋 View logs
- 🗑️ Clear user cache

### 4. GPU Deployment Switching Panel

**Current Active Deployment:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎮 Active: comfyume-vca-ftv-h200-spot                   │
│ GPU: H200 141GB | Price: €0.97/hr | Status: 🟢 Ready    │
│ Replicas: 1/20 | Queue: 3 jobs | Avg latency: 12s       │
└─────────────────────────────────────────────────────────┘
```

**One-Click Deployment Switcher:**
| Deployment | GPU | Price | Status | Action |
|------------|-----|-------|--------|--------|
| H200 Spot | H200 141GB | €0.97/hr | 🟢 Active | ━━━━━━━━ |
| H200 On-Demand | H200 141GB | €2.80/hr | ⚫ Inactive | [Activate] |
| B300 Spot | B300 288GB | €1.61/hr | ⚫ Inactive | [Activate] |
| B300 On-Demand | B300 288GB | €4.63/hr | ⚫ Inactive | [Activate] |
| Local Worker | (Verda instance) | ~€0.70/hr | ⚫ Stopped | [Start Instance] |

**Switching Workflow:**
1. Click [Activate] on target deployment
2. Confirm dialog with cost estimate
3. API call to update `SERVERLESS_ACTIVE` env var
4. Restart queue-manager
5. Verify health check on new endpoint
6. Update dashboard status

### 5. Container Management Panel

**Container Overview:**
| Container | Image | Size | Status | CPU | Memory | Actions |
|-----------|-------|------|--------|-----|--------|---------|
| comfy-queue-manager | comfyume-queue:v0.11.0 | 245MB | 🟢 Up 3d | 2% | 128MB | 🔄 📋 |
| comfy-redis | redis:7-alpine | 42MB | 🟢 Up 3d | 1% | 64MB | 🔄 📋 |
| comfy-admin | comfyume-admin:v0.11.0 | 89MB | 🟢 Up 3d | 1% | 32MB | 🔄 📋 |
| comfy-user001 | comfyume-frontend:v0.11.0 | 1.2GB | 🟢 Up 3d | 5% | 512MB | 🔄 📋 🛑 |
| comfy-user002 | comfyume-frontend:v0.11.0 | 1.2GB | 🟢 Up 3d | 3% | 480MB | 🔄 📋 🛑 |
| ... | | | | | | |

**Actions:**
- 🔄 Restart container
- 📋 View logs (last 100 lines)
- 🛑 Stop container
- 🔨 Rebuild container (requires confirmation)
- 🗑️ Remove container

**Bulk Actions:**
- [Restart All Frontends]
- [Stop All Frontends]
- [Rebuild All] (requires confirmation + progress bar)

### 6. Configuration Panel

**Key Config Files:**
| File | Location | Version/Hash | Last Modified | Actions |
|------|----------|--------------|---------------|---------|
| nginx.conf | /etc/nginx/sites-enabled/comfy.ahelme.net | sha256:abc123 | 2026-02-05 | 👁️ View |
| docker-compose.yml | /home/dev/projects/comfyume/ | git:060e0c4 | 2026-02-05 | 👁️ View |
| .env | /home/dev/projects/comfyume/ | (hidden) | 2026-02-04 | 👁️ View |
| queue-manager config | queue-manager/config.py | git:060e0c4 | 2026-02-05 | 👁️ View |

**Environment Variables (masked):**
```
REDIS_PASSWORD=****
SERVERLESS_API_KEY=****
VERDA_CLIENT_ID=kZqx...
SERVERLESS_ACTIVE=h200-spot
INFERENCE_MODE=serverless
```

### 7. Logs & Monitoring Panel

**Real-time Log Viewer:**
- Select container/service from dropdown
- Filter by level (INFO/WARN/ERROR)
- Search within logs
- Auto-scroll toggle
- Download logs button

**Metrics Dashboard (Grafana-lite):**
- Request rate (jobs/minute)
- Queue depth over time
- Average job duration
- Error rate
- GPU utilization (when using local worker)

### 8. Backup & Maintenance Panel

**Backup Status:**
| Type | Last Run | Status | Size | Action |
|------|----------|--------|------|--------|
| Hourly (Verda→SFS) | 2h ago | ✅ | N/A | [Run Now] |
| Daily (Mello→R2) | 18h ago | ✅ | 1.1GB | [Run Now] |
| Models (SFS→R2) | 3d ago | ✅ | 45GB | [Run Now] |

**Maintenance Actions:**
- [Clear Docker Cache] - `docker system prune`
- [Rotate Logs] - Archive and compress old logs
- [Update SSL Cert] - Renew Let's Encrypt
- [Sync Models] - Push local models to R2

---

## Technical Implementation

### Backend API Endpoints

```
GET  /admin/api/status           - Overall system status
GET  /admin/api/storage          - Storage metrics
GET  /admin/api/users            - User list with status
GET  /admin/api/containers       - Container list with metrics
GET  /admin/api/deployments      - Serverless deployment status
POST /admin/api/deployments/switch - Switch active deployment
POST /admin/api/containers/{id}/restart
POST /admin/api/containers/{id}/stop
POST /admin/api/containers/{id}/rebuild
GET  /admin/api/logs/{service}   - Stream logs via WebSocket
POST /admin/api/backup/{type}    - Trigger backup
```

### Data Sources

| Metric | Collection Method |
|--------|-------------------|
| Container stats | Docker API (`docker stats --format json`) |
| Disk usage | `df -h` + `du -sh` for directories |
| R2 bucket sizes | AWS CLI `aws s3 ls --summarize` |
| User activity | Redis pub/sub + WebSocket connections |
| Deployment status | Verda API |
| OS info | `/etc/os-release`, `uname -r` |

### Frontend Stack

- **Framework:** Vanilla JS or Alpine.js (keep it lightweight)
- **Styling:** Tailwind CSS or simple custom CSS
- **Charts:** Chart.js for metrics visualization
- **Real-time:** WebSocket for live updates
- **No build step:** Direct HTML/JS for simplicity

### Security

- HTTP Basic Auth (same as user auth)
- Admin-only credentials from `.env`
- CSRF protection on POST endpoints
- Rate limiting on sensitive actions
- Audit log for all admin actions

---

## Phases

### Phase 1: Core Dashboard (MVP)
- System status cards
- Storage overview (Mello only)
- Container list with restart/stop
- Basic log viewer

### Phase 2: Deployment Management
- GPU deployment switcher
- Serverless status monitoring
- One-click switching

### Phase 3: Advanced Monitoring
- Real-time metrics
- User activity tracking
- Grafana-lite charts

### Phase 4: Full Management
- R2 storage integration
- Backup triggers
- Configuration viewer
- Bulk container operations

---

## Open Questions

1. **Authentication:** Separate admin password or use existing user001 (instructor)?
2. **Mobile:** Need mobile-responsive design for phone management?
3. **Alerts:** Email/SMS notifications for critical issues?
4. **History:** Store metrics history for trend analysis?

---

## Related

- GitHub Issue: TBD (create after spec approval)
- Current admin: `/home/dev/projects/comfyume/admin/`
- Verda API docs: https://docs.datacrunch.io/
