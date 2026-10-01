# TASK-NNN: <title>

**Status:** planned | approved (<date>, by <who>) | done
**Why:** <one or two lines: the problem, with evidence path:line or issue link>

## Goal
<One sentence describing the observable outcome.>

## Non-goals
- <what this task explicitly won't touch>

## Allowed files
- `src/<path>`
- `tests/<path>`
<!-- The implementer may edit ONLY these. New files must be listed here by exact name. -->

## Dependency changes
none | `<pm> add <pkg>@<version>` (reason)

## Acceptance (runnable, all must pass)
```bash
<test command for the new behaviour>
<full suite / typecheck>
```
- [ ] <manual check, only if it can't be automated>

## Rollback
`git revert <commit>` (and `<pm> install` if dependencies changed)
