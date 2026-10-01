# Session audit: "Migration agent skills architecture"

> **Note (v0.2.0):** the `template/` folder this document refers to is now produced by the **Claude Project Setup** plugin. Run `/claude-project-setup:bootstrap` instead of copying files by hand (see the [README](../../README.md)).

Source: session `local_a8b6604b…` (CLI id `cfc8ba68…`), project `~/Downloads/codebase-migration-factory`.
I parsed the full transcript (19,874 JSONL records, 60 MB) and its subagent transcript, and checked the repo on disk on 2026-10-01.

## 1. What the session cost

| Metric | Value | Comment |
|---|---|---|
| Wall-clock span | 2026-09-25 → 2026-09-30 (6 days) | One session for the whole project |
| User prompts | 75 (12 of them replayed twice, see F2) | Many prompts held 5–8 separate asks |
| Assistant turns | 6,734 | |
| Compactions | 5 (one of them a duplicate) | Each one loses detail |
| Cost | **$383** (Sonnet 5: $213, Opus 5.5: $171) | |
| Cache-read tokens | **1.47 billion** | About 540k tokens of context re-read on every turn |
| Output tokens | 2.4 M | |
| Tool calls | Bash 2,096 · Edit 615 · Read 412 · Write 264 · Agent **2** · Grep/Glob **0** | Almost everything went through the shell |
| Bash calls with the sandbox disabled | **522 (25%)** | No sandbox allowlist was configured |
| Tool results over 20 KB | 45 | Each one stays in context until compaction |
| Lines added / removed | 23,740 / 3,028 | |
| Session ending | Usage limit hit partway through TASK-024 | Work stopped mid-task |

## 2. Findings: errors, gaps and inconsistencies

Severity: **P0** breaks correctness or the trust in a result · **P1** wastes large amounts of tokens or time · **P2** hygiene.

| # | Sev | Area | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| F1 | P0 | Accuracy | The "0% pixel diff / PARITY" result was measured on **hand-written Angular ports**, not on the skill's converter output. | `run-outputs/e2e/` has `tokentelemetry-ng/` and `registry-ng/` (hand ports, used for parity) next to `*-ng-converted/` (skill output). The SKILL.md says "mechanical JSX → template shell **+ guided port**". | Gate on the converter output only. Report two numbers: *converter parity* and *after manual port*. Fail the gate if a run needs manual edits that aren't listed as MANUAL rows in the mapping spec. |
| F2 | P0 | Context | The transcript has a **rewound or forked branch**: prompts U45–U56 repeat U20–U31 word for word, and compaction #3 is a byte-identical copy of compaction #1. | Compaction summaries at lines 3025 and 11215 have the same timestamp and length (40,024 chars). | Use one task per session. Don't resume or rewind across days; start fresh from `docs/STATE.md`. |
| F3 | P0 | Guardrails | Hard rules lived **only in prose** (CLAUDE.md and SKILL.md), so nothing enforced them. Examples: "never create files without consent", "no code before approval", "don't touch backend". | `.claude/` holds only `.DS_Store` and `.cc-writes`: no `settings.json`, no hooks, no agents. | Enforce these with `permissions` and hooks (see `template/.claude`). Keep prose for intent only. |
| F4 | P0 | Instructions | CLAUDE.md is **stale and contradicts the repo**. It was last edited 2026-09-25 14:14, before the two-skill pivot (TASK-010). | It requires 5 skills (3 exist), a `packages/` contracts package and Zod (both removed), `pnpm` baseline commands (the skills are standalone npm), and **9 named subagents (none exist)**. | When CLAUDE.md has rules the model can't follow, it learns to ignore CLAUDE.md. Rewrite it to about 80 lines (template provided) and update it in the same change as any architecture pivot. |
| F5 | P1 | Instructions | `AGENTS.md` is a find-and-replace copy of CLAUDE.md, and the replace corrupted it (it says `.Codex/agents/`). | `diff` shows the two files are identical apart from the replaced word. Claude Code **doesn't read AGENTS.md when a CLAUDE.md exists**. | Keep one source. If you need AGENTS.md for other tools, make it a one-line pointer to CLAUDE.md. |
| F6 | P1 | Architecture | Names don't match what the code does. `codebase-migration-testing` actually *converts* code, and its scope grew to **Streamlit → Next.js** (TASK-024). The v10 spec still describes 5 skills. | SKILL.md `description` and `scope` metadata. | Split into `codebase-conversion` and `parity-testing`, or rename it. Amend the v10 spec, or archive it as historical. |
| F7 | P1 | Architecture | Code is shared by copying, so extra tooling is needed to stop the copies drifting. The tracker is vendored into 2 skills; `capture.ts`, `markdown.ts`, `doc-approval.ts` and `app-runner.ts` are byte-identical across skills; `check-shared.py` and `sync-vendor.sh/.ps1` exist only to catch drift. | `scripts/check-shared.py`, `vendor/VENDORED_FROM.json`. | Publish one shared npm package (or one skill with sub-commands). Duplicate only what a standalone install truly needs. |
| F8 | P1 | Architecture | The skills need **two runtimes** (TypeScript on Node 24 type-stripping, and Python for the tracker) plus Playwright. You asked about this yourself in U60. | `compatibility` fields. | Pick one runtime per bundle. TypeScript fits here because Playwright, ts-morph and Angular are all Node, so port the 6 tracker scripts to TS. |
| F9 | P1 | Process | The spec-first process cost more than the product: 25 task specs (280 KB), 14 required fields per task, and gap-fix tasks numbered TASK-012/013/014 "gap-fixes-1/2/3". Spec format was inconsistent: TASK-000…008 and 012–014 have `.md`+`.json`, while 009–011 and 015–024 have `.md` only. | `specs/tasks/`. | Use a 1-page task template (provided) with acceptance as **runnable commands**, and keep JSON only if a tool consumes it. |
| F10 | P1 | Process | Gaps were patched one repo at a time, so the same class of bug came back. You noticed: "why everytime u are giving toml file issue" (U23) and "why u didnt fix them before" (U25). A portability break was found **by you on another machine** (Windows, `workspace:*` / `ERR_MODULE_NOT_FOUND`), not by tests. | U16, U23, U25. | Every bug report becomes a fixture and an eval *before* the fix. Add a clean-room install test (copy the skill to a temp dir, `npm ci`, run evals) on macOS and Windows in CI. |
| F11 | P1 | Tokens | Bash was used for everything (2,096 calls, 0 Grep/Glob), outputs were often unbounded, and 45 tool results were over 20 KB. Long-running harness logs were `cat`-ed into context. | Tool stats. | Use Grep/Glob/Read with ranges. Pipe shell output through `tail -n 40`. Delegate wide searches to a cheap read-only `explorer` subagent. Block reads of `run-outputs/`, `node_modules/` and `dist/` with deny rules. |
| F12 | P1 | Tokens | Unbounded loops: "/loop Dont stop improving skills until they both achieve exactly the same ui" (U38), "Until the ui matches exactly dont stop" (U75). The session hit the usage limit 3 times. | U38, U58, U75, final turn. | Every loop needs a cap (N iterations or a token budget) and a stop condition that a script evaluates, not the model. |
| F13 | P1 | Security | 25% of shell commands ran outside the sandbox (Playwright Chromium, git, npm cache, gh). | 522 of 2,096 Bash calls. | Configure the sandbox once: allowed network hosts, `excludedCommands` for Chromium/git, and an npm cache inside `$TMPDIR`. Don't disable it for each command. |
| F14 | P2 | Repo hygiene | The factory root is **not a git repository**. History lives only in `CHANGELOG.md` and a separate push clone. | `git rev-parse` fails. | Run `git init` on day one. Without it, rollback, diffs, hooks and reviews all degrade. |
| F15 | P2 | Repo hygiene | The repo holds 2.9 GB of non-source data: `run-outputs/` 2.6 GB, `.pnpm-store` 205 MB, root `node_modules` 116 MB, the `brd-generator…` clone 82 MB, and **3 copies of the skills** (`skills/`, `bundle/`, `run-outputs/push`, plus `run-outputs/fresh-bundle`). The pnpm workspace files are still there although the skills dropped them. | `du`. | Keep clones and run outputs **outside** the repo (for example `~/work/runs/`). Build the bundle in CI rather than committing it. Delete the dead workspace files. |
| F16 | P2 | Skills | The discovery `SKILL.md` is 423 lines / 25 KB, with a description of about 600 chars and a `compatibility` paragraph of about 700 chars. All of this loads whenever the skill triggers. | `wc`. | Keep SKILL.md under 200 lines: what, when, steps, and hard rules. Move details to `references/`. Make the description one trigger-rich sentence. |
| F17 | P2 | Docs | You asked for READMEs with no scripts because users run skills from chat (U30), but the skills need `npm install` and `npx playwright install chromium`. | README vs `compatibility`. | Be explicit: one "Prerequisites (one time)" block, then chat-only usage. |
| F18 | P2 | Open gap | When a repo has two frontends, discovery silently picks the one with higher confidence. | Final summary. | Add an `app` pin in the discovery config, and refuse to continue when the choice is ambiguous. |
| F19 | P2 | Prompting | Prompts mixed many goals with typos, and approvals were bare "go ahead" or "A". The model had to infer scope, and that inference was lost at compaction. | U14, U28, U31, U38. | Use the prompt templates in `README.md` §8: one goal, explicit scope, explicit "done when". |
| F20 | P2 | Config | Two always-on style plugins (caveman and ponytail) were in use, caveman was toggled per message, and the model was switched from Sonnet to Opus mid-session. | Transcript. | Pick one output style per project in settings. Route models by role (planner, implementer, explorer), not mid-session. |

## 3. Root causes (the 5 that produced most of the findings)

1. **One session as the project.** With no external state file, the only memory was the conversation. Compaction then lossily summarized it 5 times, and every turn paid for about 540k tokens of history. (F2, F11, F12)
2. **Guardrails written as wishes.** Every hard rule was prose. Prose is the weakest control layer; permissions and hooks are deterministic. (F3, F13)
3. **Instructions not versioned with the architecture.** The pivot changed the code but not CLAUDE.md or the spec. (F4, F5, F6)
4. **Validation measured the wrong thing.** Parity was measured after manual edits, and portability was tested in place rather than in a clean room. (F1, F10)
5. **No project skeleton on day one:** no git, no output directory outside the repo, no `.claude/` config. (F14, F15)

## 4. Corrective plan for `codebase-migration-factory`

| Phase | Do | Done when |
|---|---|---|
| **P0: stop the bleeding** (1 session) | `git init` and a first commit. Move `run-outputs/`, the clones and `bundle/` out of the repo. Replace CLAUDE.md with `template/CLAUDE.md`, filled in. Delete AGENTS.md or reduce it to a pointer. Copy `template/.claude/` in. Write `docs/STATE.md`. | `git status` is clean, the repo is under 120 MB, `claude` starts with STATE injected, and the hooks are proven by `template/.claude/hooks/selftest.py` |
| **P1: make the claim true** (1–2 sessions) | Change the parity gate to measure converter output. Make the report show converter vs manual parity. Add an eval: the converted app must build and pass the gate, or list each MANUAL row. | Gate output names its input directory, and the eval passes |
| **P2: simplify the architecture** (2–3 sessions) | One runtime (TypeScript). One shared package instead of vendored copies (delete `check-shared.py` and `sync-vendor.*`). Rename or split the migration-testing skill. Shrink each SKILL.md below 200 lines. | All evals pass; a clean-room install passes on macOS and Windows in CI |
| **P3: harden** | Pin the app in the discovery config (F18). Turn every past bug (toml, workspace dependency, two frontends, TZ) into a fixture. Update the v10 spec or archive it. | Regression suite covers F10 and F18 |

Run each phase as **its own session**, started from `docs/STATE.md`, with the `implementer` → `verifier` → `reviewer` agents (see `template/.claude/agents/`).
