"""Move an official scaffold's output into the project. Deterministic; stdlib only.

Why: generators such as create-vite and create-next-app refuse a folder that isn't empty, and by the time
bootstrap scaffolds, the project already holds PROJECT-BRIEF.md and .claude/. So scaffold into a temporary
folder, then adopt it.

Usage:
  python3 adopt_scaffold.py <scaffold-dir> [--target DIR] [--dry-run]

Rules: .gitignore is union-merged; any other name that already exists in the project is a collision.
Exit 0 moved (or dry run) · 3 collisions, nothing moved · 2 bad arguments.
"""
import os
import shutil
import sys

MERGEABLE = {".gitignore"}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a: argv[i + 1] for i, a in enumerate(argv) if a == "--target" and i + 1 < len(argv)}
    if not args or not os.path.isdir(args[0]):
        print(__doc__, file=sys.stderr)
        return 2
    src = os.path.realpath(args[0])
    dst = os.path.realpath(flags.get("--target", "."))
    if dst == src or dst.startswith(src + os.sep):
        print("ERROR: target must not be inside the scaffold folder", file=sys.stderr)
        return 2
    names = sorted(n for n in os.listdir(src) if n not in (".git", "node_modules"))
    collisions = [n for n in names if os.path.exists(os.path.join(dst, n)) and n not in MERGEABLE]
    for n in names:
        state = "COLLISION" if n in collisions else ("MERGE" if os.path.exists(os.path.join(dst, n)) else "MOVE")
        print(f"{state:<10} {n}")
    if collisions:
        print(f"\nREFUSED: {len(collisions)} name(s) already exist in the project; nothing moved.", file=sys.stderr)
        return 3
    if "--dry-run" in argv:
        print(f"\nDRY RUN: {len(names)} item(s) would be adopted.")
        return 0
    for n in names:
        s, d = os.path.join(src, n), os.path.join(dst, n)
        if n in MERGEABLE and os.path.exists(d):
            with open(d, encoding="utf-8") as f:
                have = f.read()
            extra = [l for l in open(s, encoding="utf-8").read().splitlines() if l.strip() and l not in have.splitlines()]
            if extra:
                with open(d, "a", encoding="utf-8") as f:
                    f.write(("" if have.endswith("\n") else "\n") + "\n".join(extra) + "\n")
        else:
            shutil.move(s, d)
    print(f"\n{len(names)} item(s) adopted into {dst}. node_modules was not moved; run the install command.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
