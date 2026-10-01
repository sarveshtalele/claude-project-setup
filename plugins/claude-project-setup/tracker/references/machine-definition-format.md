# Machine definition format

A machine definition is a single JSON file passed to `init_machine.py
--definition`. Validated against
[assets/schemas/machine-definition.schema.json](../assets/schemas/machine-definition.schema.json).

```json
{
  "initial": "DISCOVERY.FINGERPRINT",
  "stateDescriptions": {
    "DISCOVERY.FINGERPRINT": "Repository/file/config/manifest inventory captured.",
    "DISCOVERY.STRUCTURE": "Project/module/feature/file topology classified.",
    "GATE1.PENDING": "Migration IR validated; awaiting human approval of source understanding."
  },
  "transitions": [
    {"from": "DISCOVERY.FINGERPRINT", "on": "fingerprint_complete", "to": "DISCOVERY.STRUCTURE"},
    {"from": "DISCOVERY.STRUCTURE",   "on": "structure_complete",   "to": "DISCOVERY.PATTERNS"},
    {"from": "DISCOVERY.IR",          "on": "ir_valid",             "to": "GATE1.PENDING"},
    {"from": "GATE1.PENDING",         "on": "approve",              "to": "ASSESSMENT.TARGET", "guard": "gate1_approved"}
  ]
}
```

## States

States are opaque strings — this tracker never parses them. A useful convention is dot-separated hierarchy (`PARENT.CHILD`, e.g. `BUILD.TEST`), but any string works. A state doesn't
need a separate declaration — it exists by appearing in `initial` or in some
transition's `from`/`to`.

## Transitions

Each entry is `{from, on, to, guard?, guardScope?}`:

- `from` — the state this transition applies in.
- `on` — the event name that triggers it (what you pass to `transition.py --on`).
- `to` — the resulting state.
- `guard` (optional) — the name of a domain event that must have already
  been recorded (via `transition.py --on <guard-name>` with no `--to`)
  before this transition is allowed. There is no expression language: a
  guard is satisfied purely by "has an event with this name ever been
  recorded for this machine" — compose multiple guards by requiring
  multiple distinct event names across multiple transitions if you need an
  AND, or by having the consumer only record the right event for the right
  branch.
- `guardScope` (optional, needs `guard`) — `ever` (default): the guard event
  counts if recorded any time since the last reset. `since_entry`: it counts
  only if recorded since the machine last entered this transition's `from`
  state. Use `since_entry` for a gate inside a loop, so a stale pass from an
  earlier attempt can't satisfy a later one.

Two `(from, on)` pairs may legally point at different `to` — that models a
branch (e.g. `GATE4.PENDING` going to either `PHASE.DRAFTING` or
`FINAL.VALIDATION`) — the caller picks which by passing the matching `--to`.

## Events log entry shapes

One JSON object per line in `events.jsonl`, oldest first:

- Transition: `{"seq", "ts", "type": "transition", "on", "from", "to", "data"}`
- Recorded domain event (no state change): `{"seq", "ts", "type": "event", "on", "data"}`
- Reset (from `init_machine.py --force`): `{"seq", "ts", "type": "reset", "on": "reset", "to": <initial>, "data"}`.
  Replay, guards and reports all start after the most recent reset; earlier
  events stay in the log as history.

`data` is caller-supplied free-form JSON (default `{}`), useful for
attaching e.g. an approver's name or a spec hash to the event without this
skill needing to understand it.

## `stateDescriptions` (optional)

A map from exact state string to a 1–2 line human description — used by
`render_reports.py` to make `progress.md`/`changelog.md` readable without
the reader having to already know what `DISCOVERY.FINGERPRINT` means. Not
required: a state with no entry just renders without a description. Keep
each one to what a table cell would say, not a paragraph — if you need
more, put it in the consuming skill's own docs and link to it.

## Snapshot shape

`state-snapshot.json`: `{"current_state", "seq", "updated_at"}` — a cache of
"replay all events so far"; `resume.py` can always rebuild it from
`events.jsonl` alone.
