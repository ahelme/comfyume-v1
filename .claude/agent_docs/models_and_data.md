# Models, Workflows & Data

Workshop workflow templates, ML models, LoRAs, and model inventory.

## Selected Templates for Workshop

Inference runs on serverless containers (Verda (ex. DataCrunch) H200/B300). No dedicated GPU instance required.

**Template 1: Flux Klein 9B - Text to Image**
- File: `flux2_klein_9b_text_to_image.json`
- Use case: High-quality image generation
- Inference: Serverless containers (H200 141GB / B300 288GB)
- VRAM: ~12-16GB

**Template 4: LTX-2 Distilled - Text to Video**
- File: `ltx2_text_to_video_distilled.json`
- Use case: Fast video generation (distilled = faster than standard)
- Inference: Serverless containers (H200 141GB / B300 288GB)
- VRAM: ~20-25GB

### Required Models (EXACT MATCHES)

**Flux Klein 9B:**
```
diffusion_models/flux-2-klein-9b-fp8.safetensors
https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/diffusion_models/flux-2-klein-9b-fp8.safetensors

text_encoders/qwen_3_8b_fp8mixed.safetensors (8.07 GB)
https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors

vae/flux2-vae.safetensors (320 MB)
https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors
```

**LTX-2 Distilled:**
```
checkpoints/ltx-2-19b-dev-fp8.safetensors (27 GB)
text_encoders/gemma_3_12B_it.safetensors (20 GB)
loras/ltx-2-19b-distilled-lora-384.safetensors
latent_upscale_models/ltx-2-spatial-upscaler-x2-1.0.safetensors
```

### Success Criteria
- Both templates load in ComfyUI
- Flux Klein generates image in <30 seconds
- LTX-2 Distilled generates video in 1-2 minutes
- No model loading errors

---

## Workshop Workflow Templates (5 files in data/workflows/)

All 5 auto-loaded into every user's ComfyUI via docker-entrypoint.sh on container start.
Each workflow uses subgraphs (reusable node groups) as selectable pipelines.

**1. `flux2_klein_9b_text_to_image.json` - HIGH-QUALITY IMAGE GENERATION**
- 2 subgraphs: Base (~20 steps, best quality) + Distilled (~4 steps, fast drafts)
- Models: `diffusion_models/flux-2-klein-base-9b-fp8.safetensors` (9GB, base)
          `diffusion_models/flux-2-klein-9b-fp8.safetensors` (distilled, gated HF)
          `text_encoders/qwen_3_8b_fp8mixed.safetensors` (8GB)
          `vae/flux2-vae.safetensors` (321MB, shared with 4B)
- VRAM: ~12-16GB | Source: `black-forest-labs/FLUX.2-klein-base-9b-fp8` (Non-Commercial License)

**2. `flux2_klein_4b_text_to_image.json` - FAST IMAGE GENERATION (lighter)**
- 2 subgraphs: Base + Distilled (same structure as 9B but smaller/faster)
- Models: `diffusion_models/flux-2-klein-base-4b.safetensors` (base)
          `diffusion_models/flux-2-klein-4b.safetensors` (distilled)
          `text_encoders/qwen_3_4b.safetensors`
          `vae/flux2-vae.safetensors` (shared)
- VRAM: ~8-10GB | Source: `black-forest-labs/FLUX.2-klein-base-4b` (Apache 2.0)

**3. `ltx2_text_to_video.json` - FULL VIDEO GENERATION (primary workshop template)**
- 1 subgraph: "Text to Video (LTX 2.0)" - 41 nodes, full pipeline
- Features: text-to-video, spatial upscaling, camera control (dolly LoRA)
- Models: `checkpoints/ltx-2-19b-dev-fp8.safetensors` (25GB)
          `text_encoders/gemma_3_12B_it_fp4_mixed.safetensors` (8.8GB)
          `latent_upscale_models/ltx-2-spatial-upscaler-x2-1.0.safetensors` (950MB)
          `loras/ltx-2-19b-distilled-lora-384.safetensors` (7.1GB, speed boost)
          `loras/ltx-2-19b-lora-camera-control-dolly-left.safetensors` (313MB, camera moves)
- VRAM: ~20-25GB | Source: `Comfy-Org/ltx-2`, `Lightricks/LTX-2`

**4. `ltx2_text_to_video_distilled.json` - FAST VIDEO GENERATION**
- 1 subgraph: "Text to Video (LTX 2 Distilled)" - 36 nodes, fewer steps
- Same features as #3 but uses distilled checkpoint for faster inference
- Models: `checkpoints/ltx-2-19b-distilled.safetensors` (15GB)
          `text_encoders/gemma_3_12B_it_fp4_mixed.safetensors` (shared)
          `latent_upscale_models/ltx-2-spatial-upscaler-x2-1.0.safetensors` (shared)
          `loras/ltx-2-19b-lora-camera-control-dolly-left.safetensors` (shared, camera moves)

**5. `example_workflow.json` - MINIMAL EXAMPLE**
- Empty/minimal workflow, no models required

---

## Camera Control LoRAs for Filmmakers

All ~313MB-2.1GB, stored in loras/:

| LoRA | Movement | Size | Download |
|------|----------|------|----------|
| `ltx-2-19b-lora-camera-control-static.safetensors` | Static framing | 2.1GB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Static/resolve/main/ltx-2-19b-lora-camera-control-static.safetensors) |
| `ltx-2-19b-lora-camera-control-dolly-in.safetensors` | Dolly in | 313MB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Dolly-In/resolve/main/ltx-2-19b-lora-camera-control-dolly-in.safetensors) |
| `ltx-2-19b-lora-camera-control-dolly-out.safetensors` | Dolly out | 313MB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Dolly-Out/resolve/main/ltx-2-19b-lora-camera-control-dolly-out.safetensors) |
| `ltx-2-19b-lora-camera-control-dolly-left.safetensors` | Dolly left | 313MB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Dolly-Left/resolve/main/ltx-2-19b-lora-camera-control-dolly-left.safetensors) |
| `ltx-2-19b-lora-camera-control-dolly-right.safetensors` | Dolly right | 313MB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Dolly-Right/resolve/main/ltx-2-19b-lora-camera-control-dolly-right.safetensors) |
| `ltx-2-19b-lora-camera-control-jib-up.safetensors` | Jib up | 2.1GB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Jib-Up/resolve/main/ltx-2-19b-lora-camera-control-jib-up.safetensors) |
| `ltx-2-19b-lora-camera-control-jib-down.safetensors` | Jib down | 2.1GB | [HF](https://huggingface.co/Lightricks/LTX-2-19b-LoRA-Camera-Control-Jib-Down/resolve/main/ltx-2-19b-lora-camera-control-jib-down.safetensors) |
| `ltx-2-19b-distilled-lora-384.safetensors` | Speed (fewer steps) | 7.1GB | [HF](https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-19b-distilled-lora-384.safetensors) |

---

## All Models on Disk (as of 2026-02-08, 172GB total on /mnt/sfs)

| File | Dir | Size | Status | Download |
|------|-----|------|--------|----------|
| `flux-2-klein-base-9b-fp8.safetensors` | diffusion_models | 9.0GB | ON DISK | [HF (gated)](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8/resolve/main/flux-2-klein-base-9b-fp8.safetensors) |
| `flux-2-klein-9b-fp8.safetensors` | diffusion_models | - | MISSING | gated HF, distilled 9B variant |
| `flux-2-klein-base-4b.safetensors` | diffusion_models | 7.3GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/diffusion_models/flux-2-klein-base-4b.safetensors) |
| `flux-2-klein-4b.safetensors` | diffusion_models | 7.3GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/diffusion_models/flux-2-klein-4b.safetensors) |
| `qwen_3_8b_fp8mixed.safetensors` | text_encoders | 8.1GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/flux2-klein-9B/resolve/main/split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors) |
| `qwen_3_4b.safetensors` | text_encoders | 7.5GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors) |
| `gemma_3_12B_it.safetensors` | text_encoders | 19GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it.safetensors) |
| `gemma_3_12B_it_fp4_mixed.safetensors` | text_encoders | 8.8GB | ON DISK | [HF](https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors) |
| `flux2-vae.safetensors` | vae | 321MB | ON DISK | [HF](https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors) |
| `ltx-2-19b-dev-fp8.safetensors` | checkpoints | 25GB | ON DISK | [HF](https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-19b-dev-fp8.safetensors) |
| `ltx-2-19b-distilled.safetensors` | checkpoints | 15GB | ON DISK | [HF](https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-19b-distilled.safetensors) |
| `flux2_klein_9b.safetensors` | checkpoints | 17GB | ON DISK | legacy full checkpoint |
| `flux2_klein_4b.safetensors` | checkpoints | 7.3GB | ON DISK | legacy full checkpoint |
| `ltx-2-spatial-upscaler-x2-1.0.safetensors` | latent_upscale_models | 950MB | ON DISK | [HF](https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-spatial-upscaler-x2-1.0.safetensors) |

## Required ComfyUI Nodes (built into v0.11.0)

- `LTXAVTextEncoderLoader`, `LTXVAudioVAEDecode`, `LTXVAudioVAELoader`, `LTXVEmptyLatentAudio`
