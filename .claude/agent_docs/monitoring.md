# Monitoring & Management Tools

## Portainer -- Container Monitoring & Management

- Uses Tailscale Tailnet -- verda, mello, aeon (Mac)
- Can see containers across app
- Monitor resource consumption
- Restart containers
- If GPU is ticked on Verda's Portainer config -- can manage NVIDIA GPU resources

## Monitoring Stack (Verda, #106)

**Installed on Verda (95.216.229.236):**
- Prometheus (:9090)
- Grafana (:3001)
- Loki (:3100)
- cAdvisor (:8081)
- Promtail
- Dry
- Verda SDK (`pip install verda`)
- OpenTofu (`tofu`)

**Docs:** [Verda IaC](https://docs.verda.com/infrastructure-as-code/overview) | [OpenTofu](https://opentofu.org/docs/language/) | [Modules](https://search.opentofu.org/modules/)

**Claude Skills:** `/verda-ssh`, `/verda-status`, `/verda-logs`, `/verda-containers`, `/verda-terraform`, `/verda-open-tofu`, `/verda-prometheus`, `/verda-dry`, `/verda-loki`, `/verda-grafana`, `/verda-monitoring-check`, `/verda-debug-containers`

**Grafana dashboards:** Docker Containers (15331), Container Resources (14678), NVIDIA DCGM (12239)
