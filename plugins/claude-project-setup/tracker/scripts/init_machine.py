#!/usr/bin/env python3
"""Register a new state machine for a consuming skill. Stdlib only.

Usage:
  init_machine.py --id <machine-id> --definition <path-to-definition.json> [--state-dir <dir>] [--force]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _common as c  # noqa: E402


def validate_definition(defn: dict) -> None:
    if not isinstance(defn.get("initial"), str) or not defn["initial"]:
        c.die(1, "definition.initial must be a non-empty string")
    if not isinstance(defn.get("transitions"), list):
        c.die(1, "definition.transitions must be a list")
    for i, t in enumerate(defn["transitions"]):
        for key in ("from", "on", "to"):
            if not isinstance(t.get(key), str) or not t[key]:
                c.die(1, f"transitions[{i}].{key} must be a non-empty string")
        if "guardScope" in t:
            if t["guardScope"] not in ("ever", "since_entry"):
                c.die(1, f"transitions[{i}].guardScope must be 'ever' or 'since_entry'")
            if not t.get("guard"):
                c.die(1, f"transitions[{i}].guardScope needs a guard")
    if "stateDescriptions" in defn:
        if not isinstance(defn["stateDescriptions"], dict):
            c.die(1, "definition.stateDescriptions must be an object")
        for state, desc in defn["stateDescriptions"].items():
            if not isinstance(desc, str) or not desc:
                c.die(1, f"stateDescriptions[{state!r}] must be a non-empty string")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--definition", required=True, type=Path)
    p.add_argument("--state-dir", type=Path, default=Path("."))
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    defn = c.load_json(args.definition)
    validate_definition(defn)

    d = c.state_dir(args.state_dir, args.id)
    if c.machine_path(d).exists() and not args.force:
        c.die(3, "machine already initialized", id=args.id, hint="use --force to reinitialize")

    d.mkdir(parents=True, exist_ok=True)
    with c.Lock(c.lock_path(d)):
        # A re-init keeps prior history: it appends a `reset` marker that
        # replay, guards and reports all start after, instead of leaving
        # stale events that resume.py would otherwise replay.
        events = c.read_events(c.events_path(d))
        seq = max((e.get("seq", 0) for e in events), default=0)
        if events:
            seq += 1
            c.append_event(c.events_path(d), {"seq": seq, "ts": c.now_iso(), "type": "reset", "on": "reset", "to": defn["initial"], "data": {}})
        c.save_json_atomic(c.machine_path(d), defn)
        c.save_json_atomic(c.snapshot_path(d), {"current_state": defn["initial"], "seq": seq, "updated_at": c.now_iso()})
        c.events_path(d).touch(exist_ok=True)

    print(json.dumps({"initialized": True, "id": args.id, "current_state": defn["initial"], "reset": bool(events)}))


if __name__ == "__main__":
    main()
