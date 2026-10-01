---
name: create-plugin
description: Create a Claude Code plugin or skill bundle (marketplace + plugin.json + skills with state machines + optimised agents + README), validated with `claude plugin validate`. Use when the user asks to build a plugin, a skill bundle, a marketplace, or to package skills/agents for sharing.
argument-hint: "[what the plugin is for]"
---

# Create a plugin

The generator is `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py"` (use `python` on Windows). It's deterministic, never overwrites files, and writes nothing on error.

## 1. Understand it (at most 4 AskUserQuestion questions)
- **Purpose:** one line, plus the author name.
- **Skills:** for each one, its name, outcome, steps and review gates (the same questions as `create-skill`, kept short).
- **Agents:** for each one, its job and tier: **scout** (haiku, read-only), **builder** (sonnet, edits) or **judge** (inherit, read-only). Leave them out if the skills don't need delegation.
- **Layout:** a marketplace repo (`plugins/<name>/`, the default, installable with `claude plugin marketplace add`) or a bare plugin folder.

## 2. Write the spec (in `${TMPDIR:-/tmp}/plugin-spec.json`)
```json
{"kind": "plugin", "name": "release-kit", "author": "Name", "marketplace": true,
 "description": "<what the plugin does>",
 "skills": [{"name": "release-notes", "description": "… Use when …", "steps": [ … ]}],
 "agents": [{"name": "release-judge", "tier": "judge", "description": "… Use when …",
             "mission": "<one line + boundary>", "output": "<fixed reply format>"}]}
```
- Skills follow the same rules as `create-skill`.
- Every tracked skill uses **one shared** tracker at the plugin root, so there's nothing to keep in sync.
- Agents get the balanced-profile model for their tier, the fewest tools, a turn cap and the `UNCERTAIN` rule.

## 3. Preview, consent, write
1. Run `--dry-run` and show the file tree, the skills table and the agents table.
2. Ask: "Create these files?" Write them only after a yes.

## 4. Prove it
```bash
claude plugin validate .
claude plugin validate plugins/<name>
python3 plugins/<name>/skills/<skill>/evals/run_evals.py
```
Both validations must pass, and every skill's evals must pass. If `claude` isn't on PATH, say so and stop; don't claim the plugin is valid without running the validator.

## 5. Hand over
- Show the install commands from the generated `README.md`, and how to try it locally: `claude --plugin-dir ./plugins/<name>`.
- Docs go in the repo's `docs/`, outside the plugin folder, so they aren't installed with it.
