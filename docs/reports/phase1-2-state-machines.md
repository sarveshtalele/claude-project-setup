# Report: Phases 1–2 (state machines)

**Date:** 2026-10-01 · **Plan:** [v0.4 roadmap](../roadmap/v0.4-plan.md)

## Phase 1: proving the tracker (mcp-skills-registry, scratch clone)
Tested: the `state-machine-tracker` skill from codebase-migration-factory, wired by hand as a task lifecycle.

| Check | Original | Fixed |
|---|---|---|
| Normal lifecycle, reports | ✅ | ✅ |
| Illegal moves rejected, nothing written | ✅ | ✅ |
| `since_entry` loop guard | ✅ | ✅ |
| Lock held, stale lock, 24 writers at once | ✅ | ✅ |
| Machines isolated; no migration-specific coupling; ~31 ms per command | ✅ | ✅ |
| Snapshot file missing | ❌ traceback | ✅ |
| **Crash between event and snapshot** | ❌ **duplicate transition accepted**, sequence `[1,2,3,4,4]` | ✅ rejected; sequence numbers unique |
| Half-written last line in `events.jsonl` | ❌ every command crashes | ✅ ignored, with a note |
| **Machine id `../../../escaped`** | ❌ **wrote outside its folder** | ✅ refused |
| Score | 17/23 | **23/23** |

The fixes:
- **Event log as the source of truth:** every command replays `events.jsonl` instead of trusting the snapshot.
- **Torn lines tolerated:** an incomplete final line is skipped.
- **Ids validated:** machine ids are checked before use.

They are covered by 4 regression evals. Those evals fail on the original scripts (19/23) and pass on the fixed ones (23/23).

## Phase 2: in the plugin (tokentelemetry, strict, scratch clone)
| Step | Result |
|---|---|
| Brief consent creates the bootstrap machine | `BRIEFED` |
| Session break | Start hook reports "interrupted at BRIEFED…" |
| `render.py` before approval | **Exit 3, REFUSED**, nothing written |
| Claude records `user_approved` itself | **Exit 6, refused** |
| User: "looks good but use strict" | Not treated as approval |
| User: "approved" | Recorded → `APPROVED` → render → `GENERATED` |
| Self-test / doctor | 28 guard cases OK · 0 FAIL / 0 WARN → `VERIFIED` |
| Start hook after setup | Silent |
| Task: `start` before approval | Exit 3 |
| Shell command containing `user_approved` | Guard **deny** |
| User: "approve TASK-001" | Recorded → `APPROVED` → `IN_PROGRESS` |
| Scope (strict) | Allowed file → allow · `backend/app/main.py` → deny · `App.tsx` → deny |
| `pass` without the verifier | Exit 4 |
| Real acceptance (`tsc --noEmit`) → verifier `verify_passed` → `pass` | `DONE`; scope released |
| Event log size | 6 lines per task |

**Bug found and fixed:**
- **P2-1:** the plugin's own Python under `.claude/` was counted as project source, so doctor suggested `.claude` as a "module" in TypeScript projects. Dot-folders are now excluded from the source scan.
- Its regression test fails without the fix (20/21) and passes with it (21/21).

## Not covered
- A live interactive Claude Code session (login can't be reached from the test sandbox).
- Windows. Python compiles, and the hooks branch on `os.name`.

## Phase 3: agent model policy
| Check | Result |
|---|---|
| Frontmatter fields checked against the Claude Code docs (`model` aliases and ids, `effort` low…max, `maxTurns`, `omitClaudeMd`) | ✅ |
| economy / balanced / quality each render 9 agents that pass `claude plugin validate` | ✅ |
| `/models` change, then a plugin upgrade | Agents UNCHANGED (once the bug below was fixed); policy file kept (KEEP-SEED) |
| Hand edit to an agent's model | doctor WARN (not FAIL); `apply` keeps prompt edits |
| Invalid policy (`gpt-4`, `ultra`) | Exit 2, nothing written; doctor FAIL |

**Bug found and fixed:** after `/models apply`, managed keys came out in a different order than a fresh render produced, so upgrades flagged every agent as KEEP-EDITED. Managed keys are now written in a fixed order at the end of the frontmatter.
