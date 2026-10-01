# Report: end-to-end test, v0.4.1 to v0.4.2

**Date:** 2026-10-02 · **Tested build:** the released `claude-project-setup-0.4.1.zip`, installed into an isolated folder · **Projects:** a fresh clone of [tokentelemetry](https://github.com/sarveshtalele/tokentelemetry) (brownfield) and an empty folder that became a Vite + React app (greenfield).

Each run followed the plugin's skill instructions step by step. The plugin hooks were executed through the exact command strings in `hooks/hooks.json`, and the project hooks through the commands registered in the generated `.claude/settings.json`. Project commands (ruff, pytest, `tsc`, `npm run build`, vitest) were installed and run for real.

## Coverage

| Area | Brownfield | Greenfield |
|---|---|---|
| Session-start hint before setup, after brief, after setup | Yes | Yes |
| Scan, brief, bootstrap machine, tool inventory | Yes | Yes |
| Plan, dry run, approval from the user's message, render gate | Yes (standard) | Yes (strict) |
| Official scaffold | n/a | `npm create vite`, then a test runner added |
| Self-test, doctor | Yes | Yes |
| Hooks in session: guard, context, stop gate, tests on stop, approvals | Yes | Yes |
| Task lifecycle, approval ambiguity, verifier gate | Yes | n/a |
| Generated skill with a review gate | Yes | n/a |
| `/models` profile change, then plugin upgrade | Yes | n/a |

## Findings

| # | Severity | Finding | Fix | Regression test |
|---|---|---|---|---|
| 1 | High | The Stop gate blocked the first turn after setup, because generated config files counted as "code changed after STATE.md" | Setup output (`.claude/`, Markdown, `.gitignore`, `.mcp.json`, `.env.example`) no longer counts as code, in both the stop gate and the strict test hook | `e2e_fix_stop_gate_and_state_after_setup` |
| 2 | High | Greenfield setup could not scaffold: create-vite printed `Operation cancelled`, because the folder already held `PROJECT-BRIEF.md` and `.claude/` | Generators now run in a temporary folder; the new `adopt_scaffold.py` moves the output in, merges `.gitignore`, refuses collisions and never moves `node_modules` | `e2e_fix_adopt_scaffold_into_non_empty_project` |
| 3 | Medium | `docs/STATE.md` after setup was the raw template, and that placeholder text was injected into every session | `render.py` seeds it from the plan: goal, date, next step (`next_step`), known gaps (`known_gaps`) | `e2e_fix_stop_gate_and_state_after_setup` |
| 4 | Medium | The strict level accepted `FAST_TEST_CMD: n/a`, so the test hook would block every stop | Render refuses a strict plan without a real fast test command | `e2e_fix_strict_needs_tests_and_skill_approval_message` |
| 5 | Medium | Greenfield guidance had no step to add a test runner; the Vite template has none | `greenfield.md`: every project gets a test runner and one passing test in the approved scaffold step | Verified in the greenfield re-run |
| 6 | Medium | After approving a skill's review gate, the hook told Claude to run `state_cli.py move skill-… approve`, a command that doesn't exist for skills | The message now names `skill_state.py done <gate>` for skills, and `state_cli.py move <id> approve` for setup and tasks | `e2e_fix_strict_needs_tests_and_skill_approval_message` |
| 7 | Medium | `/models` changed agent files, but `CLAUDE.md` kept listing the old models until a plugin upgrade | `apply_models.py` also updates the agent list and profile name in `CLAUDE.md`; a later upgrade stays UNCHANGED | `e2e_fix_models_keep_claude_md_in_sync` |
| 8 | Low | `CLAUDE.md` didn't name the protected paths, so Claude only found out by being denied | The guardrails section lists them | `e2e_fix_stop_gate_and_state_after_setup` |
| 9 | Low | Scan reported no Python package manager without a lockfile, ignored `requirements-dev.txt`, and didn't surface test frameworks or CI commands | Adds `pip`, reads every `requirements*.txt`, plus new `test_frameworks` and `ci_commands` fields. `brownfield.md` treats CI commands as candidates to verify, and never runs publish or deploy commands | `e2e_fix_scan_python_tests_and_ci` |
| 10 | Low | The resume hint ended in `it.).` | Punctuation fixed | Verified in the re-run |

All five new regression tests, plus one updated expectation, **fail against the released 0.4.1 code** (27/33) and pass against 0.4.2 (33/33).

## Re-run on the fixed code (fresh isolated copies)

| Check | Result |
|---|---|
| Brownfield: scan finds pip, pytest and the CI commands | Pass |
| Brownfield: render after approval; no Stop-gate block after setup; `STATE.md` seeded; `CLAUDE.md` names protected paths | Pass |
| Brownfield: self-test, doctor 0 FAIL | Pass |
| Brownfield: skill approval message, gate passes after approval | Pass |
| Brownfield: `/models economy` updates `CLAUDE.md`; upgrade leaves it UNCHANGED | Pass |
| Brownfield: no source files changed | Pass (the only untracked entries were the test harness's own symlinks to shared dependency folders) |
| Greenfield: scaffold in a temp folder and adopt into the non-empty project | Pass |
| Greenfield: test runner added and passing | Pass |
| Greenfield: strict refused with `FAST_TEST_CMD: n/a`, accepted with `npm test` | Pass |
| Greenfield: no Stop-gate block after setup; broken code blocks the stop (stop gate and tests) | Pass |
| Greenfield: self-test, doctor 0 FAIL | Pass |

## Still not covered
- A live interactive Claude Code session (the test sandbox cannot use your login).
- Windows.
