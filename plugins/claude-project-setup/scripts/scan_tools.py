"""Inventory installed/available plugins and MCP servers, then classify them for this project.

Usage:
  python3 scan_tools.py [PROJECT] [--scan scan.json] [--needs ui-testing,github] [--fixture tools.json]

Prints JSON. Writes nothing. Records names, scopes, status and token cost only:
never env values, headers or tokens.
Classes: REUSE (installed, fits a need) · ADD (not installed, fills a need)
         SKIP (installed, no need here) · CONFLICT (>1 enabled in an exclusive capability)
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "catalog", "integrations.json")
MCP_LINE = re.compile(r"^([\w.@-]+): (.+?) - (.+)$")
TOKENS = re.compile(r"Always-on:\s*~?([\d.]+)(k?)\s*tok", re.I)
DESC = re.compile(r"^\s*Description:\s*(.+)$", re.M)


def run(args, timeout=120):
    if not shutil.which(args[0]):
        return None
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def live_inventory():
    inv = {"cli": bool(shutil.which("claude")), "installed": [], "available": [], "mcp": []}
    raw = run(["claude", "plugin", "list", "--json", "--available"])
    if raw:
        try:
            d = json.loads(raw)
            inv["installed"] = d.get("installed", []) if isinstance(d, dict) else d
            inv["available"] = d.get("available", []) if isinstance(d, dict) else []
        except ValueError:
            pass
    for p in inv["installed"]:
        details = run(["claude", "plugin", "details", p.get("id", "")]) or ""
        m, dm = TOKENS.search(details), DESC.search(details)
        p["always_on_tokens"] = int(float(m.group(1)) * (1000 if m.group(2) else 1)) if m else None
        p["description"] = p.get("description") or (dm.group(1).strip() if dm else "")
    for line in (run(["claude", "mcp", "list"]) or "").splitlines():
        m = MCP_LINE.match(line.strip())
        if m:
            inv["mcp"].append({"name": m.group(1), "status": m.group(3).strip(), "source": "cli"})
    return inv


def project_config(project):
    out = {"mcp_json": [], "enabled_plugins": {}}
    try:
        with open(os.path.join(project, ".mcp.json"), encoding="utf-8") as f:
            out["mcp_json"] = sorted((json.load(f).get("mcpServers") or {}).keys())
    except (OSError, ValueError):
        pass
    try:
        with open(os.path.join(project, ".claude", "settings.json"), encoding="utf-8") as f:
            out["enabled_plugins"] = json.load(f).get("enabledPlugins") or {}
    except (OSError, ValueError):
        pass
    return out


def auto_needs(scan, catalog):
    needs = set()
    for cap, spec in catalog["capabilities"].items():
        cond = spec.get("auto_if")
        if (cond == "has_frontend" and scan.get("has_frontend")) \
                or (cond == "has_dependencies" and scan.get("manifests")) \
                or (cond == "remote_github" and scan.get("git_remote_host") == "github.com") \
                or (cond and cond.startswith("framework:") and cond.split(":", 1)[1] in scan.get("frameworks", [])):
            needs.add(cap)
    return needs


def capability_of(item, catalog):
    known = catalog["known_plugins"].get(item.get("id") or item.get("name", ""))
    if known:
        return known["capability"]
    text = " ".join(str(item.get(k, "")) for k in ("id", "name", "description")).lower()
    for cap, spec in catalog["capabilities"].items():
        if any(k in text for k in spec["keywords"]):
            return cap
    return None


def classify(inv, proj, needs, catalog):
    rows = []
    configured_mcp = {m["name"] for m in inv["mcp"]} | set(proj["mcp_json"])
    covered = set()
    for p in inv["installed"]:
        cap = capability_of(p, catalog)
        row = {"kind": "plugin", "id": p.get("id"), "capability": cap, "scope": p.get("scope"),
               "always_on_tokens": p.get("always_on_tokens")}
        rows.append(row)
        if cap in needs:
            row.update(cls="REUSE", reason=f"installed and covers {cap}")
            covered.add(cap)
        else:
            row.update(cls="SKIP", reason=("no matching need for this project" if cap is None
                       else f"provides {cap}, not needed here")
                       + ("; still on via user scope: add to plan plugins.disable to turn it off here"
                          if p.get("scope") == "user" and p.get("enabled", True) else ""))
    for cap, spec in catalog["capabilities"].items():  # exclusive capabilities: >1 enabled -> CONFLICT
        enabled = [r for r in rows if r["capability"] == cap and r["kind"] == "plugin"
                   and next((p for p in inv["installed"] if p.get("id") == r["id"]), {}).get("enabled", True)]
        if spec.get("exclusive") and len(enabled) > 1:
            for r in enabled:
                r.update(cls="CONFLICT", reason=f"{len(enabled)} enabled plugins provide {cap}; pick one")
    for name, entry in catalog["mcp_servers"].items():
        cap = entry["capability"]
        if name in configured_mcp:
            rows.append({"kind": "mcp", "id": name, "capability": cap,
                         "cls": "REUSE" if cap in needs else "SKIP",
                         "reason": "already configured" + ("" if cap in needs else "; not needed here")})
            covered.add(cap)
        elif cap in needs and cap not in covered:
            rows.append({"kind": "mcp", "id": name, "capability": cap, "cls": "ADD",
                         "reason": f"fills {cap}", "env": entry.get("env", []), "notes": entry.get("notes", "")})
            covered.add(cap)
    for name in sorted(configured_mcp - set(catalog["mcp_servers"])):
        status = next((m["status"] for m in inv["mcp"] if m["name"] == name), "project .mcp.json")
        rows.append({"kind": "mcp", "id": name, "capability": None, "cls": "SKIP",
                     "reason": f"configured ({status}); not in catalog. Keep it only if a requirement needs it"})
    for a in inv["available"]:  # marketplace plugins not installed that fill an uncovered need
        cap = capability_of(a, catalog)
        if cap in needs and cap not in covered:
            rows.append({"kind": "plugin", "id": a.get("id") or a.get("name"), "capability": cap,
                         "cls": "ADD", "reason": f"available in a marketplace; fills {cap}"})
            covered.add(cap)
    return rows, sorted(needs - covered)


def main(argv):
    flags = {a: argv[i + 1] for i, a in enumerate(argv) if a.startswith("--") and i + 1 < len(argv)}
    project = next((a for a in argv if not a.startswith("--") and a not in flags.values()), ".")
    with open(CATALOG, encoding="utf-8") as f:
        catalog = json.load(f)
    if "--fixture" in flags:
        with open(flags["--fixture"], encoding="utf-8") as f:
            inv = json.load(f)
    else:
        inv = live_inventory()
    scan = {}
    if "--scan" in flags:
        with open(flags["--scan"], encoding="utf-8") as f:
            scan = json.load(f)
    needs = auto_needs(scan, catalog) | {n.strip() for n in flags.get("--needs", "").split(",") if n.strip()}
    proj = project_config(project)
    rows, unmet = classify(inv, proj, needs, catalog)
    print(json.dumps({
        "claude_cli": inv.get("cli", True),
        "needs": sorted(needs),
        "unmet_needs": unmet,
        "project": proj,
        "total_always_on_tokens": sum(r.get("always_on_tokens") or 0 for r in rows if r["kind"] == "plugin"),
        "items": rows,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
