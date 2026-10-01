# Tracker

A generic, append-only state-machine tracker used by Claude Project Setup for the bootstrap, task and generated-skill machines. Python 3.9+ standard library.

- `events.jsonl` is the source of truth. The snapshot is only a cache that `resume.py` rebuilds.
- Transitions are validated against a JSON definition ([format](references/machine-definition-format.md)). Guards are recorded events, with an optional `since_entry` scope.
- Writes are serialized by a lock file; a stale lock (older than 30 s) is broken automatically.
- Exit codes: `0` ok · `1` bad input · `2` locked · `3` illegal transition · `4` guard unmet · `5` precondition failed.

```bash
python3 scripts/init_machine.py --id <id> --definition <def.json> --state-dir <dir>
python3 scripts/transition.py  --id <id> --on <event> [--to <state>] --state-dir <dir>
python3 scripts/assert_state.py --id <id> --in <STATE> --state-dir <dir>
python3 scripts/query_state.py --id <id> --state-dir <dir>
python3 scripts/resume.py      --id <id> --state-dir <dir>
python3 scripts/render_reports.py --id <id> --state-dir <dir> [--progress-out p.md] [--changelog-out c.md]
python3 scripts/run_evals.py
```

Derived from the `state-machine-tracker` skill in codebase-migration-factory, with fixes for 4 bugs found in testing (stale-snapshot bypass, torn last line, missing snapshot, id path traversal); see `docs/reports/`.
