import sqlite3
from pathlib import Path


def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict]:
    cols = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _parse_version(v: str):
    """Parse a dotted/numeric version (e.g. '10.4', '202511') into an int tuple,
    or None if it isn't purely numeric (so callers fall back to string compare)."""
    parts = []
    for p in v.replace("-", ".").split("."):
        if p.isdigit():
            parts.append(int(p))
        else:
            return None
    return tuple(parts) if parts else None


def _ver_cmp(a: str, b: str) -> int:
    pa, pb = _parse_version(a), _parse_version(b)
    if pa is not None and pb is not None:
        return (pa > pb) - (pa < pb)
    return (a > b) - (a < b)


def _version_matches(query_version: str, row: dict) -> bool:
    """True if the row's applicability covers the requested version.

    A row applies when it is universal ('*'), an exact version hit, or the
    requested version falls within the row's [version_min, version_max] range.
    """
    rv = row.get("version") or "*"
    if rv == "*" or query_version == "*":
        return True
    if rv == query_version:
        return True
    vmin = row.get("version_min")
    vmax = row.get("version_max")
    if not vmin:
        return False
    if _ver_cmp(query_version, vmin) < 0:
        return False
    if vmax and vmax != "*" and _ver_cmp(query_version, vmax) > 0:
        return False
    return True


def _version_rank(query_version: str, row: dict) -> int:
    """Sort key: exact-version row first, then ranged, then universal ('*')."""
    rv = row.get("version") or "*"
    if rv == query_version:
        return 0
    if rv == "*":
        return 2
    return 1


class CommandQuery:

    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def exact_match(self, syntax: str, os: str, version: str) -> list[dict]:
        rows = self.syntax_rows(syntax, os)
        rows = [r for r in rows if _version_matches(version, r)]
        rows.sort(key=lambda r: _version_rank(version, r))
        return rows

    def prefix_match(self, prefix: str, os: str, version: str,
                     limit: int = 10) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM commands "
            "WHERE os = ? AND LOWER(syntax) LIKE LOWER(? || '%')",
            (os, prefix),
        )
        rows = [r for r in _rows_to_dicts(cur) if _version_matches(version, r)]
        rows.sort(key=lambda r: (_version_rank(version, r), r["syntax"]))
        return rows[:limit]

    def syntax_rows(self, syntax: str, os: str) -> list[dict]:
        """All rows whose syntax exactly matches, any version (for version-mismatch messaging)."""
        cur = self._conn.execute(
            "SELECT * FROM commands WHERE LOWER(syntax) = LOWER(?) AND os = ?",
            (syntax, os),
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
