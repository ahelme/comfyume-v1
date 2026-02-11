**Project:** ComfyuME
**Doc Created:** 2026-02-09
**Doc Updated:** 2026-02-09

# Verda Skills Guide

These 12 skills let you manage and debug the Verda production server (95.216.229.236 / aiworkshop.art) from Claude Code CLI. Type `/skill-name` to run one.

## Quick Reference

| Skill | What it does | When to use |
|-------|-------------|-------------|
| `/verda-ssh` | Run any command on Verda | One-off checks, custom commands |
| `/verda-status` | Full server health overview | First thing to check when something seems off |
| `/verda-logs` | Fetch logs for a specific service | After spotting a problem, to see what happened |
| `/verda-containers` | Manage serverless GPU containers | Check if GPU inference is working |
| `/verda-monitoring-check` | Quick pass/fail for all monitoring tools | "Is my monitoring stack even running?" |
| `/verda-prometheus` | Query CPU/memory/network metrics | Diagnosing performance issues |
| `/verda-loki` | Search logs across all containers | Finding errors across the whole system |
| `/verda-grafana` | Manage Grafana dashboards | Setting up or checking visual dashboards |
| `/verda-dry` | Docker TUI (interactive) | Hands-on container browsing (run yourself) |
| `/verda-terraform` | Terraform/IaC reference | Managing Verda infrastructure as code |
| `/verda-open-tofu` | OpenTofu reference (open-source Terraform) | Same as above, using `tofu` command |
| `/verda-debug-containers` | Step-by-step container debugging playbook | Containers crashing, models not loading |

## General

### `/verda-ssh`
Runs a command on Verda via SSH. Pass the command as an argument. Without arguments, it shows uptime, disk, memory, and top containers.

**Example:** `/verda-ssh df -h /mnt/models-block-storage`
**Output:** Disk usage for the models storage mount.

### `/verda-status`
Runs a full health check: system resources, Docker containers, monitoring services, open ports, and serverless status. Results come back as a summary table.

**Example:** `/verda-status`
**Output:** Uptime, RAM/disk usage, container list with status, which monitoring services are active, and whether the Verda SDK connects.

### `/verda-logs`
Fetches the last 50 lines of logs for a named service. Knows whether to use `docker logs` (for containers like nginx, queue-manager, user001) or `journalctl` (for Prometheus, Loki, Grafana, Promtail).

**Example:** `/verda-logs queue-manager`
**Output:** Recent queue-manager log output -- look here for serverless errors, job failures, etc.

**Example:** `/verda-logs` (no argument)
**Output:** Last 10 lines from queue-manager, nginx, and admin -- the three most useful services.

## Monitoring

### `/verda-monitoring-check`
One-shot health check of the entire monitoring stack. Hits health endpoints for Prometheus, Loki, Grafana, checks cAdvisor and Promtail status, shows scrape targets, and reports disk usage for monitoring data.

**Example:** `/verda-monitoring-check`
**Output:** A status table like:

| Service | Status |
|---------|--------|
| Prometheus (:9090) | OK |
| Loki (:3100) | OK |
| Grafana (:3001) | OK |
| cAdvisor (:8081) | running |
| Promtail | active |

### `/verda-prometheus`
Queries Prometheus metrics. You can pass a PromQL query as an argument, or run it without arguments to see a reference of useful queries (container CPU, memory, network, restarts).

**Example:** `/verda-prometheus container_memory_usage_bytes{name=~"comfy-.*"}`
**Output:** Current memory usage for all comfy containers.

**Useful queries to know:**
- `up` -- which scrape targets are reachable
- `rate(container_cpu_usage_seconds_total{name=~"comfy-.*"}[5m])` -- CPU usage per container

### `/verda-loki`
Searches logs across all containers using LogQL. Pass a query or keyword. Loki stores 7 days of logs and is fed by Promtail.

**Example:** `/verda-loki {container_name="comfy-queue-manager"} |= "error"`
**Output:** Recent error lines from the queue manager.

**Handy filters:**
- `|= "error"` -- lines containing "error"
- `!= "health"` -- exclude health check noise
- `|~ "model.*not found"` -- regex match

### `/verda-grafana`
Manages Grafana (visual dashboards on port 3001). Can check health, list data sources, list/import dashboards, or change the admin password.

**Example:** `/verda-grafana`
**Output:** Health status and list of configured dashboards.

**Installed dashboards:** Docker Containers (15331), Container Resources (14678), NVIDIA DCGM (12239 -- for GPU instances).

**Access Grafana in browser:** `http://95.216.229.236:3001` (default login: admin/admin).

### `/verda-dry`
Dry is a visual Docker manager that runs in your terminal. Claude cannot use it directly -- this skill tells you how to launch it yourself.

**To use:** Open a terminal and run `ssh -t root@95.216.229.236 "dry"`

**Key shortcuts:** `Enter` = details, `l` = logs, `s` = stats, `r` = restart, `q` = quit.

## Infrastructure

### `/verda-containers`
Manages Verda serverless GPU containers (H200, B300). Can list deployments, check endpoint health, and show which serverless config is active.

**Example:** `/verda-containers health`
**Output:** HTTP response from the active serverless endpoint's health check.

**Current endpoints:** H200 Spot, H200 On-Demand, B300 Spot, B300 On-Demand. The active one is set by `SERVERLESS_ACTIVE` in `.env`.

### `/verda-terraform`
Reference for managing Verda infrastructure as code. Shows provider config, supported resources (instances, volumes, SSH keys, containers), and common commands.

**Example:** `/verda-terraform plan`
**Output:** Preview of what infrastructure changes would be applied.

**Config lives at:** `/root/tofu/` on Verda.

### `/verda-open-tofu`
Same as `/verda-terraform` but specifically for OpenTofu (the open-source fork). The `tofu` command is installed on Verda. Syntax is identical to Terraform.

**Example:** `/verda-open-tofu`
**Output:** CLI reference and config file locations.

## Debugging

### `/verda-debug-containers`
A full 6-step debugging playbook for when containers are broken. Checks health, model paths/mounts, Loki errors, Prometheus metrics, serverless endpoints, and Docker logs. Knows about specific issues (#101 model paths, #103 SFS architecture).

**Example:** `/verda-debug-containers`
**Output:** Walks through all 6 steps and reports findings.

**Example:** `/verda-debug-containers models`
**Output:** Focuses on model path and mount debugging only.

## Common Scenarios

| Situation | Skills to use |
|-----------|--------------|
| "Is the server up?" | `/verda-status` |
| "Site is slow or unresponsive" | `/verda-status` then `/verda-prometheus` (check CPU/memory) |
| "Users can't generate images/video" | `/verda-logs queue-manager` then `/verda-containers health` |
| "A container keeps restarting" | `/verda-debug-containers` then `/verda-logs <container>` |
| "Models not loading" | `/verda-debug-containers models` |
| "Is monitoring working?" | `/verda-monitoring-check` |
| "I want to see error trends over time" | `/verda-loki` with an error filter, or `/verda-grafana` in browser |
| "Need to check GPU container status" | `/verda-containers` |
| "Want to browse containers visually" | `/verda-dry` (run in your own terminal) |
| "Planning infrastructure changes" | `/verda-terraform` or `/verda-open-tofu` |
| "Quick one-off server command" | `/verda-ssh <command>` |
| "Disk filling up?" | `/verda-ssh df -h` or `/verda-status` |
