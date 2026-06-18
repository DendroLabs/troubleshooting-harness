from dataclasses import dataclass
from pathlib import Path

from harness.src.retrieval.json_loader import JsonLoader
from harness.src.retrieval.resolver import DefIdResolver
from harness.src.retrieval.sqlite_query import (
    CaveatQuery,
    CommandQuery,
    FieldNoticeQuery,
    PlatformQuery,
)
from harness.src.validation.command_validator import CommandValidator
from harness.src.cases.case_manager import CaseManager


class PlatformResolver:

    def __init__(self, platform_query: PlatformQuery):
        self._pq = platform_query

    def resolve_family(self, platform_id: str) -> str | None:
        return self._pq.get_family(platform_id)


@dataclass
class ToolContext:
    loader: JsonLoader
    resolver: DefIdResolver
    platform_resolver: PlatformResolver
    cmd_validator: CommandValidator
    cmd_query: CommandQuery
    caveat_query: CaveatQuery
    platform_query: PlatformQuery
    field_notice_query: FieldNoticeQuery
    case_manager: CaseManager


def build_context(repo_root: Path) -> ToolContext:
    data_dir = repo_root / "data"
    db_dir = data_dir / "db"
    cases_dir = repo_root / "harness" / "cases"

    loader = JsonLoader(data_dir)
    cmd_query = CommandQuery(db_dir / "commands.db")
    caveat_query = CaveatQuery(db_dir / "caveats.db")
    platform_query = PlatformQuery(db_dir / "platforms.db")
    field_notice_query = FieldNoticeQuery(db_dir / "field-notices.db")

    return ToolContext(
        loader=loader,
        resolver=DefIdResolver(loader),
        platform_resolver=PlatformResolver(platform_query),
        cmd_validator=CommandValidator(cmd_query),
        cmd_query=cmd_query,
        caveat_query=caveat_query,
        platform_query=platform_query,
        field_notice_query=field_notice_query,
        case_manager=CaseManager(cases_dir),
    )


def wrap_result(source_tool: str, scope: dict, data, kb_coverage: str = "indexed") -> dict:
    return {
        "kb_coverage": kb_coverage,
        "source_tool": source_tool,
        "scope": scope,
        "data": data,
    }
