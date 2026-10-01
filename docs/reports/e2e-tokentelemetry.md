# End-to-end test: tokentelemetry (brownfield)

**Date:** 2026-10-01 · **Plugin:** 0.2.0 → 0.2.1 · **Target:** [sarveshtalele/tokentelemetry](https://github.com/sarveshtalele/tokentelemetry) @ `20a1da5`. The test ran on a scratch clone; the real repo was never touched.

The repo is Python (FastAPI backend, telemetry daemon, Streamlit) plus React/Vite and an npm CLI. It has 105 source files and an existing `docs/ARCHITECTURE.md`.

## Flow (bootstrap SKILL.md, step by step)
| Step | Result |
|---|---|
| 1. Scan | brownfield · modules `backend` (own manifest, Python), `cli`, `frontend` · frameworks fastapi, react, streamlit, vite · npm |
| 2. Brief | Created with the `brief` copy command and filled from the README. Guardrail level, integrations, protected areas and outputs were left on "recommend" to exercise the interview. |
| 3. Tools | Live `claude plugin list/details` found `ponytail` (~676 always-on tokens) → SKIP. Playwright and Context7 MCP → ADD (frontend and dependencies detected). |
| 4. Interview | 7 questions in 2 rounds, generated from `interview.md` triggers. Defaults taken: standard level · protect `.github/workflows/*` · 3 module CLAUDE.md files · both MCP servers · ponytail off here · security-reviewer, ui-verifier, test-writer · no format-on-edit. |
| 5. Plan | Every command ran once first: `ruff check` passed, 20 backend tests passed, `npm run build` passed. The dry run showed 28 CREATE, `.gitignore` MERGE, and a SKIP for the existing `docs/ARCHITECTURE.md`. |
| 6. Generate | Source files untouched: only `.claude/`, the CLAUDE.md files, `docs/STATE.md`, `docs/adr/`, `specs/`, `.mcp.json`, the brief and 5 `.gitignore` lines. Root CLAUDE.md is 56 lines; module files are 16 lines each. |
| 7. Verify | Hook self-test OK (25 guard cases); `doctor` 0 FAIL / 0 WARN. |

## Behaviour checks (replayed Claude Code hook payloads)
| Scenario | Expected | Result |
|---|---|---|
| Edit an existing page / create a file in `frontend/src/` | allow | Pass |
| Create a stray `analysis-report.md` at the root | ask | Pass |
| Edit `.github/workflows/ci.yml` (protected) · edit `package-lock.json` · write `.env` | deny | Pass |
| `npm publish` · `git push -f` · `sed -i … .claude/settings.json` | deny | Pass |
| `npm install recharts` | ask | Pass |
| `npm ci` · `pytest` | allow | Pass |
| SessionStart after compaction re-injects STATE "Next step" | injected | Pass |
| Stop with code changed and STATE.md stale → then updated | block → allow | Pass |
| **Strict:** active TASK-001 allows its 2 files, denies `backend/app/main.py` and `App.tsx` | allow/deny | Pass |
| **Strict:** a broken `telemetry/reconcile.py` blocks the stop with pytest output; a harmless change passes | block / allow | Pass |
| Upgrade standard → strict, then a no-op re-run | 2 hooks added and registered; 0 writes | Pass |

## Bugs found and fixed (each now has a regression test)
| # | Bug | Fix |
|---|---|---|
| E2E-1 | `git_remote_host` returned a full path for local remotes | Only URL/SSH remotes produce a host |
| E2E-2 | `docs/superpowers/specs` was reported as a test dir | `specs` removed from test-dir names |
| E2E-3 | A SKIP plugin at user scope stayed on, and the plan couldn't turn it off | `plugins.disable` writes `enabledPlugins: false` |
| E2E-4 | Plan had to supply variables for files that would be skipped anyway | Variables are required only for files that will be written |
| E2E-5 | **Level upgrade created `test_on_stop.py` but never registered it** | Hooks are merged per entry, not per group |
| E2E-6 | `STATE.md` showed a noisy KEEP-EDITED diff on every upgrade | `STATE.md` and `ARCHITECTURE.md` are seed files: created once, then the user's |
| E2E-8 | **`test_on_stop` passed silently when its command wasn't found** (`python` missing outside the venv) | It blocks with the reason; `doctor` FAILs on an unrunnable command; `plan.md` requires venv-independent commands |
| E2E-9 | A `: ` in a filled-in value (for example risk areas) made the agent YAML invalid | Unsafe frontmatter values are quoted automatically |

(E2E-7 was an error in the test setup, not the plugin.)

## Not covered
- The interview itself ran with defaults, not in a live interactive Claude Code session. The CLI's login can't be reached from the test sandbox.
- Windows was not run. Hooks use `shell=(os.name == "nt")`, and `plan.md` documents `.venv\Scripts\python`.
