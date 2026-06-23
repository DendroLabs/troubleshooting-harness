#!/usr/bin/env python3
"""Populate caveats.db from bug-ids-for-lookup.txt."""

import json
import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
ARCHIVED = REPO_ROOT / "archived-kb"

BUG_IDS_FILE = ARCHIVED / "agent-cisco-kb" / "bug-ids-for-lookup.txt"
# Curated caveats committed in the repo (reproducible without archived-kb).
CAVEATS_DIR = DATA / "caveats"

SECTION_RE = re.compile(r"^===\s+(\w+)\s+\(\d+\s+bugs?\)\s+===$")
ENTRY_RE = re.compile(r"^(CSC\w+)\s*\|\s*(\S+)\s*\|\s*(\w+)\s*\|\s*(.+)$")


def _parse_bug_ids(path: Path) -> list[dict]:
    if not path.exists():
        return []

    entries = []
    current_os = None
    current_entry = None

    for line in path.read_text().splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue

        section = SECTION_RE.match(line_stripped)
        if section:
            current_os = section.group(1).lower()
            continue

        entry = ENTRY_RE.match(line_stripped)
        if entry:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                "os": current_os,
                "csc_id": entry.group(1),
                "version": entry.group(2),
                "status": entry.group(3),
                "headline": entry.group(4).strip(),
            }
        elif current_entry and not line_stripped.startswith("==="):
            current_entry["headline"] += " " + line_stripped

    if current_entry:
        entries.append(current_entry)

    return entries


def _load_curated_caveats() -> list[dict]:
    """Load committed curated caveats from data/caveats/*.json (full column set)."""
    rows = []
    if not CAVEATS_DIR.exists():
        return rows
    for path in sorted(CAVEATS_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        doc = json.loads(path.read_text())
        for c in doc.get("caveats", []):
            rows.append(c)
    return rows


def populate(db_path: Path) -> int:
    entries = _parse_bug_ids(BUG_IDS_FILE)
    curated = _load_curated_caveats()

    conn = sqlite3.connect(str(db_path))
    conn.execute("DELETE FROM caveats")
    conn.execute("DELETE FROM caveats_fts")

    for c in curated:
        conn.execute(
            "INSERT OR IGNORE INTO caveats "
            "(os, csc_id, headline, description, severity, "
            "affected_versions, affected_platforms, affected_pids, "
            "fixed_in, keywords) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                c["os"],
                c.get("csc_id"),
                c["headline"],
                c.get("description"),
                c.get("severity"),
                c.get("affected_versions"),
                c.get("affected_platforms"),
                c.get("affected_pids"),
                c.get("fixed_in"),
                c.get("keywords"),
            ),
        )

    for e in entries:
        fixed_in = e["version"] if e["status"] == "resolved" else None
        conn.execute(
            "INSERT OR IGNORE INTO caveats "
            "(os, csc_id, headline, description, severity, "
            "affected_versions, affected_platforms, affected_pids, "
            "fixed_in, keywords) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                e["os"],
                e["csc_id"],
                e["headline"],
                None,  # description
                None,  # severity
                e["version"],
                None,  # affected_platforms
                None,  # affected_pids
                fixed_in,
                None,  # keywords
            ),
        )

    inserted = conn.execute("SELECT COUNT(*) FROM caveats").fetchone()[0]
    conn.commit()
    conn.close()
    return inserted


if __name__ == "__main__":
    db = DATA / "db" / "caveats.db"
    count = populate(db)
    print(f"caveats.db: {count} rows from {BUG_IDS_FILE.name}")
