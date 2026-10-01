#!/usr/bin/env python3
"""Run evals/evals.json assertions against the scripts in this skill.
Stdlib only. Exits non-zero if any eval fails.

Usage: run_evals.py [--evals <path>]
"""
import argparse
import json
import os
import subprocess
import time
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"


def substitute(args, tmp: str):
    return [a.replace("{tmp}", tmp).replace("{skill}", str(SKILL_ROOT)) for a in args]


def check_files(step: dict, tmp: str):
    for check in step.get("expect_file_contains", []):
        file_path = Path(substitute([check["path"]], tmp)[0])
        if not file_path.exists():
            return False, f"expected file {file_path} to exist"
        content = file_path.read_text()
        for needle in check["contains"]:
            if needle not in content:
                return False, f"expected {file_path} to contain {needle!r}, got:\n{content}"
    return True, ""


def run_step(step: dict, tmp: str):
    if "mkfile" in step:
        path = Path(tmp) / step["mkfile"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("precreated")
        if "age_seconds" in step:
            old = time.time() - step["age_seconds"]
            os.utime(path, (old, old))
        return True, ""

    if "append" in step:  # simulate a crash artefact: raw text appended to a file
        with (Path(tmp) / step["append"]).open("a", encoding="utf-8") as f:
            f.write(step["text"])
        return True, ""

    if "rm" in step:
        (Path(tmp) / step["rm"]).unlink()
        return True, ""

    if "expect_absent" in step:
        path = Path(tmp) / step["expect_absent"]
        return (not path.exists()), f"expected {path} to be absent"

    if "cmd" not in step:
        return check_files(step, tmp)

    cmd = substitute(step["cmd"], tmp)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / cmd[0]), *cmd[1:]],
        capture_output=True, text=True,
    )
    expect_exit = step.get("expect_exit", 0)
    if proc.returncode != expect_exit:
        return False, f"exit {proc.returncode} != {expect_exit}\nstdout={proc.stdout}\nstderr={proc.stderr}"

    for needle in step.get("expect_contains", []):
        if needle not in proc.stdout:
            return False, f"expected stdout to contain {needle!r}, got: {proc.stdout!r}"

    expect_json = step.get("expect_json")
    if expect_json is not None:
        try:
            out = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return False, f"could not parse JSON stdout: {proc.stdout!r}"
        for k, v in expect_json.items():
            if out.get(k) != v:
                return False, f"expect_json mismatch: {k}={out.get(k)!r} != {v!r}"

    return check_files(step, tmp)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evals", type=Path, default=SKILL_ROOT / "evals" / "evals.json")
    args = p.parse_args()

    suite = json.loads(args.evals.read_text())
    failures = []
    for case in suite["evals"]:
        with tempfile.TemporaryDirectory() as tmp:
            for i, step in enumerate(case["steps"]):
                ok, detail = run_step(step, tmp)
                if not ok:
                    failures.append(f"[{case['name']}] step {i}: {detail}")
                    break

    total = len(suite["evals"])
    print(f"{total - len(failures)}/{total} evals passed")
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
