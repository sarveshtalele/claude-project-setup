---
paths:
  - "skills/**"
  - ".claude/skills/**"
---
# Rules for authoring Agent Skills (loaded only when touching skills)
- SKILL.md under 200 lines: what, when, steps, hard rules. Everything else goes in `references/` and is linked.
- `description`: one or two sentences, under 400 chars, starting with what the skill does, then "Use when …" with real trigger phrases.
- Scripts are deterministic and non-interactive. The agent asks the human and passes the answer as a CLI flag.
- One runtime per skill. Don't vendor copies of shared code; depend on one package.
- Every skill folder is installable on its own: test it by copying to a temp dir, then a clean install, then evals, on macOS and Windows.
- A success claim must name exactly what it measured. Example: "parity on converter output", not on hand-edited output.
- Every reported bug becomes an eval fixture before it is fixed.
