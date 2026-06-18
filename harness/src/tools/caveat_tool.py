from harness.src.tools.base import ToolContext, wrap_result


class CaveatTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def search_caveats(self, query: str, os: str,
                       version: str | None = None,
                       severity: str | None = None,
                       limit: int = 10) -> dict:
        if query:
            rows = self._ctx.caveat_query.fts_search(query, os=os, limit=limit)
        else:
            rows = self._ctx.caveat_query.by_os(os, severity=severity, limit=limit)

        results = []
        for row in rows:
            entry = dict(row)
            entry["match_confidence"] = "possible_match"
            entry["warning"] = None
            if version and row.get("affected_versions"):
                if version in row["affected_versions"]:
                    entry["match_confidence"] = "version_match"
                else:
                    entry["warning"] = (
                        f"Version {version} not in affected_versions "
                        f"'{row['affected_versions']}'. "
                        f"Flag as 'possible regression', not confirmed bug."
                    )
            results.append(entry)

        kb = "indexed" if results else "not_indexed"
        return wrap_result(
            "search_caveats",
            {"os": os, "version": version},
            {"caveats": results, "total": len(results)},
            kb_coverage=kb,
        )
