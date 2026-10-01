"""Shared helpers for state-machine-tracker scripts. Stdlib only, no imports
of anything outside this file within the skill."""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def state_dir(base: Path, machine_id: str) -> Path:
    if not ID_RE.match(machine_id) or ".." in machine_id:
        die(1, "invalid machine id (letters, digits, . _ - only)", id=machine_id)
    return base / ".state-machine" / machine_id


def machine_path(d: Path) -> Path:
    return d / "machine.json"


def snapshot_path(d: Path) -> Path:
    return d / "state-snapshot.json"


def events_path(d: Path) -> Path:
    return d / "events.jsonl"


def lock_path(d: Path) -> Path:
    return d / ".lock"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def die(code: int, message: str, **extra):
    print(json.dumps({"error": message, **extra}), file=sys.stderr)
    sys.exit(code)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_atomic(path: Path, data) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def read_events(events_file: Path):
    if not events_file.exists():
        return []
    out = []
    lines = [l.strip() for l in events_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, line in enumerate(lines):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1:  # torn write from a crash: ignore, it never committed
                print(json.dumps({"note": "ignored incomplete last event line", "file": str(events_file)}), file=sys.stderr)
                continue
            die(1, "corrupt events.jsonl", line=i + 1, file=str(events_file))
    return out


def next_seq(events: list) -> int:
    return max((e.get("seq", 0) for e in events), default=0) + 1


def append_event(events_file: Path, event: dict) -> None:
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True))
        f.write("\n")


def since_last_reset(events: list) -> list:
    """Events after the most recent `reset` (all events if never reset).
    `init_machine.py --force` appends a reset rather than truncating, so
    history survives but never leaks into the current run."""
    for i in range(len(events) - 1, -1, -1):
        if events[i].get("type") == "reset":
            return events[i + 1:]
    return events


def replay_state(machine: dict, events: list) -> str:
    state = machine["initial"]
    for e in since_last_reset(events):
        if e.get("type") == "transition":
            state = e["to"]
    return state


def guard_satisfied(transition: dict, events: list) -> bool:
    """One definition of "guard satisfied", used by every script.

    guardScope "ever" (default): an event with the guard's name exists
    since the last reset. "since_entry": it exists since the machine last
    entered this transition's `from` state -- so an approval from an
    earlier attempt can't unlock a later one.
    """
    guard = transition.get("guard")
    if not guard:
        return True
    scoped = since_last_reset(events)
    if transition.get("guardScope") == "since_entry":
        for i in range(len(scoped) - 1, -1, -1):
            e = scoped[i]
            if e.get("type") == "transition" and e.get("to") == transition["from"]:
                scoped = scoped[i + 1:]
                break
    return any(e.get("type") == "event" and e.get("on") == guard for e in scoped)


class Lock:
    """Exclusive lock via O_CREAT|O_EXCL — one portable primitive, no
    fcntl/msvcrt platform branching.

    A lock older than `stale_after` seconds is treated as left behind by a
    crashed writer and broken (writes hold it for milliseconds). Age-based,
    not PID-based: os.kill(pid, 0) terminates the target on Windows.
    ponytail: two processes breaking the same stale lock in the same
    microsecond could both proceed -- the rename+re-check narrows that to
    a lock that was already `stale_after` seconds dead.
    """

    def __init__(self, path: Path, timeout: float = 5.0, poll: float = 0.05, stale_after: float = 30.0):
        self.path = path
        self.timeout = timeout
        self.poll = poll
        self.stale_after = stale_after
        self._fd = None

    def _break_if_stale(self) -> None:
        try:
            if time.time() - self.path.stat().st_mtime < self.stale_after:
                return
            grave = self.path.with_name(f"{self.path.name}.stale.{os.getpid()}")
            os.replace(self.path, grave)
        except FileNotFoundError:
            return
        if time.time() - grave.stat().st_mtime < self.stale_after:
            os.replace(grave, self.path)  # someone re-locked between stat and rename; give it back
            return
        grave.unlink(missing_ok=True)
        print(json.dumps({"note": "stale lock broken", "path": str(self.path)}), file=sys.stderr)

    def __enter__(self):
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                self._break_if_stale()
                if not self.path.exists():
                    continue
                if time.monotonic() >= deadline:
                    die(2, "locked", path=str(self.path))
                time.sleep(self.poll)

    def __exit__(self, exc_type, exc, tb):
        if self._fd is not None:
            os.close(self._fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
