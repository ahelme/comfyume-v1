**Project:** ComfyuME Multi-User ComfyUI Workshop Platform | **Repo:** github.com/ahelme/comfyume-v1
**Doc Updated:** 2026-02-22

# All-Teams Progress (Ultra-Concise Commit Log)

## How to Update
**EVERY COMMIT** add one line: `- [TEAM] [HASH] [type]: [description] (#issue)`
Newest at top. One line per commit. No fluff. Link issues.

## Team Progress Files (FULL DETAIL)
- **Mello:** [progress-mello-team-one-dev.md](./progress-mello-team-one-dev.md) | Branch: `testing-mello-team-one*`
- **Verda:** [progress-verda-team-one-dev.md](./progress-verda-team-one-dev.md) | Branch: `verda-team-one-*`
- **Admin Panel:** [progress-mello-admin-panel-team-dev.md](./progress-mello-admin-panel-team-dev.md) | Branch: `mello-admin-panel-team-*`
- **Scripts:** [progress-mello-scripts-team-dev.md](./progress-mello-scripts-team-dev.md) | Branch: `mello-scripts-team-*`

---

## 2026-02-22

- [MELLO-ONE-TEAM] 4e10bd3 feat: gpu_overlay admin/user modes + comfyume_progress events (#44, #73)
- [MELLO-ONE-TEAM] 2b5cc87 refactor: extract status_banner as reusable extension (#73, #44)
- [MELLO-ONE-TEAM] abc8e2d feat: gpu_overlay extension — modular progress banner (#73, #44)
- [MELLO-ONE-TEAM] 86fadcd fix: early bail on LB routing miss + better error messages (#73)
- [MELLO-ONE-TEAM] 0770cb5 fix: serverless_proxy error handling — prevent frontend dialog crash (#73)
- [MELLO-ONE-TEAM] GH #73 created: serverless_proxy malformed execution_error
- [MELLO-ONE-TEAM] GH #74 created: inference broken on testing-009 after IaC deployment
- [ADMIN] 4ab61c6 fix: restore correct per-user credentials on testing-009
- [ADMIN] 5a4cc05 fix: address mello-team-one review — permissions, CORS, verbose (#71)
- [ADMIN] 0c10d41 feat: add environment variable for isolated serverless deployments (#71)
- [ADMIN] 6588f93 fix: add OpenTofu state files to .gitignore + production safety docs (#71, #54)
- [ADMIN] (testing-009) tofu apply: comfyume-test-vca-ftv-h200-spot created, CLONE_SFS (#72)
- [ADMIN] (testing-009) QM switched to testing endpoint, htpasswd restored to strong passwords
- [ADMIN] GH #71 created: SFS volume mismatch diagnosis + environment isolation
- [ADMIN] GH #72 created: apply environment-isolated serverless on testing-009

## 2026-02-17

- [ADMIN] 2a81358 docs: update learnings from testing instance 009 — E2E inference confirmed (#70)
- [ADMIN] eab1a1b fix: add --output-directory to all serverless deployments + CORS for anegg.app (#70, #54)
- [ADMIN] (scripts) restore-verda-instance-comfyume-v1-testing.sh created for instance 009
- [ADMIN] 6dd9fe5 docs: add anegg.app testing domain to infrastructure (#68)
- [ADMIN] (scripts) a36088c docs: add anegg.app domain for testing instance 009
- [MELLO-ONE-TEAM] (scripts) feat: per-env SSH identities — all host keys renamed verda_production_*, 3 ed25519 pairs (#55)
- [MELLO-ONE-TEAM] (scripts) refactor: backup-mello.sh → backup-user-data.sh, runs locally on Verda (#48)
- [MELLO-ONE-TEAM] (scripts) fix: backup-cron.sh v3.2 — local user data backup, double-logging fix (#48)
- [MELLO-ONE-TEAM] (scripts) b9c204a feat: disk-check --require, backup reports, remove set -e (#48) — PR #53
- [MELLO-ONE-TEAM] (scripts) SSH key cleanup: removed Claude-generated verda@gpu-worker + dev@verda->mello keys
- [MELLO-ONE-TEAM] (scripts) Fixed backup cron (was silently crashing since Feb 16), crontab stderr redirect
- [MELLO-ONE-TEAM] (scripts) Verda→Mello SSH working — host ed25519 key deployed, logged in #45
- [MELLO-ONE-TEAM] CLAUDE.md rule #7: never generate SSH keys without user approval
- [ADMIN] (no commit) fix: regenerated nginx/.htpasswd from .env credentials using Python bcrypt (#61, closed)
- [ADMIN] (no commit) created GH #61: nginx 500 — .htpasswd lost during git operations
- [ADMIN] (no commit) updated GH #58 title: removed subdomain references (path-based approach kept)
- [ADMIN] d153c17 fix: SSL docs correction, certbot webroot renewal, CORS cleanup (#58) — PR #59 merged
- [ADMIN] (verda) fix: captured Ralph Loop local changes from production server — PR #60 merged
- [ADMIN] (verda) synced .env to Verda: found 10 inconsistencies (R2 double .eu.eu, wrong REDIS_BIND_IP)
- [ADMIN] (verda) fixed certbot: standalone→webroot, added /var/www/certbot volume mount
- [ADMIN] (verda) recreated all 24 containers — all healthy
- [ADMIN] (scripts) updated .env: DOMAIN, SSL paths, USE_HOST_NGINX=false, SERVER_MODE=serverless

## 2026-02-16

- [MELLO-ONE-TEAM] 9049b2b fix: restore script v0.5.0 — 6 naming mismatches + bugs #41-#45 (scripts PR #52, merged)
- [MELLO-ONE-TEAM] (scripts) GH issue #51 created: copy models to CLONE_SFS
- [MELLO-ONE-TEAM] ca1b1b5 docs: session handover — backup verified, restore gap analysis (#31, #48)
- [MELLO-ONE-TEAM] Merge PR #52 into main (backup verified, restore gap analysis)
- [MELLO-ONE-TEAM] git pull main → both repos synced
- [SCRIPTS] 005f62e fix: redesign backup log dashboard, separate verify log (#48)
- [SCRIPTS] Merge PR #50 into main (backup log dashboard + verify-and-log)
- [SCRIPTS] git pull main → scripts repo synced
- [ADMIN] fdc69ce docs: add OpenTofu debugging/deployment workflow to CLAUDE.md (#54)
- [ADMIN] e7e7842 feat: import 4 Verda deployments, align .tf with live production (#54) — drift audit complete
- [ADMIN] 8930d46 Merge PR #55 (import + drift alignment + CLAUDE.md)
- [ADMIN] ff558b8 feat: add OpenTofu infrastructure for Verda serverless deployments
- [ADMIN] 54abda4 Merge PR #53 (initial .tf files)
- [ADMIN] created GH #54: IaC — bring Verda serverless under OpenTofu management
- [MELLO-ONE-TEAM] (no commit) redis-7-alpine uploaded to R2 (16.4 MiB, verified)
- [MELLO-ONE-TEAM] (no commit) R2 upload verified: 13 items, 0 failures, all VERIFIED
- [MELLO-ONE-TEAM] (no commit) restore script gap analysis: 6 critical naming mismatches found
- [ADMIN] 0829a6c Merge PR #51 (QM logging, IaC mandate, inference investigation)
- [ADMIN] 694b8ef Merge PR #50 (admin team session handover)
- [ADMIN] 1d0dc1a fix: log serverless execution error details in QM (#48)
- [ADMIN] e844b4f docs: IaC mandate in CLAUDE.md, inference regression investigation
- [MELLO-ONE-TEAM] 09fc66d Merge PR #49 into main (R2 audit, backup scripts, session handover)
- [MELLO-ONE-TEAM] ab5443c merge: incorporate main (admin team entries)
- [MELLO-ONE-TEAM] ffca3db docs: context.md — missing container check, backups-log rule
- [MELLO-ONE-TEAM] 20e35d2 docs: session handover — R2 audit, backup scripts, PR #41 merged (#31, #42)
- [MELLO-ONE-TEAM] 949fbe1 Merge PR #41 into main (CLAUDE.md reorg, backup docs, infra cleanup)
- [MELLO-ONE-TEAM] dde0552 merge: incorporate main (PR #39) into testing-mello-team-one
- [MELLO-ONE-TEAM] 2f34b0f docs: add backup retention policy and backups agent doc (#42)
- [MELLO-ONE-TEAM] 2a0c4ed docs: reorganize CLAUDE.md — deployment checklist, storage naming
- [ADMIN] (no commit) fix: restarted all 20 frontend containers — NFS model visibility restored (#43)
- [ADMIN] (no commit) created GH issues #44 (GPU banner), #45 (cookie auth), #46 (cold start UX)
- [ADMIN] (no commit) diagnosed: redirect.js serverless early-exit, auth re-prompting, cold start timeout chain
- [ADMIN] (no commit) SSH updated: Tailscale 100.89.38.43 as dev (root on public IP broken after reprovision)
- [ADMIN] **REGRESSION**: inference broken for ALL workflows — serverless returns status=error, no deployment drift found
- [ADMIN] (no commit) investigation: no code drift, QM doesn't log serverless error detail (#48)
- [ADMIN] created GH #48: QM poll_serverless_history logging gap
- [ADMIN] 1d0dc1a fix: log serverless execution error details in QM (#48) — deployed to production
- [ADMIN] e844b4f docs: add IaC mandate to CLAUDE.md — Critical Instruction #6: OpenTofu mandatory
- [MELLO-ONE-TEAM] eff863a docs: deployment checklist SFS-first, instance 008, DR clone (#38)
- [MELLO-ONE-TEAM] 92861b9 merge: incorporate main, resolve PR #39 conflicts
- [MELLO-ONE-TEAM] eaf1631 docs: testing instance provisioned, model vault restored (#38)
- [MELLO-ONE-TEAM] 817fc51 docs: testing instance in infrastructure table (#38)
- [MELLO-ONE-TEAM] (scripts) 6658d02 docs: add backups log — verified R2 contents audit (#45)
- [MELLO-ONE-TEAM] (scripts) c71874c fix: backup scripts — retention policy, dated naming (#48)
- [MELLO-ONE-TEAM] (scripts) 2de0a45 fix: bash arithmetic gotcha with set -e (#48)
- [MELLO-ONE-TEAM] (scripts) 01d4e4e fix: backup-cron.sh image naming (#48)
- [MELLO-ONE-TEAM] (scripts) a4244af Merge PR #49 into main (image naming fix)

## 2026-02-15

- [MELLO-ONE-TEAM] 0ca2ef7 docs: session handover — Phase 1.75 complete (#37, #38)
- [MELLO-ONE-TEAM] ff2a10a chore: Verda resource naming convention, SFS clone setup, infra cleanup (#37, #38)
- [MELLO-ONE-TEAM] 876cc8b docs: session handover — Phase 1.5 complete (#29, #31)
- [MELLO-ONE-TEAM] 5ba7039 docs: 3-tier deployment workflow, team renames, Verda rebrand (#29, #31) — 32 files, +372/-181
- [MELLO-ONE-TEAM] 0c762c0 merge: incorporate main (PRs #32-#35) into testing-mello-team-one

## 2026-02-12

- [MELLO-ONE-TEAM] 0f9c503 docs: post-Ralph documentation — changelog, server admin, media flow (comfyume-v1 #29, #30, PR #33)
- [MELLO-ONE-TEAM] e6fd900 fix: log Ralph Loop results — QA passed, image delivery fixed (comfyume-v1 #22, PR #32)
- [RALPH] f79eefc feat: SFS-based image delivery for serverless mode (comfyume-v1 #22, PR #28)
- [RALPH] 48fb876 fix: increase poll timeout to 600s, reduce per-request to 10s (comfyume-v1 #22, PR #27)
- [RALPH] b4116d1 fix: improve serverless polling diagnostics and timeouts (comfyume-v1 #22, PR #26)

## 2026-02-11

- [RALPH] 77c3a6e fix: set history_result in serverless proxy for ComfyUI v0.11.0 (comfyume-v1 #22, PR #25)
- [RALPH] b93fe9f fix: /api/health route alias for nginx proxy path (comfyume-v1 #22, PR #24)
- [RALPH] 74bccc0 feat: image delivery gap fix — serverless proxy + QM image fetching (comfyume-v1 #22, PR #23)
- [RALPH] 97c4f0c refactor: rename comfyui-qa-loop to comfyui-fix-loop (comfyume-v1 #22, PR #21)
- [RALPH] cf0be64 docs: QA iteration 1 — Flux2 Klein 9B tested, image delivery gap confirmed (comfyume-v1 #22, PR #21)
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
