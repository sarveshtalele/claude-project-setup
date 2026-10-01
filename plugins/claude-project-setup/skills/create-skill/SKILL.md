---
name: create-skill
description: Create a new Agent Skill (SKILL.md + scripts + evals) whose steps are tracked by a state machine, so they can't run out of order or skip a review. Use when the user asks to create, build or design a skill, slash command or repeatable workflow (e.g. "a skill that drafts release notes").
argument-hint: "[what the skill should do]"
---

# Create a skill

The generator is deterministic: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py"` (use `python` on Windows). It never overwrites files, and exit 2 means the spec is invalid; nothing is written in either case.

## 1. Understand it (at most 4 AskUserQuestion questions; skip anything already said)
- **Outcome:** what the skill produces, and one example request that should trigger it.
- **Steps:** the ordered steps, as short verbs (collect → draft → review → write).
- **Review gates:** which steps need the user's approval before continuing.
- **Where:** a project skill (`.claude/skills/<name>`, the default), a standalone folder, or part of a plugin (use `create-plugin` instead).

## 2. Write the spec (in `${TMPDIR:-/tmp}/skill-spec.json`, not the project)
```json
{"kind": "skill", "name": "release-notes", "title": "Release notes",
 "description": "<What it does>. Use when <trigger phrases>.",
 "summary": "<one paragraph>", "path": ".claude/skills/release-notes", "tracker": "auto",
 "steps": [{"id": "collect", "title": "Collect commits", "do": "<exact instructions>"},
           {"id": "review", "title": "User review", "gate": true}]}
```
- **name:** lowercase-hyphenated, ≤ 64 chars, unique.
- **description:** 40–1024 chars, must include "Use when…", and must not overlap an existing skill's triggers.
- **steps:** `id` is snake_case and `do` is concrete, ideally a command. Rules that must always hold belong in a script, not in prose.
- **tracker:** `auto` turns the state machine on for 3 or more steps or any gate.

## 3. Preview, consent, write
1. `scaffold.py --spec "${TMPDIR:-/tmp}/skill-spec.json" --target . --dry-run`, then show the file list and the step diagram (a Mermaid `stateDiagram-v2`: one line per transition, with the gates marked).
2. Ask: "Create these files?" Run it without `--dry-run` only after a yes.
3. Run its evals: `python3 <path>/evals/run_evals.py`. They must all pass. They check the structure, the step order, the gates and a full run to `DONE`.

## 4. Hand over
- Tell the user how to trigger it (`/<name>`, or a phrase from the description), and that a run's progress is in `.claude/state-machine/.state-machine/skill-<name>/`.
- Suggest adding real input/output cases to `evals/evals.json` (format at the top of `run_evals.py`).
