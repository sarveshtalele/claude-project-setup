# Module CLAUDE.md files (large repos)

Claude Code loads a subfolder's `CLAUDE.md` only when it works in that folder. Module files keep the root small, and each session pays only for the area it touches.

## Which folders
Start from `module_candidates` in the scan. A folder qualifies if it has **its own manifest**, has **more than 150 source files**, or uses **a language other than the root's**. Confirm the list in the interview (at most 8 modules; group small ones under their parent).
Skip vendored code, generated code, examples, fixtures, and clones of other repos.

## Content (≤ 40 lines; template `CLAUDE.module.md`)
| Var | Content |
|---|---|
| `MODULE_PURPOSE` | One sentence: what the module does and who calls it |
| `MODULE_ENTRY_POINTS` | 2–5 bullets of real files (`path`: role), checked to exist |
| `MODULE_TEST_CMD`, `MODULE_BUILD_CMD` | Commands run from the module folder, checked once, or `n/a` |
| `MODULE_RULES` | 1–5 bullets of rules that apply **only** here (conventions, forbidden imports, owners) |

Never repeat root rules in a module file. If a rule applies everywhere, it belongs in the root.

## Module experts (optional)
For at most 3 of the biggest modules, add a `module-expert` agent:
`{"template": "module-expert", "vars": {"AGENT_NAME": "<module>-expert", "MODULE": "<path>"}}`.
Offer this in the interview; it's worth it only when the user will work in that module often.

## Path-scoped rules
When a rule applies to a file type across modules (API handlers, UI components, tests), use `.claude/rules/` with `paths:` (`api`, `ui` and `testing` templates) instead of copying it into every module file.
