# Project state

<!-- Keep under 60 lines. Injected into every session at start and after compaction.
     Overwrite stale lines; don't append history (that's git log + CHANGELOG). -->

**Goal:** {{STATE_GOAL}}
**Updated:** {{STATE_DATE}} by claude-project-setup

## Current task
- none
- Next step: {{STATE_NEXT}}

## Architecture (now)
- See `docs/ARCHITECTURE.md` and `docs/adr/`.

## Done (recent, max 5)
- Claude setup (level: {{GUARDRAIL_LEVEL}}): verified by `python3 .claude/hooks/selftest.py`

## Open questions / blocked on user
- none

## Known gaps (not yet tasks)
{{STATE_GAPS}}
