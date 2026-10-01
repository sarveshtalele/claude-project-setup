# Claude Code project kit

> **Note (v0.2.0):** the `template/` folder this document refers to is now produced by the **Claude Project Setup** plugin. Run `/claude-project-setup:bootstrap` instead of copying files by hand (see the [README](../../README.md)).

This is a playbook and a copy-ready `template/` for starting any project with Claude Code. It aims for accurate results, low token use, and guardrails that are enforced by machinery rather than requested in prose.
It was built from an audit of the "Migration agent skills architecture" session. Read **[session-audit.md](session-audit.md)** for what went wrong there and the fix plan for that repo.

```
claude-project-kit/
├── README.md                 ← this playbook
├── SESSION-AUDIT.md          ← findings F1–F20 + corrective plan for codebase-migration-factory
└── template/                 ← copy into any project root
    ├── CLAUDE.md             ← about 50 lines; fill in the <placeholders>
    ├── .gitignore
    ├── docs/STATE.md         ← cross-session memory (injected automatically)
    ├── docs/adr/0000-template.md
    ├── specs/TASK-TEMPLATE.md
    └── .claude/
        ├── settings.json     ← permissions (allow/ask/deny), hooks, sandbox
        ├── write-allow.txt   ← where new files may be created without asking
        ├── hooks/            ← guard.py · session_context.py · stop_gate.py · selftest.py
        ├── agents/           ← explorer · implementer · verifier · reviewer
        ├── skills/           ← /task (plan) · /checkpoint (save state)
        └── rules/            ← path-scoped rules (load only when matching files are touched)
```

---

## 1. The model: four layers of control

Prose is the weakest control. Put each rule in the **strongest layer that can express it**.

| Layer | Strength | Use for | In this kit |
|---|---|---|---|
| 1. **Permissions** (`settings.json`: allow/ask/deny) | Hard, native | Secrets, dangerous commands, noisy directories | `deny` Read on `.env*`, keys, `node_modules/`, `dist/`; `ask` on push and installs |
| 2. **Hooks** (deterministic scripts) | Hard, scriptable | Rules that need logic: "ask before any new file", "STATE.md must be updated", "inject state after compaction" | `guard.py`, `stop_gate.py`, `session_context.py` |
| 3. **Sandbox** | Hard, OS-level | Filesystem and network boundary for Bash | `sandbox.enabled: true`; configure the allowlist once (§6) |
| 4. **CLAUDE.md, rules and skills** (prose) | Soft | Intent, conventions, workflow | The template files |

In your session, every hard rule ("no file without consent", "don't touch the backend", "no code before approval") lived only in layer 4. That is audit finding F3.

## 2. Setup for a new project (about 10 minutes, mostly no AI)

```bash
cp -R ~/Downloads/claude/claude-project-kit/template/. ./my-project/
```
```bash
cd my-project && git init && git add -A && git commit -m "chore: project skeleton"
```
```bash
python3 .claude/hooks/selftest.py
```
Then, by hand:
1. Fill in the `<placeholders>` in `CLAUDE.md`: the stack, the 4 commands and the layout. Keep it **under 100 lines**.
2. Write the **Goal** line in `docs/STATE.md`.
3. Edit `.claude/write-allow.txt` to list your real source and test folders.
4. Edit `settings.json` → `permissions.allow` to list your real test and lint commands, so they never prompt.
5. Choose an output directory **outside** the repo for clones, screenshots and run outputs (for example `~/work/<project>-runs/`), and record it in CLAUDE.md.
6. **Windows:** replace `python3` with `python` (or `py`) in the 3 hook commands in `settings.json`.

Only then start `claude`. The first prompt is §8.1.

**Existing project:** run the built-in `/init` first, then merge its output into the template `CLAUDE.md`. Keep the facts it found and drop the boilerplate.

## 3. Session and context protocol (how not to lose context)

The rule: **the conversation isn't memory; files are.** The session you ran lasted 6 days, went through 5 compactions and cost $383, because the conversation was the only place the project's state lived.

| Situation | Do this |
|---|---|
| Starting work | Start a new session. `session_context.py` injects `docs/STATE.md` and the git status, so you don't need a recap. |
| One task finished | `/checkpoint`, then `/clear`. The task file and STATE.md carry everything. |
| Context is getting long (status line shows over 50%) | `/checkpoint`, then `/compact keep: current task file, failing tests, decisions not yet in STATE.md`. After compaction, the hook re-injects STATE.md. |
| Second compaction in the same session | Stop. `/checkpoint`, then start a new session. Two compactions mean the task was too big; split it. |
| Next day | Start a new session, not `--resume`. Resuming reloads the whole old context, and rewinding or forking duplicated 12 prompts in your transcript (F2). |
| Ended mid-task (usage limit) | The Stop hook already forced STATE.md to be current, so start a new session. |
| Decision made in chat | It doesn't exist until it is in STATE.md, the task file or an ADR. `/checkpoint` writes it down. |

What lives where:

| Need | File | Loaded |
|---|---|---|
| Stable rules and commands | `CLAUDE.md` | Every session |
| Rules for one area (tests, skills, API) | `.claude/rules/*.md` with `paths:` | Only when matching files are touched |
| Where we are now | `docs/STATE.md` | Injected at start, resume, clear and compaction |
| What one change must do | `specs/tasks/TASK-NNN.md` | When a task is worked on |
| Why the architecture is the way it is | `docs/adr/` | On demand |
| History | `git log` | On demand, never in context |
| Personal preferences (not committed) | `CLAUDE.local.md` | Every session |

## 4. Token optimisation checklist

Each item is ordered by how much it saved, or would have saved, in the audited session.

1. **Short sessions.** Cost grows with context × turns. Your session re-read about 540k tokens per turn, 1.47 B tokens in total. Keeping each task to its own session is the biggest saving available.
2. **Delegate searching.** The `explorer` agent runs on Haiku in its own context and returns about 30 lines of `path:line` facts. The main context never sees the file dumps.
3. **Deny noisy reads.** `node_modules`, `dist`, lockfiles and run outputs are denied in `settings.json`. Keep 2.6 GB of run outputs outside the repo (F15).
4. **Bound tool output.** Use Grep, Glob and Read with ranges instead of `cat`. Pipe Bash through `| tail -n 40`. Never `cat` a log. Your session produced 45 tool results over 20 KB.
5. **Keep CLAUDE.md small:** under 100 lines, facts only. Move area-specific rules into `.claude/rules/` with `paths:` so they load only when relevant.
6. **Keep SKILL.md small:** under 200 lines. Details go in `references/`, which load only when the skill needs them.
7. **Route models by role:** plan and review on Opus, implement on Sonnet, explore and verify on Haiku. The agents' `model:` field already does this. Don't switch the main model mid-task.
8. **Never write unbounded loops.** "Don't stop until it matches exactly" needs a cap: *"max 5 iterations; stop and report if the diff isn't decreasing."*
9. **Use one output style.** Choose caveman *or* ponytail, set it once, and don't toggle it per message.
10. **Batch questions.** Ask up to 3 clarifying questions at the start of a task, not one at a time across turns.

## 5. Agents: when to use which

| Agent | Model | Writes? | Use when |
|---|---|---|---|
| `explorer` | haiku | no | Any search wider than about 3 files; repo mapping; "where is X used" |
| `implementer` | sonnet | yes, allowed files only | Exactly one **approved** task |
| `verifier` | haiku | no | After implementation, to run the acceptance commands and report PASS/FAIL verbatim. Checking claims this way, rather than trusting what the model said, was the gap in F1. |
| `reviewer` | inherit | no | Before each commit: diff vs spec, security, drift |

Standard flow for one task:
```
/task <title>  →  you approve  →  implementer  →  verifier  →  reviewer  →  commit  →  /checkpoint  →  /clear
```
Read-only agents can run in parallel. Run only one writing agent at a time. Four agents that exist and get used beat nine that are only listed in CLAUDE.md (F4).

## 6. Guardrails and security that this kit enforces

| Rule | Enforced by | Behaviour |
|---|---|---|
| Never read or write secrets | `deny` Read rules and `guard.py` PROTECTED | Hard block |
| Never write outside the project (temp dir allowed) | `guard.py` | Hard block |
| **Ask before creating any new file** not in `write-allow.txt` | `guard.py` → `ask` | You approve each new path |
| Don't edit lockfiles, `.git/`, `.claude/settings.json` or `.claude/hooks/` | `guard.py` | Hard block, so the agent can't weaken its own guardrails |
| No force-push, `reset --hard`, `git clean -f`, `sudo`, `curl \| sh`, `--no-verify`, `npm publish` | `guard.py` and `deny` rules | Hard block |
| Dependency installs and `git push` ask first | `guard.py` and `ask` rules | You approve each one |
| STATE.md must be current before a turn ends | `stop_gate.py` | Claude is sent back once to update it |
| State survives `/clear` and compaction | `session_context.py` | Injected automatically |

**Sandbox:** 25% of your Bash calls bypassed the sandbox (F13). Instead of disabling it per command, allow what the project needs once, in `.claude/settings.json` under `sandbox` (allowed network domains for your registries, and excluded commands for tools such as Playwright's Chromium that can't run sandboxed). Run `/sandbox` in a terminal session to see and edit the effective config.

Domain-specific guards follow the same pattern as `guard.py`. For example, "only migrate the frontend, never touch `backend/`" becomes one line added to `PROTECTED`: `"backend/*"`.

## 7. Recommended project structure

```
my-project/
├── CLAUDE.md                 # ≤100 lines: stack, commands, layout, rules
├── docs/
│   ├── STATE.md              # ≤60 lines: where we are now
│   └── adr/                  # one file per architecture decision
├── specs/
│   ├── TASK-TEMPLATE.md
│   └── tasks/TASK-001-*.md   # one page each; acceptance = commands
├── src/ …  tests/ …          # your code
└── .claude/                  # settings, hooks, agents, skills, rules (all committed)
```
Not in the repo: clones of other repos, screenshots, run outputs, built bundles, package stores. Put them under `~/work/<project>-runs/`.

**For skill bundles** (like your migration factory):
```
skills-repo/
├── CLAUDE.md
├── packages/shared/          # ONE shared lib (not vendored copies + drift checkers)
├── skills/<skill-name>/
│   ├── SKILL.md              # ≤200 lines
│   ├── references/           # details, loaded on demand
│   ├── scripts/              # deterministic, non-interactive, one runtime
│   └── evals/                # fixtures from real bugs + runner
└── .github/workflows/ci.yml  # clean-room install + evals on macOS and Windows
```

## 8. Prompt templates

One prompt carries one goal. Each template states its scope and a "done when".

**8.1 Kickoff (first session):**
```
Read CLAUDE.md and docs/STATE.md. Goal: <one line>.
Use explorer to map the repo (≤30 lines). Then ask me at most 3 questions that change the plan.
Do not create any files yet.
```

**8.2 Plan one change:**
```
/task <title>
Context: <evidence: error text, file:line, screenshot path>.
Out of scope: <…>. Done when: <observable result / command>.
```

**8.3 Implement (after you approve):**
```
Approved. Run implementer on specs/tasks/TASK-007-*.md, then verifier, then reviewer.
Report the three results only.
```

**8.4 Bounded improvement loop (replaces "don't stop until perfect"):**
```
Goal: <metric> on <input> reaches <target>. Max 5 iterations.
Each iteration: one hypothesis → one change → re-measure with <command>.
Stop early if the metric doesn't improve twice in a row, and report what's blocking.
```

**8.5 Bug report from another machine:**
```
/task fix <symptom>
Repro: <exact command + error>. First add a failing eval fixture that reproduces it,
then fix the class of bug (not just this repo), then run the clean-room install test.
```

**8.6 End of day:** `/checkpoint`

## 9. Checklist before calling a project "set up"

- [ ] `git init` done and the first commit made
- [ ] `python3 .claude/hooks/selftest.py` prints `OK`
- [ ] CLAUDE.md is under 100 lines, and every command in it actually runs
- [ ] Only one instruction file (no AGENTS.md copy; if another tool needs it, make it a one-line pointer to CLAUDE.md)
- [ ] `docs/STATE.md` has a Goal
- [ ] Run outputs and clones directory is outside the repo
- [ ] `permissions.allow` covers your test, lint and typecheck commands, so you get no prompt fatigue
- [ ] Sandbox allowlist configured for the tools you know you'll need

Docs used: code.claude.com/docs/en/{memory, settings, hooks, sub-agents, skills}, checked on 2026-10-01. Hook events and subagent and skill frontmatter fields were verified against those pages.
