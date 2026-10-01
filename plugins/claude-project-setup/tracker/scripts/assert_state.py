#!/usr/bin/env python3
"""Precondition check: exit 0 only if the machine is currently in one of
the given states, exit 5 otherwise. Read-only, never writes. Stdlib only.

Call this BEFORE doing a step's work, so an out-of-order step does nothing
at all -- instead of doing its work and only then finding out the
transition is illegal.

Usage: assert_state.py --id <machine-id> --in <STATE> [--in <STATE> ...] [--state-dir <dir>]
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
    p.add_argument("--in", dest="allowed", action="append", required=True)
    p.add_argument("--state-dir", type=Path, default=Path("."))
    args = p.parse_args()

    d = c.state_dir(args.state_dir, args.id)
    if not c.machine_path(d).exists():
        c.die(1, "unknown machine id", id=args.id)

    current = c.replay_state(c.load_json(c.machine_path(d)), c.read_events(c.events_path(d)))
    if current not in args.allowed:
        c.die(5, "precondition failed", id=args.id, current_state=current, allowed=args.allowed)
    print(json.dumps({"ok": True, "id": args.id, "current_state": current}))


if __name__ == "__main__":
    main()
