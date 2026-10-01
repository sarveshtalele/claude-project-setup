#!/usr/bin/env python3
"""Report current state and legal next transitions. Stdlib only.

Usage: query_state.py --id <machine-id> [--state-dir <dir>]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _common as c  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--state-dir", type=Path, default=Path("."))
    args = p.parse_args()

    d = c.state_dir(args.state_dir, args.id)
    if not c.machine_path(d).exists():
        c.die(1, "unknown machine id", id=args.id)

    machine = c.load_json(c.machine_path(d))
    events = c.read_events(c.events_path(d))
    current = c.replay_state(machine, events)

    legal = []
    for t in machine["transitions"]:
        if t["from"] != current:
            continue
        legal.append({
            "on": t["on"], "to": t["to"], "guard": t.get("guard"),
            "guard_scope": t.get("guardScope", "ever") if t.get("guard") else None,
            "guard_satisfied": c.guard_satisfied(t, events),
        })

    print(json.dumps({"id": args.id, "current_state": current, "legal_transitions": legal}))


if __name__ == "__main__":
    main()
