# CLAUDE RESUME - COMFYUME (VERDA TEAM ONE)

**DATE**: 2026-02-22

---

## CONTEXT

**We are Verda Team One.** We work on the Verda instance directly.

**Production:** aiworkshop.art runs on Verda (NOT Mello).
**Testing:** anegg.app on testing-009 (65.108.33.80). Shared by all teams.

---

## TESTING-009 DEPLOYMENT (CRITICAL)

**testing-009 runs the `testing-009` branch ONLY.**
- NEVER `git checkout <team-branch>` on the server — wipes other team's code
- Merge your team branch into `testing-009`, then `git pull` on the server
- See CLAUDE.md "Deploying to Testing-009" for full workflow

---

## CONTEXT LOADING

Please read:

1. **`./CLAUDE.md`** - Project instructions (Verda = PRODUCTION)
2. **`.claude/agent_docs/progress-verda-team-one-dev.md`** (top ~250 lines) - Current tasks + recent progress
3. **`.claude/agent_docs/progress-all-teams.md`** - All-teams commit log
4. **`git status && git log --oneline -10`** - Pending work

---

## KEY FILES

| File | Purpose |
|------|---------|
| `./CLAUDE.md` | Project guide, architecture, gotchas |
| `.claude/agent_docs/progress-verda-team-one-dev.md` | Tasks + session progress |
| `.claude/agent_docs/progress-all-teams.md` | All-teams commit log |

---

## TEAM COORDINATION

**GitHub Issues:** https://github.com/ahelme/comfyume/issues
**Private Scripts:** https://github.com/ahelme/comfymulti-scripts

---

## SESSION START CHECKLIST

- [ ] Check today's date
- [ ] `git status` on both repos
- [ ] Read `.claude/agent_docs/progress-verda-team-one-dev.md` top section
- [ ] Discuss priorities with user
