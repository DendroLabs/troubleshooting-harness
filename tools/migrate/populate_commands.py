#!/usr/bin/env python3
"""Populate commands.db from curated JSON data and IOS-XR show command catalog."""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
ARCHIVED = REPO_ROOT / "archived-kb"

SHOW_COMMANDS_FILE = ARCHIVED / "agent-cisco-kb" / "all_show_commands_clean.txt"

DATA_DIRS = {
    "protocols": DATA / "protocols",
    "concepts": DATA / "concepts",
    "diagnostics": DATA / "diagnostics",
    "procedures": DATA / "procedures",
    "human-errors": DATA / "human-errors",
}


def _extract_commands_recursive(obj):
    """Walk any nested structure, yield every dict that has 'command' + 'os' keys."""
    if isinstance(obj, dict):
        if "command" in obj and "os" in obj and isinstance(obj["command"], str):
            yield obj
        for v in obj.values():
            yield from _extract_commands_recursive(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _extract_commands_recursive(item)


def _description(cmd):
    parts = []
    for key in ("confirms_if", "look_for", "purpose"):
        val = cmd.get(key)
        if val:
            parts.append(val)
    return "; ".join(parts) or None


def _version(cmd):
    vr = cmd.get("version_range", {})
    return vr.get("min", "*") or "*"


def _version_min(cmd):
    vr = cmd.get("version_range", {})
    v = vr.get("min", "*")
    return v if v != "*" else None


def _version_max(cmd):
    vr = cmd.get("version_range", {})
    v = vr.get("max", "*")
    return v if v != "*" else None


def _load_json_commands():
    """Extract commands from all JSON data directories."""
    rows = []
    for data_type, dir_path in DATA_DIRS.items():
        if not dir_path.exists():
            continue
        for path in sorted(dir_path.glob("*.json")):
            if path.name.startswith("_"):
                continue
            doc = json.loads(path.read_text())
            doc_id = path.stem
            context = f"{data_type}:{doc_id}"
            for cmd in _extract_commands_recursive(doc):
                rows.append((
                    cmd["os"],
                    _version(cmd),
                    _version_min(cmd),
                    _version_max(cmd),
                    None,  # platform
                    cmd["command"],
                    _description(cmd),
                    None,  # defaults
                    None,  # mode
                    context,
                ))
    return rows


def _load_show_commands():
    """Load IOS-XR show command catalog (syntax only, one per line)."""
    if not SHOW_COMMANDS_FILE.exists():
        return []
    rows = []
    for line in SHOW_COMMANDS_FILE.read_text().splitlines():
        syntax = line.strip()
        if not syntax:
            continue
        rows.append((
            "iosxr",
            "*",
            None,  # version_min
            None,  # version_max
            None,  # platform
            syntax,
            None,  # description
            None,  # defaults
            None,  # mode
            "iosxr-show-catalog",
        ))
    return rows


def populate(db_path: Path) -> dict:
    rows = _load_json_commands()
    json_count = len(rows)

    show_rows = _load_show_commands()
    show_count = len(show_rows)
    rows.extend(show_rows)

    conn = sqlite3.connect(str(db_path))
    conn.execute("DELETE FROM commands")
    conn.execute("DELETE FROM commands_fts")

    inserted = 0
    for row in rows:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO commands "
                "(os, version, version_min, version_max, platform, syntax, "
                "description, defaults, mode, context) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
            if conn.total_changes > inserted:
                inserted = conn.total_changes
        except sqlite3.IntegrityError:
            pass
    inserted = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]

    conn.commit()
    conn.close()
    return {"json_commands": json_count, "show_commands": show_count, "inserted": inserted}


if __name__ == "__main__":
    db = DATA / "db" / "commands.db"
    result = populate(db)
    print(f"commands.db: {result['inserted']} rows "
          f"({result['json_commands']} from JSON, {result['show_commands']} from IOS-XR catalog)")
