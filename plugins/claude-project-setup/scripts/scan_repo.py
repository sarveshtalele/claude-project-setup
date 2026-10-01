"""Deterministic repository scan. Prints JSON; writes nothing.

Usage: python3 scan_repo.py [ROOT] [--module-threshold 150]

Decides greenfield vs brownfield, finds manifests, languages, frameworks, commands,
tests, existing AI instruction files, and module candidates for nested CLAUDE.md.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".nuxt", ".venv", "venv", "env",
             "__pycache__", ".pytest_cache", ".mypy_cache", "target", "coverage", ".turbo",
             ".cache", "vendor", ".idea", ".vscode", ".gradle", "out", ".svelte-kit", ".angular"}
LANG = {".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript",
        ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".vue": "vue",
        ".svelte": "svelte", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
        ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift", ".dart": "dart",
        ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".scala": "scala", ".ex": "elixir"}
MANIFESTS = {"package.json": "node", "pyproject.toml": "python", "requirements.txt": "python",
             "setup.py": "python", "Pipfile": "python", "go.mod": "go", "Cargo.toml": "rust",
             "pom.xml": "java", "build.gradle": "java", "build.gradle.kts": "kotlin", "Gemfile": "ruby",
             "composer.json": "php", "pubspec.yaml": "dart", "mix.exs": "elixir"}
LOCKS = {"package-lock.json": "npm", "pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "bun.lockb": "bun",
         "bun.lock": "bun", "uv.lock": "uv", "poetry.lock": "poetry", "Pipfile.lock": "pipenv",
         "Cargo.lock": "cargo", "go.sum": "go"}
MONOREPO = ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "rush.json"]
INSTRUCTION_FILES = ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".cursorrules", "GEMINI.md",
                     ".github/copilot-instructions.md", ".windsurfrules", ".mcp.json"]
FRAMEWORKS = {  # dependency name -> framework label
    "next": "nextjs", "react": "react", "vue": "vue", "nuxt": "nuxt", "@angular/core": "angular",
    "svelte": "svelte", "@sveltejs/kit": "sveltekit", "solid-js": "solid", "astro": "astro",
    "vite": "vite", "express": "express", "@nestjs/core": "nestjs", "fastify": "fastify",
    "hono": "hono", "electron": "electron", "react-native": "react-native", "expo": "expo",
    "fastapi": "fastapi", "django": "django", "flask": "flask", "streamlit": "streamlit",
    "pytest": "pytest", "jest": "jest", "vitest": "vitest", "@playwright/test": "playwright",
    "cypress": "cypress", "prisma": "prisma", "sqlalchemy": "sqlalchemy", "alembic": "alembic",
    "@sentry/node": "sentry", "@sentry/react": "sentry", "sentry-sdk": "sentry", "jquery": "jquery",
}
FRONTEND = {"nextjs", "react", "vue", "nuxt", "angular", "svelte", "sveltekit", "solid", "astro",
            "jquery", "streamlit", "electron", "react-native", "expo"}
TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs", "e2e", "cypress"}
TEST_FILE_RE = re.compile(r"(\.test\.|\.spec\.|_test\.|^test_.*\.py$)")


def list_files(root):
    """Project-relative POSIX paths. Uses git (respects .gitignore) when available."""
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root,
                             capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            files = [f for f in out.stdout.splitlines() if f]
            return [f for f in files if not set(f.split("/")[:-1]) & SKIP_DIRS], True
    except (OSError, subprocess.SubprocessError):
        pass
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip ignored dirs and nested git repos (clones of other projects)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not os.path.exists(os.path.join(dirpath, d, ".git"))]
        rel = os.path.relpath(dirpath, root)
        for n in filenames:
            files.append(n if rel == "." else f"{rel}/{n}".replace(os.sep, "/"))
    return files, False


def read(root, rel, limit=200_000):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def deps_of(root, rel):
    name = rel.rsplit("/", 1)[-1]
    text = read(root, rel)
    if name == "package.json":
        try:
            pj = json.loads(text)
        except ValueError:
            return set(), {}
        deps = set()
        for k in ("dependencies", "devDependencies", "peerDependencies"):
            deps |= set((pj.get(k) or {}).keys())
        return deps, pj.get("scripts") or {}
    # python and others: crude but deterministic token match against known names
    tokens = set(re.findall(r"[A-Za-z0-9_.\-@/]+", text.lower()))
    return {d for d in FRAMEWORKS if d in tokens}, {}


def git_remote(root):
    try:
        return subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def scan(root, threshold=150):
    root = os.path.realpath(root)
    files, is_git = list_files(root)
    source = [f for f in files if os.path.splitext(f)[1] in LANG]
    langs = Counter(LANG[os.path.splitext(f)[1]] for f in source)
    manifests = [{"path": f, "kind": MANIFESTS[f.rsplit("/", 1)[-1]]} for f in files
                 if f.rsplit("/", 1)[-1] in MANIFESTS]
    frameworks, scripts = set(), {}
    for m in manifests:
        deps, sc = deps_of(root, m["path"])
        frameworks |= {FRAMEWORKS[d] for d in deps if d in FRAMEWORKS}
        if sc:
            scripts[m["path"]] = sc
    locks = sorted({LOCKS[f.rsplit("/", 1)[-1]] for f in files if f.rsplit("/", 1)[-1] in LOCKS})
    test_files = [f for f in files if TEST_FILE_RE.search(f.rsplit("/", 1)[-1])
                  or set(f.split("/")[:-1]) & TEST_DIR_NAMES]
    test_dirs = sorted({"/".join(f.split("/")[:i + 1]) for f in test_files
                        for i, p in enumerate(f.split("/")[:-1]) if p in TEST_DIR_NAMES})[:20]
    instructions = sorted(f for f in files if not f.endswith(".DS_Store") and (f in INSTRUCTION_FILES or f.endswith("/CLAUDE.md")
                          or f.endswith("/AGENTS.md") or f.startswith((".claude/", ".cursor/rules/"))))
    root_lang = langs.most_common(1)[0][0] if langs else None

    # module candidates: dirs (depth <= 3) with own manifest, > threshold source files, or other language
    per_dir = Counter()
    lang_dir = {}
    for f in source:
        parts = f.split("/")[:-1]
        for i in range(1, min(len(parts), 3) + 1):
            d = "/".join(parts[:i])
            per_dir[d] += 1
            lang_dir.setdefault(d, Counter())[LANG[os.path.splitext(f)[1]]] += 1
    manifest_dirs = {m["path"].rsplit("/", 1)[0] for m in manifests if "/" in m["path"]}
    candidates = []
    for d in sorted(per_dir, key=lambda x: (x.count("/"), x)):
        if any(d.startswith(c["path"] + "/") for c in candidates):
            continue  # already covered by a parent module
        reasons = []
        if d in manifest_dirs:
            reasons.append("own manifest")
        if per_dir[d] > threshold and d.count("/") <= 1:
            reasons.append(f"{per_dir[d]} source files")
        dl = lang_dir[d].most_common(1)[0][0]
        if root_lang and dl != root_lang and per_dir[d] >= 10 and d.count("/") == 0:
            reasons.append(f"language {dl} differs from root {root_lang}")
        if reasons:
            candidates.append({"path": d, "source_files": per_dir[d], "language": dl, "reasons": reasons})

    remote = git_remote(root) if is_git else ""
    return {
        "root": root,
        "mode": "brownfield" if source else "greenfield",
        "is_git": is_git,
        "git_remote_host": re.sub(r"^(https?://|git@)([^/:]+).*$", r"\2", remote) if remote else None,
        "total_files": len(files),
        "source_files": len(source),
        "languages": dict(langs.most_common()),
        "primary_language": root_lang,
        "manifests": manifests,
        "package_managers": locks,
        "monorepo_markers": [m for m in MONOREPO if m in files],
        "frameworks": sorted(frameworks),
        "has_frontend": bool(frameworks & FRONTEND),
        "scripts": scripts,
        "test_files": len(test_files),
        "test_dirs": test_dirs,
        "instruction_files": instructions,
        "env_files": sorted(f for f in files if f.rsplit("/", 1)[-1].startswith(".env")),
        "top_level": sorted({f.split("/")[0] for f in files if "/" in f})[:40],
        "module_candidates": candidates[:15],
    }


def main(argv):
    root = next((a for a in argv if not a.startswith("--")), ".")
    threshold = int(argv[argv.index("--module-threshold") + 1]) if "--module-threshold" in argv else 150
    print(json.dumps(scan(root, threshold), indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
