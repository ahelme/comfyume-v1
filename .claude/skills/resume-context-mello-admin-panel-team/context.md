# CLAUDE RESUME - COMFYUME (ADMIN PANEL TEAM)

**DATE**: 2026-02-10

---

## CONTEXT

**We are the Mello Admin Panel Team.** Branch: `mello-admin-panel-team`.

**Production:** aiworkshop.art runs on Verda CPU instance (see `VERDA_PUBLIC_IP` in `.env`), NOT Mello.

---

## IMMEDIATE PRIORITY

### 1. Fix yaml key on REAL SFS (#101)

**Root cause confirmed:** `/mnt/sfs/extra_model_paths.yaml` has wrong key `upscale_models` — needs `latent_upscale_models`. ComfyUI uses yaml key verbatim as folder type (no aliasing except `unet`→`diffusion_models`, `clip`→`text_encoders`). Confirmed by ComfyUI issue #12004.

**The `sed` fix was applied but DID NOT WORK** — container logs still show `Adding extra search path upscale_models`. The `sed -i 's/^upscale_models:/latent_upscale_models:/'` likely failed because the yaml key is indented (not at column 0). Need a `sed` without the `^` anchor, or use python/awk.

**Fix command (corrected — no `^` anchor):**
```
bash -c "sed -i 's/upscale_models:/latent_upscale_models:/' /mnt/sfs/extra_model_paths.yaml && python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --extra-model-paths-config /mnt/sfs/extra_model_paths.yaml"
```
After one successful startup, revert to normal cmd:
```
python3 /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --extra-model-paths-config /mnt/sfs/extra_model_paths.yaml
```

Also fix `clip:` → `text_encoders:` for consistency (works via legacy map but fragile).

### 2. Investigate missing UI feedback on job completion

**Flux inference IS WORKING end-to-end!** Jobs submit (201), dispatch to serverless (200), execute (113s). But the user sees no feedback in ComfyUI UI. The generated images stay on the serverless container — no mechanism to push results back to the user's browser. This is a separate issue from #101.

**Queue-manager logs confirm:**
- `POST /api/jobs` → 201 Created
- `HTTP Request: POST .../comfyume-vca-ftv-h200-spot/prompt "HTTP/1.1 200 OK"`
- Serverless logs: `Prompt executed in 113.63 seconds` (Flux loaded, VAE, text encoder — all working)

### 3. Storage situation (#103)

| Storage | What | Serverless sees? | Instance sees? |
|---------|------|-----------------|----------------|
| **REAL SFS** | Verda NFS share (172GB models) | YES at `/mnt/sfs` | NO (NFS mount fails) |
| **Block storage** | 220GB on CPU instance | NO | YES at `/mnt/models-block-storage` |

Can't SSH-edit REAL SFS — must fix via serverless startup command.

---

## MONITORING STACK (#106) + SUBDOMAINS (#109)

All live. Use `/verda-monitoring-check` to verify.

| Tool | Port | Access |
|------|------|--------|
| Prometheus | :9090 | https://prometheus.aiworkshop.art (basic auth) |
| Grafana | :3001 | https://grafana.aiworkshop.art (admin login) |
| Loki | :3100 | via Grafana or SSH |
| cAdvisor | :8081 | via Prometheus |
| Promtail | :9080 | ships Docker logs → Loki |
| Portainer | :9443 | https://portainer.aiworkshop.art |

Subdomains reverse-proxied through Mello nginx → Verda via Tailscale. Let's Encrypt certs auto-renew.

**12 skills:** `/verda-ssh`, `/verda-status`, `/verda-logs`, `/verda-containers`, `/verda-terraform`, `/verda-open-tofu`, `/verda-prometheus`, `/verda-dry`, `/verda-loki`, `/verda-grafana`, `/verda-monitoring-check`, `/verda-debug-containers`

---

## KEY RESEARCH FINDINGS (this session)

**ComfyUI folder_paths.py:**
- `extra_config.py:load_extra_path_config()` iterates yaml keys
- Each key passed to `folder_paths.add_model_folder_path(key, path)`
- `map_legacy()` only maps `unet`→`diffusion_models` and `clip`→`text_encoders`
- Yaml key IS the folder type verbatim — no other aliasing
- The repo's yaml (`comfyui-worker/extra_model_paths.yaml`) already has correct keys

**Verda SDK:**
- `update_deployment(name, deployment)` takes a full `Deployment` object, NOT kwargs
- No container logs via SDK or API
- No exec/shell into containers
- Can query ComfyUI API through inference endpoint (e.g. `/object_info`)

---

## GITHUB ISSUES

- **#101** — OPEN. Root cause confirmed, sed fix attempted but failed (indentation). Flux inference works, LTX-2 blocked.
- **#103** — OPEN. REAL SFS only accessible from serverless containers.
- **#106** — OPEN. Monitoring stack complete. Subdomains live.
- **#109** — OPEN. SSL certs for 5 subdomains complete.

---

## SESSION START CHECKLIST

- [ ] Read `.claude/agent_docs/progress-mello-admin-panel-team-dev.md` top section
- [ ] Run `/verda-monitoring-check` to verify stack is healthy
- [ ] Fix #101: re-run sed without `^` anchor via Verda console
- [ ] Investigate result delivery: how do serverless outputs get back to user?
