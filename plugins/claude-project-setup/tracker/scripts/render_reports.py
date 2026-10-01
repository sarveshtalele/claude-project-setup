#!/usr/bin/env python3
"""Render progress.md and changelog.md from a machine's events.jsonl and
machine.json (including its optional stateDescriptions). Stdlib only.

Usage:
  render_reports.py --id <machine-id> [--state-dir <dir>]
                     [--progress-out <path>] [--changelog-out <path>]

Defaults: <state-dir>/.state-machine/<id>/progress.md and changelog.md.
Pass --progress-out/--changelog-out to place them wherever the caller's
own layout expects them.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _common as c  # noqa: E402


def render_progress(machine_id: str, machine: dict, snapshot: dict, events: list) -> str:
    state = snapshot["current_state"]
    descriptions = machine.get("stateDescriptions", {})
    desc = descriptions.get(state)

    lines = [f"# Progress — `{machine_id}`", ""]
    lines.append(f"**Current state:** `{state}`")
    if desc:
        lines.append(f"> {desc}")
    lines.append("")
    lines.append(f"Updated: {snapshot['updated_at']}")
    lines.append("")

    lines.append("## Legal next transitions")
    legal = [t for t in machine["transitions"] if t["from"] == state]
    if not legal:
        lines.append("_(none — terminal state for this machine)_")
    else:
        for t in legal:
            guard = t.get("guard")
            target_desc = descriptions.get(t["to"])
            suffix = f" — {target_desc}" if target_desc else ""
            if guard:
                satisfied = "satisfied" if c.guard_satisfied(t, events) else "UNMET"
                scope = t.get("guardScope", "ever")
                lines.append(f"- `{t['on']}` → `{t['to']}` (guard `{guard}`, scope `{scope}`: {satisfied}){suffix}")
            else:
                lines.append(f"- `{t['on']}` → `{t['to']}`{suffix}")
    lines.append("")

    lines.append("## Recent history")
    recent = events[-10:]
    if not recent:
        lines.append("_(no events yet)_")
    else:
        lines.append("| Seq | Time | Type | Event | Detail |")
        lines.append("| --- | --- | --- | --- | --- |")
        for e in recent:
            if e.get("type") == "transition":
                detail = f"{e['from']} → {e['to']}"
            elif e.get("type") == "reset":
                detail = f"machine reset → {e.get('to')} (history before this kept, not replayed)"
            else:
                detail = "(recorded, no state change)"
            lines.append(f"| {e['seq']} | {e['ts']} | {e['type']} | `{e.get('on', '')}` | {detail} |")
    lines.append("")
    return "\n".join(lines)


def render_changelog(machine_id: str, machine: dict, events: list) -> str:
    descriptions = machine.get("stateDescriptions", {})
    lines = [f"# Changelog — `{machine_id}`", ""]
    if not events:
        lines.append("_(no events yet)_")
        return "\n".join(lines) + "\n"

    for e in events:
        ts = e.get("ts", "?")
        if e.get("type") == "transition":
            target_desc = descriptions.get(e["to"])
            suffix = f" — {target_desc}" if target_desc else ""
            lines.append(f"- **{ts}** — `{e['on']}`: `{e['from']}` → `{e['to']}`{suffix}")
        elif e.get("type") == "reset":
            lines.append(f"- **{ts}** — **machine reset** → `{e.get('to')}` (a new run starts here)")
        else:
            lines.append(f"- **{ts}** — event `{e.get('on', '')}` recorded" + (f" ({e['data']})" if e.get("data") else ""))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--state-dir", type=Path, default=Path("."))
    p.add_argument("--progress-out", type=Path)
    p.add_argument("--changelog-out", type=Path)
    args = p.parse_args()

    d = c.state_dir(args.state_dir, args.id)
    if not c.machine_path(d).exists():
        c.die(1, "unknown machine id", id=args.id)

    machine = c.load_json(c.machine_path(d))
    events = c.read_events(c.events_path(d))
    snapshot = {"current_state": c.replay_state(machine, events),
                "updated_at": events[-1]["ts"] if events else c.now_iso()}

    progress_out = args.progress_out or (d / "progress.md")
    changelog_out = args.changelog_out or (d / "changelog.md")
    progress_out.parent.mkdir(parents=True, exist_ok=True)
    changelog_out.parent.mkdir(parents=True, exist_ok=True)

    progress_out.write_text(render_progress(args.id, machine, snapshot, events), encoding="utf-8")
    changelog_out.write_text(render_changelog(args.id, machine, events), encoding="utf-8")

    print(json.dumps({"ok": True, "progress": str(progress_out), "changelog": str(changelog_out)}))


if __name__ == "__main__":
    main()
