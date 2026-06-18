#!/usr/bin/env python3
"""Orchestrate SQLite database population for TSH.

Usage: cd tools/migrate && python3 build_sqlite.py

Re-initializes all databases, then populates commands, caveats, and platforms.
Safe to re-run — drops and recreates all data each time.
"""

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
DB_DIR = DATA / "db"
SCHEMA_SQL = DB_DIR / "schema.sql"


def _reinit_db(db_path: Path):
    """Drop all user tables and recreate from schema.sql sections."""
    conn = sqlite3.connect(str(db_path))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]
    for t in tables:
        if t.endswith("_fts") or t.endswith("_content") or t.endswith("_segments") \
                or t.endswith("_segdir") or t.endswith("_docsize") or t.endswith("_stat") \
                or t.endswith("_idx") or t.endswith("_data") or t.endswith("_config"):
            continue
        try:
            conn.execute(f"DROP TABLE IF EXISTS [{t}]")
        except Exception:
            pass
    conn.close()

    import init_databases
    init_databases.init_db(db_path, *_get_section(db_path.name))


def _get_section(db_filename: str):
    """Parse schema.sql and return (ddl, metadata_sql) for a given db file."""
    import init_databases
    sections, metadata_sql = init_databases.parse_sections(SCHEMA_SQL)
    key_map = {"commands.db": "commands", "caveats.db": "caveats",
               "field-notices.db": "field_notices", "platforms.db": "platforms"}
    key = key_map.get(db_filename, db_filename.replace(".db", ""))
    return sections.get(key, ""), metadata_sql


def main() -> int:
    import populate_commands
    import populate_caveats
    import populate_platforms

    dbs = {
        "commands.db": DB_DIR / "commands.db",
        "caveats.db": DB_DIR / "caveats.db",
        "field-notices.db": DB_DIR / "field-notices.db",
        "platforms.db": DB_DIR / "platforms.db",
    }

    for name, path in dbs.items():
        _reinit_db(path)

    cmd_result = populate_commands.populate(dbs["commands.db"])
    print(f"commands.db: {cmd_result['inserted']} rows "
          f"({cmd_result['json_commands']} from JSON, "
          f"{cmd_result['show_commands']} from IOS-XR catalog)")

    cav_count = populate_caveats.populate(dbs["caveats.db"])
    print(f"caveats.db: {cav_count} rows")

    plat_result = populate_platforms.populate(dbs["platforms.db"])
    print(f"platforms.db: {plat_result['platforms']} platforms, "
          f"{plat_result['ports']} port groups")

    print(f"field-notices.db: 0 rows (no source data)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
