# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · versions follow [SemVer](https://semver.org/).

## [Unreleased]
### Added
- State machines (roadmap phases 1–2). The bootstrap machine makes setup resumable, and `render.py` refuses a first-time setup until it's `APPROVED`. Each `/task` gets a task machine (`PLANNED → APPROVED → IN_PROGRESS → VERIFYING → DONE`) at the standard and strict levels.
- `approval_capture` hook: `user_approved` is recorded only from the user's own message. `state_cli` refuses it, and `guard.py` blocks it in the shell.
- `scope_check` reads the task machine (with a `STATE.md` fallback). The verifier and implementer record transitions.
- Tracker vendored into `tracker/`, with 4 bug fixes (stale-snapshot bypass, torn last line, missing snapshot, id path traversal) and regression evals.
- Agent model policy (roadmap phase 3):
  - `.claude/agent-models.json` (economy / balanced / quality profiles, per-agent overrides with globs, escalation ladder) and `apply_models.py`, which is deterministic and rewrites only the managed frontmatter keys.
  - `/models` project skill and `create-agent` plugin skill (tier → model per profile → minimal tools → output contract).
  - Every agent reports `UNCERTAIN:` when unsure, and `CLAUDE.md` tells the main session to retry it once on the next tier.
  - `doctor` reports model drift (WARN) and invalid policies (FAIL).
- Project types and generators (roadmap phase 4):
  - `scan_repo` detects app, library, skill, agents, plugin or unknown, and bootstrap routes to the matching generator.
  - `scaffold.py` plus the `create-skill` and `create-plugin` skills. Generated skills get portable frontmatter, `${CLAUDE_SKILL_DIR}` paths, a step state machine with review gates, `skill_state.py`, and evals derived from the machine. Plugin bundles get a marketplace, one shared tracker, tier-optimised agents and a README.
  - Approvals can name a skill run (`approve skill-<name>`).
### Fixed
- Scan no longer counts dot-folder tooling (`.claude/`, `.github/`) as project source.

## [0.3.0] - 2026-10-01
### Added
- Auto-invocation: describing a project in chat triggers `brief`, which drafts `PROJECT-BRIEF.md` (with consent) and hands off to `bootstrap`.
- Plugin SessionStart hint (`hooks/hooks.json`), shown only in projects that aren't set up yet.
- Generated `settings.json` sets `attribution.commit` / `attribution.pr` to `""`, so there are no AI co-author lines.
- Documentation set in `docs/` (not shipped with the plugin).

## [0.2.1] - 2026-10-01
### Fixed (from the [tokentelemetry end-to-end run](docs/reports/e2e-tokentelemetry.md))
- A level upgrade now registers every new hook (settings are merged per entry).
- `test_on_stop` blocks when its command can't run, and `doctor` checks it.
- `STATE.md` and `ARCHITECTURE.md` are seed files, never diffed on upgrade.
- Variables are required only for files that will be written. Added `plugins.disable`. Unsafe YAML frontmatter values are quoted.
- Scan: correct `git_remote_host` for local remotes, and `specs/` is no longer treated as a test folder.

## [0.2.0] - 2026-10-01
### Added
- First release: the `brief`, `bootstrap`, `doctor` and `integrations` skills; deterministic `scan_repo`, `scan_tools`, `render` and `doctor` scripts; 9 agent templates, 7 hook templates, 3 guardrail levels, and the plugin/MCP catalog.
