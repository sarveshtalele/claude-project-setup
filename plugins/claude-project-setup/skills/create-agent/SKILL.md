---
name: create-agent
description: Create a new project subagent in .claude/agents/ with model optimisation built in (cheapest capable model per role, minimal tools, turn cap, short output contract, escalation). Use when the user asks to create, add or design an agent/subagent, or wants a specialist for a recurring job (e.g. "an agent that reviews SQL migrations").
argument-hint: "[what the agent should do]"
---

# Create an agent

## 1. Understand the job (at most 4 AskUserQuestion questions; skip anything already said)
- **Role:** what it does, with one example request.
- **Writes?** Read-only, edits files in a given area, or runs commands only.
- **Scope:** which folders or files it works in.
- **Output:** what the caller needs back (a verdict, a list of findings, a patch summary…).

## 2. Derive the design (deterministic; show it to the user)
Pick the **tier** from the role, then use [references/agent-design.md](references/agent-design.md) for the model per profile, the tool set and the output contract.

| Tier | Typical roles | Tools |
|---|---|---|
| `scout` | search, map, check, verify, lint | Read, Grep, Glob (+ Bash if it must run commands) |
| `builder` | implement, write tests, refactor, migrate | Read, Grep, Glob, Edit, Write, Bash |
| `judge` | review, security, architecture, migration safety | Read, Grep, Glob, Bash |

- **Name:** kebab-case, not already in `.claude/agents/`.
- **Description:** one sentence on what it does, plus "Use when …". It must not overlap an existing agent's description; compare them all and reword if two would trigger on the same request.

## 3. Consent, then write
1. Show the full agent file. Its body comes from the skeleton in agent-design.md.
2. Ask: "Create `.claude/agents/<name>.md`?" Write it only after a yes. The guard hook may also ask.
3. If `.claude/agent-models.json` exists, add `"<name>"` to **every** profile with the tier's settings from agent-design.md. Then run:
   ```bash
   python3 .claude/scripts/apply_models.py
   python3 .claude/scripts/apply_models.py --check
   ```
   `--check` must list no difference for the new agent.
   If the policy file doesn't exist (light setup), write the frontmatter values directly.

## 4. Prove it
- Give one **test prompt** the user can try, e.g. "Use the `<name>` agent to …", and say what a good answer looks like.
- Add a line to the `## Agents` list in `CLAUDE.md`: `` `<name>` (<model>): <first sentence of the description>. ``
