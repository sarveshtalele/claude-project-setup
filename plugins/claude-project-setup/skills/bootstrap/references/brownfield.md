# Brownfield

**Hard rule: no source code changes.** Only `CLAUDE.md` files, `docs/`, `specs/`, `.claude/`, `.mcp.json`, `.env.example`, `.gitignore` and the brief may be written.

1. **Facts from the scan, not exploration.** Fill `vars` from `cps-scan.json`:
   - `RUNTIME` and `PACKAGE_MANAGER` come from the languages, manifests and lockfiles.
   - Commands come from the `scripts` map (for example `package.json` scripts) or `pyproject` tools. **Run each command once** before it goes into `vars`. Use `n/a` with a note if it fails.
   - `LAYOUT` is one line per top-level folder that matters. Use the `explorer` agent only for what the scan can't answer (for example "what does `core/` do?"), with at most 3 targeted questions.
2. **Existing instructions:** read every file in `instruction_files`. The generated root CLAUDE.md is merged into the existing one (step 6 of SKILL.md), keeping all still-true user rules and dropping rules that contradict the repo. If `AGENTS.md` duplicates the content, propose making it a one-line pointer (`See CLAUDE.md.`).
3. **Existing `.claude/`:** `settings.json` and `.mcp.json` are union-merged by `render.py` and never overwritten. Existing agents or hooks with the same names are skipped; mention them in the plan.
4. **ARCHITECTURE.md describes what exists**, with path evidence: components, entry points, external services found in config. Gaps and smells go in STATE.md under "Known gaps" as `path:line`, not as fixes.
5. **Protected areas:** propose protecting generated code, vendored code, migrations, and any area the brief puts out of scope (for example `backend/*` for a frontend-only effort).
6. **Modules:** see [modules.md](modules.md).
7. **Large folders** (outputs, clones, caches inside the repo): don't move or delete them. Add `Read(./<dir>/**)` deny rules to the plan's `permissions.deny`, and list them in STATE.md "Known gaps" with the advice to move them outside the repo.
8. STATE.md: Goal (from the brief), Current task "none", Next step "/task <first requirement>", and the Known gaps found.
