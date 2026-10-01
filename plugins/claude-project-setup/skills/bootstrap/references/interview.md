# Interview rules

**Purpose:** close the gaps between the brief and the scan with as few questions as possible. Never assume silently, and never ask something the brief or the scan already answers.

## Mechanics
- Use the AskUserQuestion tool: up to **4 questions per round** and **2 rounds at most**.
- Each question has 2–4 options. Put the recommended option first and mark it `(Recommended)`, so "accept defaults" is always one click.
- Round 1 covers decisions that change the structure. Round 2 is only for follow-ups that round 1 answers create.
- Afterwards, append each answer to the brief's `## Decisions` section. That section is the durable record and survives compaction.

## Question bank (ask only when triggered)
| Topic | Ask when | Example | Plan field |
|---|---|---|---|
| Project type | Scan says `unknown` (greenfield) and the brief says "recommend" | "What are we building: an app, a library/CLI, an Agent Skill, a set of agents, or a Claude Code plugin?" | routes step 6 |
| Mode | Scan is ambiguous (a few files, no manifest) | "3 files, no manifest. Treat as greenfield?" | `mode` |
| Stack | Brief says "recommend" or conflicts with the scan | "Next.js + FastAPI, or Vite SPA + Express?" | greenfield scaffold, `vars` |
| Guardrail level | Brief says "recommend" | light / **standard** / strict, with the one-line definition of each | `level` |
| Autonomy | Always in greenfield; in brownfield only if write-allow is unclear | "Create files freely in `src/`, `tests/`?" | `write_allow` |
| Protected areas | Scan finds backend/, migrations/, infra/, generated code and the brief is silent | "Protect `backend/` and `migrations/`?" | `protected` |
| Specialist agents | Risk areas, migrations, a frontend or large modules exist | "Add `security-reviewer` (brief mentions auth)?" | `agents` |
| Quality hooks | A formatter or fast test command was detected | "Format edited files with Prettier? Run fast tests on Stop?" | `format_on_edit`, `level` |
| Modules | `module_candidates` is not empty | "Add module CLAUDE.md for `apps/web`, `packages/api`?" | `modules` |
| Plugins | `cps-tools.json` contains REUSE, ADD or CONFLICT plugin rows | "Enable `ponytail` (~676 tok/session) here?" / "Two style plugins: keep which?" | `plugins.enable` |
| MCP servers | ADD rows, or SKIP rows for servers that are configured but unused | "Add Playwright MCP for UI checks? GitHub MCP (needs GITHUB_PAT)?" | `mcp` |
| Model profile | Always (one question) | "Agent models: economy (cheapest), **balanced** (Recommended), or quality?" | `models.profile` |
| Outputs | Brief "Outputs location" is empty | "Runs and screenshots go to `~/work/<name>-runs`?" | `vars.OUTPUTS_DIR` |
| Existing instructions | Brownfield, with CLAUDE.md/AGENTS.md/.cursorrules present | "Merge AGENTS.md into CLAUDE.md and make it a pointer?" | merge step |

## Priorities when there are more than 8 candidate questions
Mode > Stack > Protected areas > Guardrail level > Modules > Integrations > Agents > the rest.
Questions that don't fit are defaulted to their Recommended option, and the setup plan lists them as "Defaulted: …" so the user can still change them.
