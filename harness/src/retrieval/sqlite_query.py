import sqlite3
from pathlib import Path


def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


class CommandQuery:

    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def exact_match(self, syntax: str, os: str, version: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM commands "
            "WHERE LOWER(syntax) = LOWER(?) AND os = ? AND version IN (?, '*') "
            "ORDER BY CASE WHEN version = '*' THEN 1 ELSE 0 END, version DESC",
            (syntax, os, version),
        )
        return _rows_to_dicts(cur)

    def prefix_match(self, prefix: str, os: str, version: str,
                     limit: int = 10) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM commands "
            "WHERE os = ? AND version IN (?, '*') AND LOWER(syntax) LIKE LOWER(? || '%') "
            "ORDER BY syntax LIMIT ?",
            (os, version, prefix, limit),
        )
        return _rows_to_dicts(cur)

    def fts_search(self, query: str, os: str | None = None,
                   limit: int = 20) -> list[dict]:
        fts_query = _sanitize_fts(query)
        if not fts_query:
            return []
        if os:
            cur = self._conn.execute(
                "SELECT c.* FROM commands_fts f "
                "JOIN commands c ON c.id = f.rowid "
                "WHERE f.commands_fts MATCH ? AND c.os = ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, os, limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT c.* FROM commands_fts f "
                "JOIN commands c ON c.id = f.rowid "
                "WHERE f.commands_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, limit),
            )
        return _rows_to_dicts(cur)

    def close(self):
        self._conn.close()


class CaveatQuery:

    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def fts_search(self, query: str, os: str | None = None,
                   limit: int = 10) -> list[dict]:
        fts_query = _sanitize_fts(query)
        if not fts_query:
            return []
        if os:
            cur = self._conn.execute(
                "SELECT c.* FROM caveats_fts f "
                "JOIN caveats c ON c.id = f.rowid "
                "WHERE f.caveats_fts MATCH ? AND c.os = ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, os, limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT c.* FROM caveats_fts f "
                "JOIN caveats c ON c.id = f.rowid "
                "WHERE f.caveats_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, limit),
            )
        return _rows_to_dicts(cur)

    def by_csc_id(self, csc_id: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM caveats WHERE csc_id = ?", (csc_id,)
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None

    def by_os(self, os: str, severity: str | None = None,
              limit: int = 50) -> list[dict]:
        if severity:
            cur = self._conn.execute(
                "SELECT * FROM caveats WHERE os = ? AND severity = ? LIMIT ?",
                (os, severity, limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT * FROM caveats WHERE os = ? LIMIT ?",
                (os, limit),
            )
        return _rows_to_dicts(cur)

    def close(self):
        self._conn.close()


class PlatformQuery:

    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def by_id(self, platform_id: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM platforms WHERE platform_id = ?", (platform_id,)
        )
        rows = _rows_to_dicts(cur)
        return rows[0] if rows else None

    def by_os(self, os: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM platforms WHERE os = ?", (os,)
        )
        return _rows_to_dicts(cur)

    def by_family(self, family: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM platforms WHERE platform_family = ?", (family,)
        )
        return _rows_to_dicts(cur)

    def ports(self, platform_id: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM platform_ports WHERE platform_id = ?", (platform_id,)
        )
        return _rows_to_dicts(cur)

    def get_family(self, platform_id: str) -> str | None:
        cur = self._conn.execute(
            "SELECT platform_family FROM platforms WHERE platform_id = ?",
            (platform_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def close(self):
        self._conn.close()


class FieldNoticeQuery:

    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def fts_search(self, query: str, os: str | None = None,
                   limit: int = 10) -> list[dict]:
        fts_query = _sanitize_fts(query)
        if not fts_query:
            return []
        if os:
            cur = self._conn.execute(
                "SELECT f2.* FROM field_notices_fts f "
                "JOIN field_notices f2 ON f2.id = f.rowid "
                "WHERE f.field_notices_fts MATCH ? AND f2.os = ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, os, limit),
            )
        else:
            cur = self._conn.execute(
                "SELECT f2.* FROM field_notices_fts f "
                "JOIN field_notices f2 ON f2.id = f.rowid "
                "WHERE f.field_notices_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, limit),
            )
        return _rows_to_dicts(cur)

    def close(self):
        self._conn.close()


def _sanitize_fts(query: str) -> str:
    cleaned = []
    for ch in query:
        if ch.isalnum() or ch in (" ", "-", "_"):
            cleaned.append(ch)
    result = "".join(cleaned).strip()
    if not result:
        return ""
    terms = result.split()
    return " ".join(terms)
