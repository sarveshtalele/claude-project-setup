# Greenfield

1. **Architecture first.** From the brief and the interview, draft:
   - the `ARCH_OVERVIEW`, `ARCH_COMPONENTS` (table rows) and `ARCH_EXTERNAL` vars;
   - one ADR decision (stack, with 1–2 rejected alternatives and why), which becomes `docs/adr/0001-stack.md` after generation;
   - the top-level folder tree, at most 2 levels deep.
   Only use components the requirements need. Add nothing speculative: no queue, cache or microservice without a requirement behind it.
2. **Official generator only.** Choose the stack's own scaffold command. Examples:

   | Stack | Command |
   |---|---|
   | Vite (React/Vue/Svelte) | `npm create vite@latest app -- --template react-ts` |
   | Next.js | `npx create-next-app@latest app --ts --eslint --app --use-npm` |
   | Angular | `npx @angular/cli@latest new app --skip-git` |
   | Python app/lib | `uv init app` (then `uv add <deps>` inside it) |
   | FastAPI | `uv init app` + `uv add fastapi uvicorn` + `uv add --dev pytest ruff` |
   | Node library | `mkdir app && cd app && npm init -y && npm i -D typescript vitest` |

   All commands run inside `${TMPDIR:-/tmp}/cps-scaffold/` and create `app/`, which you then adopt (below).

   Put the scaffold command in the setup plan, and run it only after approval. Check the generator's current flags first; prefer the Context7 MCP or the official docs over memory.

   **Scaffold into a temporary folder, never into the project root.** Generators refuse a folder that isn't empty, and the project already holds `PROJECT-BRIEF.md` and `.claude/`. Run the generator with a folder name instead of `.`, then adopt its output:
   ```bash
   mkdir -p "${TMPDIR:-/tmp}/cps-scaffold" && cd "${TMPDIR:-/tmp}/cps-scaffold" && npm create vite@latest app -- --template react-ts
   cd - && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adopt_scaffold.py" "${TMPDIR:-/tmp}/cps-scaffold/app" --dry-run
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/adopt_scaffold.py" "${TMPDIR:-/tmp}/cps-scaffold/app"
   ```
   It merges `.gitignore`, refuses any other name that already exists (exit 3, nothing moved), and never moves `node_modules`. Run the install command afterwards.
3. **Every project gets a test runner.** If the template has none (Vite apps don't), add the stack's standard one in the same approved step: `npm i -D vitest` and `"test": "vitest run"` for Vite and React, `uv add --dev pytest` for Python. Add one small passing test, so the verifier and the strict level have something real to run. The strict level refuses `FAST_TEST_CMD: n/a`.
4. **Commands must be real.** After scaffolding, run install, test, lint and build once. Only commands that exit 0 go into `vars` (`INSTALL_CMD`, `TEST_CMD`, `FAST_TEST_CMD`, `LINT_CMD`, `BUILD_CMD`). Use `n/a` for a command that doesn't exist yet, and say so in STATE.md.
5. **Backlog:** after rendering, create `specs/tasks/TASK-001…N` stubs, one per numbered requirement in the brief, with status `planned` and `Allowed files` left as `TBD`. Put TASK-001 in STATE.md as the next step.
6. `write_allow` usually covers the source and test roots the scaffold created. `protected` is usually empty unless the brief says otherwise.
7. Run `git init` before the first commit, after asking the user.
