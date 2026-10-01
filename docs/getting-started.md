# Getting started

## Prerequisites
| Need | Version | Check |
|---|---|---|
| Claude Code | with plugin support | `claude --version` |
| Python | 3.9+ (`python3` on macOS/Linux, `python` on Windows) | `python3 --version` |
| git | any | `git --version` |

## Install

**1. Add the marketplace**
```bash
claude plugin marketplace add sarveshtalele/claude-project-setup
```
**2. Install the plugin**
```bash
claude plugin install claude-project-setup@claude-project-setup
```
**3. Start Claude Code in your project folder**
```bash
cd my-project && claude
```

Only `plugins/claude-project-setup/` is installed: skills, scripts, templates, the tracker and two plugin hooks (session hint, approval capture). This `docs/` folder isn't. Step-by-step instructions for every kind of project are in the [Setup guide](setup-guide.md).

### Try without installing
```bash
git clone https://github.com/sarveshtalele/claude-project-setup.git
```
```bash
claude --plugin-dir ./claude-project-setup/plugins/claude-project-setup
```

## First run

<p align="center"><img src="assets/workflow.svg" alt="Workflow" width="100%"></p>

- **New project:** in an empty folder, describe what you want to build:
  > I want to build a habit-tracker web app with login, daily streaks and a weekly email summary.
- **Existing repo:** open the repo and ask:
  > Set up this repo for Claude. Goal: add CSV export and a date filter; don't touch `backend/`.
- The plugin takes over from there: it drafts the brief, asks before writing it, interviews you, shows the plan, and generates files only after you approve.
- Slash commands work too: `/claude-project-setup:brief`, then `/claude-project-setup:bootstrap`.

## After setup
1. **Start a new session** so the new hooks, agents and `CLAUDE.md` files load.
2. Accept the **workspace trust** prompt. Claude Code ignores the project's `permissions.allow` rules until you do.
3. Begin with `/task <first requirement>`.

## Update and uninstall
```bash
claude plugin update claude-project-setup@claude-project-setup
```
```bash
claude plugin uninstall claude-project-setup@claude-project-setup
```
Generated files stay in your project; they belong to you. To refresh generated agents and hooks after an update, run `/claude-project-setup:doctor upgrade`.

Next: [User guide](user-guide.md)
