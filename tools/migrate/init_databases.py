#!/usr/bin/env python3
"""Initialize TSH SQLite databases from schema.sql sections.

Usage: python init_databases.py [--db-dir ../../data/db]

Reads schema.sql and applies each section to the correct database.
Safe to re-run — uses IF NOT EXISTS throughout.
"""

import argparse
import re
import sqlite3
from pathlib import Path

DB_DIR_DEFAULT = Path(__file__).parent.parent.parent / "data" / "db"

SECTION_MAP = {
    "commands.db": "commands",
    "caveats.db": "caveats",
    "field_notices.db": "field_notices",  # mapped from field-notices.db
    "platforms.db": "platforms",
}

DB_FILE_MAP = {
    "commands": "commands.db",
    "caveats": "caveats.db",
    "field_notices": "field-notices.db",
    "platforms": "platforms.db",
}


def parse_sections(schema_path: Path) -> dict[str, str]:
    text = schema_path.read_text()
    sections = {}
    current_section = None
    current_lines = []

    for line in text.splitlines():
        header_match = re.match(r"^-+\s*$", line)
        section_match = re.match(r"^-- (\w+)\.db", line)

        if section_match:
            if current_section:
                sections[current_section] = "\n".join(current_lines)
            current_section = section_match.group(1)
            current_lines = []
        elif current_section:
            current_lines.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_lines)

    # metadata section applies to all databases
    metadata_match = re.search(
        r"-- metadata table.*?$(.+)", text, re.MULTILINE | re.DOTALL
    )
    metadata_sql = metadata_match.group(1).strip() if metadata_match else ""

    return sections, metadata_sql


def init_db(db_path: Path, ddl: str, metadata_sql: str):
    conn = sqlite3.connect(str(db_path))
    conn.executescript(ddl)
    if metadata_sql:
        conn.executescript(metadata_sql)
    conn.close()
    print(f"  Initialized {db_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Initialize TSH SQLite databases")
    parser.add_argument(
        "--db-dir", type=Path, default=DB_DIR_DEFAULT, help="Database directory"
    )
    args = parser.parse_args()

    schema_path = Path(__file__).parent.parent.parent / "data" / "db" / "schema.sql"
    if not schema_path.exists():
        print(f"Error: schema.sql not found at {schema_path}")
        return 1

    sections, metadata_sql = parse_sections(schema_path)

    for section_key, ddl in sections.items():
        db_filename = DB_FILE_MAP.get(section_key, f"{section_key}.db")
        db_path = args.db_dir / db_filename
        init_db(db_path, ddl, metadata_sql)

    print("All databases initialized.")
    return 0


if __name__ == "__main__":
    exit(main())
