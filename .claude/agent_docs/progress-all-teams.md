**Project:** ComfyuME Multi-User ComfyUI Workshop Platform | **Repo:** github.com/ahelme/comfyume-v1
**Doc Updated:** 2026-02-11

# All-Teams Progress (Ultra-Concise Commit Log)

## How to Update
**EVERY COMMIT** add one line: `- [TEAM] [HASH] [type]: [description] (#issue)`
Newest at top. One line per commit. No fluff. Link issues.

## Team Progress Files (FULL DETAIL)
- **Mello:** [progress-mello-team-one-dev.md](./progress-mello-team-one-dev.md) | Branch: `mello-team-one-*`
- **Verda:** [progress-verda-team-one-dev.md](./progress-verda-team-one-dev.md) | Branch: `verda-team-one-*`
- **Admin Panel:** [progress-admin-panel-team-dev.md](./progress-admin-panel-team-dev.md) | Branch: `admin-panel-team-*`
- **Testing Scripts:** [progress-testing-scripts-team-dev.md](./progress-testing-scripts-team-dev.md) | Branch: `testing-scripts-team-*`

---

## 2026-02-11

- [RALPH] 467b4d7 fix: reference .env for QA test user credentials instead of hardcoding (comfyume-v1 #1, PR #21)
- [RALPH] e258c8c feat: create Mello Ralph Team — autonomous engineering agent team identity (comfyume-v1 #1, PR #20)
- [MELLO-ONE-TEAM] bd358f3 fix: fix loop — context management, 50 iterations, auto-resume, stuck handler (comfyume-v1 #1, PR #18)
- [MELLO-ONE-TEAM] 53f51ad feat: add ComfyUI fix loop skill for autonomous workflow testing (comfyume-v1 #1, PR #17)
- [MELLO-ONE-TEAM] 9006781 docs: add extension separation and deploy flow rules to CLAUDE.md (comfyume-v1 #12, #13, PR #16)
- [MELLO-ONE-TEAM] 2e172ba refactor: factor out extensions to comfyume-extensions/, add deploy script (comfyume-v1 #12, #13, PR #15)
- [MELLO-ONE-TEAM] b883467 fix: GPU progress banner in redirect.js, sync deployment drift (comfyume-v1 #1, #13, PR #14)
- [MELLO-ONE-TEAM] (no commit) feat: redirect.js status banner — floating GPU progress indicator, deployed to 20 user dirs (comfyume-v1 #1)
- [MELLO-ONE-TEAM] (no commit) fix: added serverless response key logging to QM main.py, SCP'd + restarted (comfyume-v1 #1)
- [MELLO-ONE-TEAM] (no commit) fix: disabled default_workflow_loader on 20 user dirs (renamed .disabled) — canvas null errors (comfyume-v1 #1)
- [MELLO-ONE-TEAM] (no commit) fix: deployed canvas-wait loader.js to 20 user dirs (comfyume-v1 #1)
- [MELLO-ONE-TEAM] (no commit) ops: rebuilt frontend + nginx images, recreated all containers with fixes (comfyume-v1 #1)
- [MELLO-ONE-TEAM] (no commit) fix: copied queue_redirect + default_workflow_loader to all 20 user dirs (comfyume-v1 #1, #8)
- [MELLO-ONE-TEAM] (no commit) ops: SSL cert via certbot, .htpasswd restored, nginx container recreated (comfyume-v1 #1)
- [MELLO-ONE-TEAM] cae94ab docs: production live! nginx fixed, SSL cert, end-to-end working (comfyume-v1 #1)
- [MELLO-ONE-TEAM] 93bf1a1 fix: dynamic DNS resolution in nginx, fix http2 deprecation (comfyume-v1 #1)
- [MELLO-ONE-TEAM] 8b21b75 docs: session handover — core stack healthy, nginx/SSL remaining (comfyume-v1 #1)
- [MELLO-ONE-TEAM] 5ecbaa4 fix: remove unused redis.conf volume mount (comfyume-v1 #1, #7)
- [MELLO-ONE-TEAM] f38f260 docs: update progress — worker gpu profile fix, branch rename (comfyume-v1 #1, #2, #5)
- [MELLO-ONE-TEAM] 749def7 fix: add gpu profile to worker-1, only starts on GPU instances (comfyume-v1 #1, #5)
- [MELLO-ONE-TEAM] 445577a fix: remove leftover worker container before starting app stack [private scripts repo] (comfyume-v1 #1)
- [MELLO-ONE-TEAM] c2e75d5 fix: skip worker build on CPU instance [private scripts repo] (comfyume-v1 #1, #5)
- [MELLO-ONE-TEAM] a9f5693 fix: use REDIS_HOST directly in docker-compose, remove APP_SERVER_REDIS_HOST indirection (comfyume-v1 #1, #5)
- [MELLO-ONE-TEAM] 0da9a62 fix: single frontend build, Tailscale auth key, stop building 20 identical images [private scripts repo] (comfyume-v1 #1, #5)
- [MELLO-ONE-TEAM] 74f04d0 fix: add tailscale up, fix Redis sed for new variable names, set instance ID [private scripts repo] (comfyume-v1 #1, #2)
- [MELLO-ONE-TEAM] 0d587fa docs: update progress — restore script running on quiet-city, DNS updated (comfyume-v1 #1, #2, #3)
- [MELLO-ONE-TEAM] c405f9a docs: update progress with session 40 discoveries and restore plan (comfyume-v1 #1, #2, #3)
- [MELLO-ONE-TEAM] 2c42279 feat: import working app code from comfyume repo, Mello frozen state (comfyume-v1 #1)
- [MELLO-ONE-TEAM] 6d619c3 feat: add comfyume-v1 restore script v0.5.0 + setup-monitoring.sh + safety flags [private scripts repo]

## 2026-02-10

- [MELLO-ONE-TEAM] d920010 feat: initial commit — project docs, Claude skills, agent config (comfyume-v1 #1)
- [ADMIN] bb1de2a refactor: split CLAUDE.md into progressive disclosure modules (#124)
- [ADMIN] -- refactor: migrate .claude/commands/ to .claude/skills/ format, remove archive/build_reports, rename mello-team to mello-team-one

## 2026-02-09

- [TEST] 9583dc5 fix: replace favicon with official ComfyUI logo (#111)
- [TEST] b40ef37 docs: update progress for file sharing and favicon (#111)
- [ADMIN] -- feat: SSL certs for 5 subdomains via Mello nginx reverse proxy (#109)
- [ADMIN] -- fix: Promtail docker group, Loki labels, Verda SDK methods, skill files (#106)
- [ADMIN] -- docs: verda-skills-guide.md - user-friendly guide to 12 monitoring skills (#106)
- [ADMIN] 6b70dbe feat: install monitoring stack on Verda + 12 custom skills (#106)
- [ADMIN] 6e96601 fix: remove non-working favicon from nginx (#101)
- [TEST] fb51baf feat: add inline SVG favicon to admin and user frontends
- [TEST] -- feat: bidirectional file sharing on mello with cookie auth (#111)
- [TEST] -- feat: upload.aiworkshop.art subdomain for file exchange (#111)
- [TEST] -- feat: paste (Cmd+V) support on upload page (#111)
- [ADMIN] -- fix: redirect.js import, endpoint, field name, priority, graphToPrompt() (#101)
- [ADMIN] -- fix: nginx auth_basic off on /api/, removed trailing slash, 600s timeouts, favicon (#101)
- [ADMIN] -- fix: queue-manager debug logging for serverless response body (#101)
- [ADMIN] -- deployed all inference fixes to Verda (nginx, redirect.js, loader.js to 20 users)
- [ADMIN] -- discovery: serverless container still accesses REAL SFS; block storage renamed to /mnt/models-block-storage (#103)
- [ADMIN] -- created #101 (yaml key mapping), #102 (General Storage), #103 (SFS architecture decision)

## 2026-02-08

- [ADMIN] 9132eaf feat: add delete button for orphaned models (#88)
- [ADMIN] 4341cc6 fix: always show Check Models button after scan (#88)
- [ADMIN] 9f0aa61 feat: add orphaned model detection to check downloads page (#88)
- [ADMIN] e924010 fix: resolve HF_TOKEN ReferenceError in check downloads UI (#93)
- [ADMIN] -- deployed download engine (#93) to Verda, fixed SSL certs, downloaded last missing model
- [ADMIN] -- disk cleanup: removed 3 legacy models (~34GB), 85%→68% usage
- [ADMIN] -- fix: copied queue_redirect to all 20 user custom_nodes dirs, restarted containers
- [TEST] 3fa1c0e feat: add model download engine to admin panel (#93, #88)
- [ADMIN] f9526fb docs: add workflow template reference with model inventory and camera LoRAs (#88)
- [ADMIN] -- downloaded 21 models (172GB) to /mnt/sfs: 3 Flux Klein, 7 camera LoRAs, LTX-2 distilled, Flux 4B
- [ADMIN] -- fix: replace symlink storage with direct .env paths, restore script v0.4.2 (private scripts 2a3d444)
- [ADMIN] -- recreated all 22 containers with correct /mnt/sfs/models mount, Templates tab verified working
- [ADMIN] 296d69e feat: add Templates & Models management tab to admin panel (#88)
- [ADMIN] -- deployed #88 to Verda, built admin container, nginx reload, initial testing looks great
- [ADMIN] -- fix: REDIS_BIND_IP + INFERENCE_SERVER_REDIS_HOST → Verda Tailscale IP (private scripts 8259d60)
- [MELLO-ONE-TEAM] 9b66c7c feat: add Portainer edge agent startup to restore script v0.4.1 [private scripts repo]
- [TEST] 6721430 docs: update CLAUDE.md with Mello staging role and aiworkshop.art links (#71)
- [TEST] 07032a2 feat: add Mello container cleanup script (#71)
- [ADMIN] PENDING feat: add Templates & Models management tab to admin panel (#88)
- [MELLO-ONE-TEAM] (no comfyume commit) fix: R2 creds, backup cron, wiki pages, model storage plan (#87, #88)
- [MELLO-ONE-TEAM] 8261a19 fix: backup-cron --backup-to-scratch flag (#87)
- [MELLO-ONE-TEAM] e0b4a72 fix: persist AWS/R2 credentials in restore script
- [ADMIN] 3ac3f56 docs: move user prefs to bottom of CLAUDE.md, add branch rule (#22)
- [ADMIN] cd89b53 docs: update progress files - sync with main, close issues (#65, #66, #67)
- [ADMIN] -- debugged admin auth on Verda (URL-encoded password), generated corrected user magic links
- [ADMIN] -- restore-verda-instance.sh: Termius keys, root→dev key copy, full .env sync, MELLO_PUBLIC_IP (PR #32)
- [ADMIN] -- copied commands to claude-settings/all-teams/commands/ in private scripts repo
- [ADMIN] -- merged 34 commits from main, resolved merge conflict in resume file
- [MELLO-ONE-TEAM] bb838ce feat: add /update-progress command for team-aware progress updates (#22) - PR #81
- [MELLO-ONE-TEAM] 367c36f feat: add /pull-main command to merge latest main into current branch - PR #82

## 2026-02-07

- [MELLO-ONE-TEAM] a9c3c42 fix: admin routing, QM event loop block, health check IPv6 (#64)
- [TEST] 5dbfad0 docs: update README with serverless architecture (#22)
- [TEST] e5ee2a5 docs: update worker README with serverless note (#22)
- [TEST] 849ef58 docs: update .env.example to v0.3.5 with serverless config (#22)
- [TEST] c21cdc3 chore: archive obsolete GPU deployment scripts (#22)
- [MELLO-ONE-TEAM] a9d7cd2 fix: admin routing, QM event loop block, health check IPv6 (#64)
- [MELLO-ONE-TEAM] bc647b2 fix: nginx auth, CORS domain, user-maps include for Verda restore (#64)
- [MELLO-ONE-TEAM] 367c36f feat: add /pull-main command (#22) - PR #82
- [MELLO-ONE-TEAM] bb838ce feat: add /update-progress command (#22) - PR #81
- [MELLO-ONE-TEAM] 5b0c8ec docs: session 36 progress - resume/handover cleanup, smart hooks (#22, #8) - PR #80
- [ADMIN] -- closed GH issues #65, #66, #67 with implementation comments referencing PR #69

- [MELLO-ONE-TEAM] 7664d83 docs: add gh CLI Projects Classic workaround to CLAUDE.md (#22) - PR #79
- [MELLO-ONE-TEAM] 5ba904e chore: slim down all resume files, fix testing-scripts paths (#22) - PR #78
- [MELLO-ONE-TEAM] 66a6fe0 chore: fix file paths in resume/handover files, archive ARCHITECTURE-ASCII (#22) - PR #76
- [MELLO-ONE-TEAM] 9e7ff1f feat: daily R2 upload with rotation, max 10 copies [private scripts repo]
- [TEST] -- PR #75 created, issue #6 updated and closed
- [TEST] 421e989 docs: update testing-scripts-team progress (#6)
- [TEST] 0731e29 fix: update docker-compose references across scripts (#6)
- [TEST] 16d2767 docs: add comprehensive admin testing guide (#6)
- [TEST] c166901 test: add connectivity test (#6)
- [TEST] 61f202c test: add serverless inference e2e test (#6)
- [TEST] ddda4e0 test: rewrite integration test suite for serverless architecture (#6)
- [TEST] bd49f8c test: add shared test helper library (#6)
- [TEST] f7a9574 docs: add testing-scripts-team onboarding files
- [MELLO-ONE-TEAM] 4212e0f docs: archive stale .claude files (#22) - PR #73
- [MELLO-ONE-TEAM] dcd0e96 docs: update all references setup-verda-solo-script → restore-verda-instance (#64, #71) - PR #72
- [MELLO-ONE-TEAM] 28eda1c docs: update refs for restore-verda-instance.sh v0.4.0 (#64, #71) - PR #72
- [MELLO-ONE-TEAM] ea6549b feat: add restore-verda-instance.sh v0.4.0 for production app server (#64, #71) [private scripts repo]
- [MELLO-ONE-TEAM] 38a28da docs: session 34 - Verda instance setup, central progress log in CLAUDE.md (#64, #71)
- [MELLO-ONE-TEAM] 05eb063 feat: add production nginx configs from old Verda instance (#64) [private scripts repo]
- [MELLO-ONE-TEAM] -- backed up old OS drive to scratch: nginx, SSL, .env, tarballs, worker image
- [MELLO-ONE-TEAM] -- SFS mount BLOCKED: CPU instance has no private network to reach NFS (10.1.78.10)
- [MELLO-ONE-TEAM] -- created #71 (Mello VPS downgrade), updated #64 with full backup/restore tasks

## 2026-02-06

- [ADMIN] bbffd11 docs: add all-teams ultra-concise commit log, link from all handover/resume files
- [ADMIN] e8787bf feat: admin dashboard v2 - system status, GPU switching, storage mgmt (#65, #66, #67)
- [ADMIN] -- team initialized: progress file, handover, resume context, onboarding
- [ADMIN] -- PR #69: https://github.com/ahelme/comfyume/pull/69
- [MELLO-ONE-TEAM] f134ff5 docs: session 33 - Verda CPU instance provisioned, handover update
- [MELLO-ONE-TEAM] d0fd975 docs: CRITICAL - aiworkshop.art PRODUCTION is on Verda, not Mello
- [MELLO-ONE-TEAM] -- provisioned Verda CPU instance soft-wolf-shines-fin-01 (CPU.8V.32G, €34/mth) (#64)
- [MELLO-ONE-TEAM] -- restructured nginx configs: staging vs production in private scripts repo

## 2026-02-05

- [MELLO-ONE-TEAM] 060e0c4 fix: resolve workflow save/load 405 error (#54)
- [MELLO-ONE-TEAM] -- root cause: nginx proxy_pass trailing slash decodes %2F in userdata API
- [MELLO-ONE-TEAM] -- created comfyui-userdata-maps.conf, updated 20 user proxy_pass lines

## 2026-02-04

- [MELLO-ONE-TEAM] 4706846 docs: session handover - all 4 serverless deployments complete
- [MELLO-ONE-TEAM] 02e8043 docs: add Verda console deployment steps for serverless
- [MELLO-ONE-TEAM] 00f6571 docs: update progress log - phase 11 serverless complete
- [MELLO-ONE-TEAM] 9475024 feat: add serverless API key authentication support (#62)
- [MELLO-ONE-TEAM] -- created 4 DataCrunch deployments: H200/B300 x spot/on-demand
- [MELLO-ONE-TEAM] -- terraform configs + GitHub Actions workflow for mobile GPU switching
- [VERDA] 9475024 feat: serverless inference WORKING on Verda (#62)
- [VERDA] -- fixed: API key auth, python→python3 CMD, SERVERLESS_API_KEY config

## 2026-02-03

- [MELLO-ONE-TEAM] -- #62 serverless multi-GPU implementation: config.py, switch-gpu.sh, h200.env, b300.env

## 2026-02-02

- [MELLO-ONE-TEAM] -- fix: add ComfyUI favicon and frontend assets for presentation (247 files)
- [MELLO-ONE-TEAM] -- #54 workaround: disabled broken custom nodes for boss meeting
- [MELLO-ONE-TEAM] -- #40 backup: worker container built, config backup to SFS, silent failures discovered
- [VERDA] -- #40 downloaded 7 models (77GB) + gemma (8.8GB), R2 upload 98GB total
- [VERDA] -- fixed R2 endpoint: .r2. → .eu.r2.

## 2026-02-01

- [MELLO-ONE-TEAM] ea844ee test: complete infrastructure test for #39 (4/5 passing, 20 containers)
- [MELLO-ONE-TEAM] 17cea21 feat: add multi-user load testing framework (#19)
- [MELLO-ONE-TEAM] 67afebe feat: validate 5 workflow templates for v0.11.0 (#17) - 49% JSON reduction
- [MELLO-ONE-TEAM] -- #21 COMFYUI_MODE implementation, .env v0.3.2
- [MELLO-ONE-TEAM] -- PR #37, PR #31 merged to main
- [VERDA] -- .env v0.3.2 migration across both repos (#22, #14)
- [VERDA] -- CLAUDE.md cleanup, R2 buckets update (3→7), file organization
- [VERDA] -- PR #32 merged to main
