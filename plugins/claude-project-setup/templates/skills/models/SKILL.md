---
name: models
description: Show or change which model, effort and turn limit each subagent uses (.claude/agent-models.json). Use when the user asks which models agents use, wants to save cost, switch to economy/balanced/quality, or pin a model for one agent.
argument-hint: "[show | economy | balanced | quality | <agent>=<model> | apply]"
---

# Agent models

`.claude/agent-models.json` holds the policy. It belongs to the user: they can edit it by hand, and you edit it only when they ask.

| `$ARGUMENTS` | Do |
|---|---|
| *(empty)* or `show` | `python3 .claude/scripts/apply_models.py --list`, then show the table |
| `economy` / `balanced` / `quality` | Set `"profile"` in the policy, then **apply** |
| `<agent>=<model>` (e.g. `implementer=opus`) | Set `overrides.<agent>.model`, then **apply**. Globs are allowed (`*-expert`) |
| `apply` | `python3 .claude/scripts/apply_models.py`, then show what changed |

Rules:
- **Apply** rewrites only `model`, `effort`, `maxTurns`, `omitClaudeMd` (and `tools` / `disallowedTools`, if the policy sets them) in each agent's frontmatter. Prompts and other edits stay as they are.
- Valid models: `haiku`, `sonnet`, `opus`, `fable`, `inherit`, or a `claude-*` model id. Valid effort: `low`, `medium`, `high`, `xhigh`, `max`, or `null` (inherit the session's effort). Keep `effort: null` for haiku, which may not support every level.
- Exit code 2 means the policy is invalid and nothing was written. Show the error and fix the JSON.
- After changing models, tell the user the new settings apply to agents started in this or later sessions.
- Profiles in brief: **economy** puts search, checks and tests on haiku and reviews on sonnet. **balanced** (the default) puts search and checks on haiku, building on sonnet, and reviews on your session model. **quality** uses sonnet or better everywhere.
