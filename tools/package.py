"""Build a release package of the plugin. Run from the repository root: python3 tools/package.py

Checks that the working tree is clean, that the version in plugin.json matches the CHANGELOG and the
README badge, that the test suite passes and (if the claude CLI is available) that the plugin validates.
Then writes dist/claude-project-setup-<version>.zip (marketplace + plugin + README + CHANGELOG + LICENSE
if present) and a .sha256 file next to it. Nothing is published; use gh release create for that.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENTS = [".claude-plugin", "plugins", "README.md", "CHANGELOG.md", "LICENSE"]


def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def fail(msg):
    print(f"PACKAGE ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if run("git", "status", "--porcelain").stdout.strip():
        fail("working tree is not clean; commit first so the package matches a commit")
    with open(os.path.join(ROOT, "plugins/claude-project-setup/.claude-plugin/plugin.json"), encoding="utf-8") as f:
        version = json.load(f)["version"]
    if f"## [{version}]" not in open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read():
        fail(f"CHANGELOG.md has no '## [{version}]' section")
    if f"version-{version}-" not in open(os.path.join(ROOT, "README.md"), encoding="utf-8").read():
        fail(f"README version badge does not say {version}")
    tests = run(sys.executable, "plugins/claude-project-setup/tests/test_scripts.py")
    if tests.returncode != 0:
        fail("tests failed:\n" + tests.stdout[-800:])
    if shutil.which("claude"):
        for target in (".", "plugins/claude-project-setup"):
            v = run("claude", "plugin", "validate", target)
            if "Validation passed" not in v.stdout + v.stderr:
                fail(f"claude plugin validate {target} failed")
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    name = f"claude-project-setup-{version}"
    out = os.path.join(ROOT, "dist", f"{name}.zip")
    paths = [p for p in CONTENTS if os.path.exists(os.path.join(ROOT, p))]
    r = run("git", "archive", "--format=zip", f"--prefix={name}/", "-o", out, "HEAD", *paths)
    if r.returncode != 0:
        fail(r.stderr.strip())
    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    with open(out + ".sha256", "w", encoding="utf-8") as f:
        f.write(f"{digest}  {name}.zip\n")
    print(f"{tests.stdout.strip().splitlines()[-1]}\nbuilt dist/{name}.zip\nsha256 {digest}")


if __name__ == "__main__":
    main()
