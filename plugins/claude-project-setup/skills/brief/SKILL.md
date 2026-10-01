---
name: brief
description: Start here when the user describes a project they want to build ("I want to build…", "create an app that…", "new project for…") or asks to set up, adopt or onboard an existing repo for Claude Code. Drafts PROJECT-BRIEF.md from their description (new or existing project), lets them review it, then hands off to bootstrap.
argument-hint: "[optional: project description]"
---

# Brief: description → PROJECT-BRIEF.md → bootstrap

## 1. Understand the starting point
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scan_repo.py" . > "${TMPDIR:-/tmp}/cps-scan.json"
```
- `mode: greenfield` means a new project; use the user's description for everything.
- `mode: brownfield` means an existing repo. Prefill **Stack preferences** with `keep current (<frameworks from scan>)`; the description adds goals and requirements.
- Prefill **Project type** with the scan's `project_type` (`plugin`, `skill`, `agents`, `app` or `library`) unless it's `unknown`, or the user said otherwise.
- If `PROJECT-BRIEF.md` already exists, don't overwrite it. Show which sections are empty, then go to step 4.

## 2. Draft from the conversation (no invention)
Start from `${CLAUDE_PLUGIN_ROOT}/templates/PROJECT-BRIEF.md` and fill **only** what the user actually said (in `$ARGUMENTS` or the chat):
- **Goal:** their words, condensed to one paragraph.
- **Requirements:** one numbered line per goal. Split compound sentences, and keep the user's wording.
- **Risk areas:** list only what they mentioned (auth, payments, PII, uploads, migrations…).
- Every section they didn't cover stays empty or says `recommend`. Those become bootstrap interview questions. **Never guess.**

## 3. Consent, then write
- Ask with AskUserQuestion: "Create `PROJECT-BRIEF.md` and a setup tracker in `.claude/state-machine/`?" Options: **Yes (Recommended)** / Different name / Show draft only.
- Write the file only after a yes. Then start the setup machine, so the setup can resume after an interruption:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/templates/state-machine/state_cli.py" new bootstrap
  python3 "${CLAUDE_PLUGIN_ROOT}/templates/state-machine/state_cli.py" move bootstrap brief_written
  ```
- Show a five-line summary: goal, the number of requirements, the sections left for the interview, and the mode.

## 4. Review, then hand off
- Tell the user they can edit `PROJECT-BRIEF.md` in their editor now, or just answer "go".
- When they confirm, **invoke the `claude-project-setup:bootstrap` skill** with the brief path. Don't repeat the scan; bootstrap reads `${TMPDIR:-/tmp}/cps-scan.json` if it's present.
