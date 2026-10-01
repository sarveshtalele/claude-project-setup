#!/usr/bin/env python3
"""Reconstruct current state purely from events.jsonl and heal a
missing/stale snapshot. Stdlib only.

Usage: resume.py --id <machine-id> [--state-dir <dir>]
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
    p.add_argument("--lock-timeout", type=float, default=5.0)
    p.add_argument("--stale-lock-after", type=float, default=30.0)
    args = p.parse_args()

    d = c.state_dir(args.state_dir, args.id)
    if not c.machine_path(d).exists():
        c.die(1, "unknown machine id", id=args.id)

    machine = c.load_json(c.machine_path(d))
    events = c.read_events(c.events_path(d))

    recomputed_state = c.replay_state(machine, events)
    seq = max((e.get("seq", 0) for e in events), default=0)

    snapshot_state = None
    if c.snapshot_path(d).exists():
        try:
            snapshot_state = c.load_json(c.snapshot_path(d)).get("current_state")
        except json.JSONDecodeError:
            snapshot_state = None

    match = snapshot_state == recomputed_state

    with c.Lock(c.lock_path(d), timeout=args.lock_timeout, stale_after=args.stale_lock_after):
        c.save_json_atomic(c.snapshot_path(d), {
            "current_state": recomputed_state, "seq": seq, "updated_at": c.now_iso(),
        })

    print(json.dumps({
        "id": args.id,
        "recomputed_state": recomputed_state,
        "snapshot_state": snapshot_state,
        "match": match,
        "healed": True,
    }))


if __name__ == "__main__":
    main()
