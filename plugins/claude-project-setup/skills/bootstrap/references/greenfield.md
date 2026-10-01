# Greenfield

1. **Architecture first.** From the brief and the interview, draft:
   - the `ARCH_OVERVIEW`, `ARCH_COMPONENTS` (table rows) and `ARCH_EXTERNAL` vars;
   - one ADR decision (stack, with 1–2 rejected alternatives and why), which becomes `docs/adr/0001-stack.md` after generation;
   - the top-level folder tree, at most 2 levels deep.
   Only use components the requirements need. Add nothing speculative: no queue, cache or microservice without a requirement behind it.
2. **Official generator only.** Choose the stack's own scaffold command. Examples:

   | Stack | Command |
   |---|---|
   | Vite (React/Vue/Svelte) | `npm create vite@latest . -- --template react-ts` |
   | Next.js | `npx create-next-app@latest . --ts --eslint --app --use-npm` |
   | Angular | `npx @angular/cli@latest new <name> --directory . --skip-git` |
   | Python app/lib | `uv init` (then `uv add <deps>`) |
   | FastAPI | `uv init` + `uv add fastapi uvicorn` + `uv add --dev pytest ruff` |
   | Node library | `npm init -y` + `npm i -D typescript vitest` |

   Put the scaffold command in the setup plan, and run it only after approval. Check the generator's current flags first; prefer the Context7 MCP or the official docs over memory.
3. **Commands must be real.** After scaffolding, run install, test, lint and build once. Only commands that exit 0 go into `vars` (`INSTALL_CMD`, `TEST_CMD`, `FAST_TEST_CMD`, `LINT_CMD`, `BUILD_CMD`). Use `n/a` for a command that doesn't exist yet, and say so in STATE.md.
4. **Backlog:** after rendering, create `specs/tasks/TASK-001…N` stubs, one per numbered requirement in the brief, with status `planned` and `Allowed files` left as `TBD`. Put TASK-001 in STATE.md as the next step.
5. `write_allow` usually covers the source and test roots the scaffold created. `protected` is usually empty unless the brief says otherwise.
6. Run `git init` before the first commit, after asking the user.
