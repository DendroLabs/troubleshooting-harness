from harness.src.tools.base import ToolContext, wrap_result


class CommandTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def validate_command(self, command: str, os: str, version: str) -> dict:
        result = self._ctx.cmd_validator.validate(command, os, version)
        return wrap_result(
            "validate_command",
            {"os": os, "version": version},
            result.to_dict(),
            kb_coverage=result.kb_coverage,
        )

    def search_commands(self, query: str, os: str, version: str,
                        limit: int = 20) -> dict:
        rows = self._ctx.cmd_query.fts_search(query, os=os, limit=limit)
        filtered = [
            r for r in rows
            if r.get("version") in (version, "*")
        ]
        kb = "indexed" if filtered else "not_indexed"
        return wrap_result(
            "search_commands",
            {"os": os, "version": version},
            {"commands": filtered, "total": len(filtered)},
            kb_coverage=kb,
        )
