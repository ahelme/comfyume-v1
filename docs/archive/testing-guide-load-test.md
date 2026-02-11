**Project:** ComfyUme
**Project Desc:** ComfyUI Multi-User Workshop Platform
**Project Started:** 2026-01-02
**Repository:** github.com/ahelme/comfyume
**Domain:** comfy.ahelme.net
**Doc Created:** 2026-02-01
**Doc Updated:** 2026-02-01

---

# Testing Guide - Multi-User Load Testing

This guide covers load testing procedures for Issue #19 (Phase 3: Multi-user load test).

## Overview

The load testing framework validates:
- ✅ 20 concurrent user containers
- ✅ Queue management under load
- ✅ Worker distribution
- ✅ Output isolation per user
- ✅ Zero deadlocks
- ✅ Acceptable memory usage

## Prerequisites

**Required Services:**
- queue-manager (healthy)
- redis (healthy)
- At least 1 worker (for end-to-end testing)

**Infrastructure:**
- User data directories initialized
- Docker compose users file generated
- Workflow templates available

## Setup

### 1. Initialize User Data

Creates directory structure for all 20 users:

```bash
./scripts/init-user-data.sh
```

This creates:
- `data/user_data/user001/` through `data/user_data/user020/`
- Custom nodes per user
- User preference directories

### 2. Generate User Containers

Creates `docker-compose.users.yml` for 20 frontend containers:

```bash
./scripts/generate-user-compose.sh
```

Configuration:
- Batch size: 5 users per batch
- Total batches: 4
- Batch leaders: user001, user006, user011, user016

### 3. Start Services

Start all services including 20 user frontends:

```bash
docker compose up -d
```

Expected startup time:
- Without workers: ~30-60 seconds (frontends only)
- With workers: ~2-3 minutes (includes GPU initialization)

## Running Load Tests

### Basic Load Test (100 jobs)

Submit 5 jobs per user (100 total):

```bash
./scripts/load-test.sh
```

Default configuration:
- Users: 20
- Jobs per user: 5
- Total jobs: 100
- Workflow: `example_workflow.json`

### Custom Configuration

Override defaults via environment variables:

```bash
# Test with 10 jobs per user (200 total)
JOBS_PER_USER=10 ./scripts/load-test.sh

# Use different workflow
TEST_WORKFLOW=flux2_klein_4b_text_to_image.json ./scripts/load-test.sh

# Test with fewer users
NUM_USERS=5 ./scripts/load-test.sh
```

## Monitoring

### Real-time Queue Monitor

Watch queue statistics during testing:

```bash
./scripts/monitor-queue.sh
```

Displays:
- Queue depth
- Pending/running/completed jobs
- Worker count
- Container status

Refresh interval: 2 seconds (configurable via `REFRESH_INTERVAL`)

### Manual Monitoring

**Queue status API:**
```bash
curl http://localhost:3000/api/queue/status | jq
```

**Worker logs:**
```bash
docker logs -f comfy-worker-1
```

**Container health:**
```bash
docker ps --filter "name=comfy-"
```

## Validation

### Automated Validation

Run post-test validation checks:

```bash
./scripts/validate-load-test.sh
```

Validates:
1. All 20 containers started
2. Queue manager healthy
3. Zero failed jobs
4. Output directories isolated
5. Resource limits applied

Exit codes:
- `0` = All tests passed
- `1` = Some tests failed

### Manual Validation

**Check output isolation:**
```bash
ls -lh data/outputs/user*/
```

Each user should have isolated output directory.

**Check queue depth over time:**
```bash
watch -n 1 'curl -s http://localhost:3000/api/queue/status | jq'
```

Queue depth should decrease as workers process jobs.

## Success Criteria (Issue #19)

Must achieve:
- ✅ Zero failed jobs
- ✅ All 20 containers started
- ✅ Batches complete within 3 minutes
- ✅ Isolated outputs per user
- ✅ No queue deadlocks
- ✅ Memory usage within limits (2G per container)

## Troubleshooting

### Containers fail to start

**Check Docker resources:**
```bash
docker system df
docker system prune  # if needed
```

**Check logs:**
```bash
docker logs comfy-user001
```

### Queue manager unhealthy

**Check Redis connection:**
```bash
docker logs comfy-queue-manager
docker logs comfy-redis
```

**Verify Redis password:**
```bash
docker exec -it comfy-redis redis-cli -a "$REDIS_PASSWORD" ping
```

### Jobs stuck in queue

**Check worker status:**
```bash
docker ps --filter "name=worker"
docker logs comfy-worker-1
```

**Verify queue-manager → worker connection:**
```bash
curl http://localhost:3000/api/workers/status
```

### High memory usage

**Check container memory:**
```bash
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"
```

**Restart containers if needed:**
```bash
docker compose restart
```

## Performance Benchmarks

Expected performance (development environment):

**Without GPU workers (infrastructure only):**
- Container startup: 30-60 seconds
- Job submission: <5 seconds for 100 jobs
- Queue manager response: <100ms

**With GPU workers (end-to-end):**
- Container startup: 2-3 minutes
- Job processing: Depends on workflow complexity
- Example workflow: ~2-5 seconds per job

**Production (Verda H100):**
- LTX-2 video (5 sec): ~30-60 seconds
- Flux2 Klein image: ~5-10 seconds

## Related Documentation

- Issue #19: Phase 3: Multi-user load test
- Issue #18: End-to-end job submission test
- Issue #20: Workshop readiness checklist
- Admin Guide: [docs/admin-backup-restore.md](./admin-backup-restore.md)

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `init-user-data.sh` | Initialize 20 user directories | `./scripts/init-user-data.sh` |
| `generate-user-compose.sh` | Generate user containers config | `./scripts/generate-user-compose.sh` |
| `load-test.sh` | Submit jobs from all users | `./scripts/load-test.sh` |
| `monitor-queue.sh` | Real-time queue monitoring | `./scripts/monitor-queue.sh` |
| `validate-load-test.sh` | Validate test results | `./scripts/validate-load-test.sh` |

---

**Last Updated:** 2026-02-01
