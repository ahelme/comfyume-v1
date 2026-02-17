# Project Structure

## Main Repository

```
/home/dev/comfyume/
├── .claude/
│   ├── progress-**.md                  # Session logs per team (UPDATE ON COMMITS)
│   ├── progress-all-teams.md           # Central 1-line-per-commit log
│   ├── commands/                       # Claude skills
│   └── agent_docs/                     # Progressive disclosure modules
├── implementation-*.md                 # Implementation plans for deployment phases
├── CLAUDE.md                           # Project guide
├── README.md                           # Public project documentation
├── .env                                # Local configuration (gitignored -- FULL OF SECRETS)
├── .env.example                        # Template configuration
├── docker-compose.yml                  # Main orchestration (includes docker-compose.users.yml)
├── docker-compose.users.yml            # 20 USER CONTAINERS - per-user isolation (auto-generated)
├── nginx/                              # Reverse proxy
├── queue-manager/                      # FastAPI service
├── comfyui-worker/                     # GPU worker
├── comfyui-frontend/                   # User UI container base (builds 20 per-user images)
├── admin/                              # Admin dashboard
├── scripts/
│   ├── generate-user-compose.sh        # Regenerates docker-compose.users.yml
│   ├── start.sh                        # Start all services
│   └── stop.sh                         # Stop all services
├── data/
│   ├── user_data/                      # Per-user persistent data (backed up to R2)
│   │   ├── user001/
│   │   │   ├── comfyui.db              # User settings database
│   │   │   ├── default/                # User preferences
│   │   │   └── comfyui/
│   │   │       └── custom_nodes/       # User-installed custom nodes (mounted per-user)
│   │   │           ├── ComfyUI-Manager/
│   │   │           └── my-custom-node/
│   │   ├── user002/
│   │   │   └── ... (same structure)
│   │   └── ... (user003-user020)
│   ├── workflows/                      # Shared template workflows (read-only to all users)
│   │   ├── flux2_klein_9b_text_to_image.json
│   │   ├── flux2_klein_4b_text_to_image.json
│   │   ├── ltx2_text_to_video.json
│   │   ├── ltx2_text_to_video_distilled.json
│   │   └── example_workflow.json
│   ├── models/
│   │   ├── shared/                     # Shared models (at /mnt/sfs on Verda)
│   │   │   ├── checkpoints/
│   │   │   ├── text_encoders/
│   │   │   ├── loras/
│   │   │   ├── vae/
│   │   │   └── latent_upscale_models/
│   │   └── user/                       # User-specific models (future)
│   ├── inputs/                         # User uploads (symlinked to Verda block storage - EPHEMERAL)
│   │   ├── user001/
│   │   └── ... (user002-user020)
│   └── outputs/                        # User outputs (symlinked to Verda block storage - EPHEMERAL)
│       ├── user001/
│       └── ... (user002-user020)
└── docs/                               # User/admin guides
```

## Private Scripts Repository

```
/home/dev/projects/comfymulti-scripts/  # PRIVATE REPO FOR SCRIPTS & SECRETS
├── .env                           # HOW SECRET/PRIVATE .env IS SHARED BETWEEN DEVS
├── README-RESTORE.md              # Basic backup/restore doc
├── restore-verda-instance.sh      # Production app server restore script (v0.4.0)
├── setup-verda-solo-script.sh     # Legacy GPU worker setup script (v0.3.3)
├── backup-cron.sh                 # Hourly backups: Verda->SFS + user data->R2
├── backup-user-data.sh            # Backs up user files (workflows, outputs, inputs) to R2
├── backup-verda.sh                # Backs up all data to R2 before instance deleted
└── archive/                       # Legacy scripts (quick-start.sh, RESTORE-SFS.sh)
```
