#!/usr/bin/env python3
"""Apply a transition, or record a domain event, against a registered
machine. Stdlib only.

Usage:
  transition.py --id <machine-id> --on <event-name> --to <target-state> [--data '{"k":"v"}'] [--state-dir <dir>]
  transition.py --id <machine-id> --on <event-name> [--data '{"k":"v"}'] [--state-dir <dir>]

With --to: attempts a state transition. Must match a declared transition
(from=current_state, on=event, to=target); rejected with no file changes if
no such transition is declared, or if its guard is unmet.

Without --to: records a domain event only (e.g. an approval), without
changing state. A transition whose guard names this event later treats it
as satisfied.
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
    p.add_argument("--on", required=True)
    p.add_argument("--to")
    p.add_argument("--data")
    p.add_argument("--state-dir", type=Path, default=Path("."))
    p.add_argument("--lock-timeout", type=float, default=5.0)
    p.add_argument("--stale-lock-after", type=float, default=30.0)
    args = p.parse_args()

    data = json.loads(args.data) if args.data else {}
    d = c.state_dir(args.state_dir, args.id)
    if not c.machine_path(d).exists():
        c.die(1, "unknown machine id", id=args.id)

    with c.Lock(c.lock_path(d), timeout=args.lock_timeout, stale_after=args.stale_lock_after):
        machine = c.load_json(c.machine_path(d))
        events = c.read_events(c.events_path(d))
        current = c.replay_state(machine, events)  # event log is the truth; snapshot is only a cache
        seq = c.next_seq(events) - 1

        if args.to is None:
            seq += 1
            c.append_event(c.events_path(d), {
                "seq": seq, "ts": c.now_iso(), "type": "event", "on": args.on, "data": data,
            })
            c.save_json_atomic(c.snapshot_path(d), {"current_state": current, "seq": seq, "updated_at": c.now_iso()})
            print(json.dumps({"applied": False, "recorded_event": True, "on": args.on}))
            return

        match = next(
            (t for t in machine["transitions"]
             if t["from"] == current and t["on"] == args.on and t["to"] == args.to),
            None,
        )
        if match is None:
            c.die(3, "illegal transition", frm=current, on=args.on, to=args.to)

        if not c.guard_satisfied(match, events):
            c.die(4, "guard unmet", guard=match.get("guard"), guard_scope=match.get("guardScope", "ever"), frm=current, on=args.on, to=args.to)

        seq += 1
        c.append_event(c.events_path(d), {
            "seq": seq, "ts": c.now_iso(), "type": "transition",
            "on": args.on, "from": current, "to": args.to, "data": data,
        })
        c.save_json_atomic(c.snapshot_path(d), {
            "current_state": args.to, "seq": seq, "updated_at": c.now_iso(),
        })
        print(json.dumps({"applied": True, "from": current, "to": args.to}))


if __name__ == "__main__":
    main()
