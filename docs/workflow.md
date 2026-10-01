# Workflow: from description to a set-up project

```mermaid
sequenceDiagram
    autonumber
    actor U as You
    participant C as Claude Code
    participant S as Scripts (no AI)
    participant P as Project
    U->>C: Describe the project / "set up this repo"
    C->>S: scan_repo.py
    S-->>C: mode, stack, modules, existing instructions
    C->>U: Draft brief. Create PROJECT-BRIEF.md?
    U->>C: Yes (edit, then "go")
    C->>S: scan_tools.py
    S-->>C: plugins and MCP servers: REUSE / ADD / SKIP / CONFLICT
    C->>U: Interview (≤ 2 rounds × 4 questions)
    U->>C: Answers (or defaults)
    C->>S: render.py --dry-run
    S-->>C: exact file list
    C->>U: Setup plan. Reply "approved"
    U->>C: approved
    Note over U,C: approval hook records user_approved from your message
    C->>S: state_cli move bootstrap approve
    C->>S: render.py (refuses unless APPROVED)
    S->>P: CLAUDE.md files, agents, hooks, settings, .mcp.json
    C->>S: selftest.py + doctor.py
    S-->>U: PASS table
```

## Step by step

**0. Resume.** Every step is a transition of the bootstrap state machine. After an interruption, the next session's start hook says where to resume.

**1. Trigger**
- You describe a project in chat. The plugin's `brief` skill matches on its description.
- In a project that isn't set up yet, a one-line SessionStart hint tells Claude the plugin is available. It's silent once the project is set up.

**2. Scan**: `scan_repo.py`
- Detects the **project type**: app, library, skill, agents, plugin or unknown. For skill, agents and plugin projects, bootstrap offers the matching generator once the base setup is written ([details](creating-skills-and-plugins.md)).
- Detects greenfield vs brownfield, languages, frameworks, package managers, scripts and test folders.
- Lists existing `CLAUDE.md`, `AGENTS.md`, `.cursorrules` and `.claude/`.
- Finds module candidates: folders with their own manifest, more than 150 source files, or a different language from the root.

**3. Brief**: `PROJECT-BRIEF.md`
- Drafted from your words only, with a consent question before it's written.
- Brownfield: stack prefilled as `keep current (…)`.

**4. Tool inventory**: `scan_tools.py`
- Runs `claude plugin list --json --available`, `claude plugin details` (token cost) and `claude mcp list`.
- Sorts each item into REUSE, ADD, SKIP or CONFLICT. See [Integrations](integrations.md).

**5. Interview**
- Asks only about gaps or conflicts between the brief and the scan. Priority order: mode → stack → protected areas → level → modules → integrations → agents.
- Answers are appended to `## Decisions` in the brief, so they survive compaction.

**6. Setup plan**
- Claude writes a plan JSON (schema: [plan.md](../plugins/claude-project-setup/skills/bootstrap/references/plan.md)). Every command in it is run once first.
- `render.py --dry-run` shows the exact CREATE, MERGE and SKIP list.

**7. Approve**: reply `approved`. Nothing has been written or installed yet.
- The approval hook records your reply. Claude can't record it for you.
- `render.py` refuses a first-time setup until the bootstrap machine is `APPROVED`.
- If the plan changes, you approve again. Details: [State machines](state-machines.md).

**8. Generate**
- Greenfield: the official scaffold runs first (`npm create vite`, `create-next-app`, `uv init`…).
- `render.py` writes the files. An existing `CLAUDE.md` is merged by hand, with a diff shown.
- Each new plugin install needs its own yes.

**9. Verify**
- `.claude/hooks/selftest.py` and `doctor.py` must pass with no FAIL rows.
- Claude offers a commit, then tells you to start a new session.

## Greenfield vs brownfield

```mermaid
flowchart TD
    Q{"Source files?"} -- none --> G["Greenfield"]
    Q -- some --> B["Brownfield"]
    G --> G1["Architecture + ADR-0001"] --> G2["Official scaffold"] --> G3["Verify commands"] --> G4["Task stubs per requirement"]
    B --> B1["Facts from scan"] --> B2["Merge existing instructions"] --> B3["Module CLAUDE.md"] --> B4["No source changes"]
    G4 --> R["render.py"]
    B4 --> R
```

| | Greenfield | Brownfield |
|---|---|---|
| Source code | Created by the official scaffold | **Never modified** |
| `CLAUDE.md` | Generated | Merged into yours, with a diff shown |
| `docs/ARCHITECTURE.md` | The approved design | What exists, with path evidence (kept if you already have one) |
| Task stubs | One per requirement | Created later with `/task` |
