# Agent design reference

## Model per tier and profile
Add these settings to `profiles.<profile>.<name>` in `.claude/agent-models.json`:

| Tier | economy | balanced | quality |
|---|---|---|---|
| scout | `haiku`, effort `null`, maxTurns 20, omitClaudeMd `true` | `haiku`, `null`, 25, `true` | `sonnet`, `low`, 30, `true` |
| builder | `sonnet`, `low`, 40, `false` | `sonnet`, `medium`, 50, `false` | `inherit`, `high`, 70, `false` |
| judge | `sonnet`, `medium`, 15, `false` | `inherit`, `high`, 20, `false` | `inherit`, `high`, 25, `false` |

Why:
- **Scouts** do mechanical work (search, run, compare), so the cheapest model is enough.
- **Builders** need reliability, so they use sonnet.
- **Judges** catch subtle problems, so they inherit your session model.
- `omitClaudeMd: true` only for scouts, which don't need project conventions.
- `effort: null` on haiku, because its effort levels may be limited.

## Tool sets (least privilege)
- **scout:** `Read, Grep, Glob`. Add `Bash` only if it must run commands; read-only Bash means ls, git log/diff and test runners.
- **builder:** `Read, Grep, Glob, Edit, Write, Bash`.
- **judge:** `Read, Grep, Glob, Bash`, with no Edit or Write.
- MCP tools: list `mcp__<server>` only when the job needs that server.
- Never give `Agent` to a scout. Nested agents multiply cost.

## Skeleton
```markdown
---
name: <name>
description: <What it does in one sentence>. Use when <trigger phrases / situations>.
tools: <tier tools>
model: <from policy>
maxTurns: <from policy>
---

You <one-line mission>. You <never do X> (the boundary).

1. <step>
2. <step>
3. <verification step that uses real command output>

Rules:
- Stay inside <scope>. If more is needed, stop and report it.
- If a hook blocks you, report it. Never work around it.
- Never claim success without quoting the output that shows it.

Return (at most <15|20|30> lines):
` ` `
<FIXED FORMAT, e.g. VERDICT / FINDINGS / CHANGED / EVIDENCE path:line>
` ` `

If you can't do this reliably (missing facts, ambiguous spec, repeated failure), add a final line `UNCERTAIN: <why>`. The main session may re-run you once on a stronger model.
```
(Replace `` ` ` ` `` with three backticks.)

## Checklist before writing
- [ ] Name is kebab-case and unique.
- [ ] The description doesn't overlap any existing agent's.
- [ ] Tools are the tier's minimum.
- [ ] The output format is fixed and short.
- [ ] The UNCERTAIN line is present.
- [ ] A policy entry is in all 3 profiles.
