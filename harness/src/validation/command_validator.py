from dataclasses import dataclass, field
from enum import Enum

from harness.src.retrieval.sqlite_query import CommandQuery


class ValidationStatus(Enum):
    EXACT = "exact"
    PREFIX = "prefix"
    FTS = "fts"
    NOT_FOUND = "not_found"


@dataclass
class ValidationResult:
    status: ValidationStatus
    matched_syntax: str | None = None
    description: str | None = None
    suggestions: list[str] = field(default_factory=list)
    kb_coverage: str = "indexed"
    warning: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "matched_syntax": self.matched_syntax,
            "description": self.description,
            "suggestions": self.suggestions,
            "kb_coverage": self.kb_coverage,
            "warning": self.warning,
        }


class CommandValidator:

    def __init__(self, cmd_query: CommandQuery):
        self._q = cmd_query

    def validate(self, command: str, os: str, version: str) -> ValidationResult:
        syntax = command.strip()

        rows = self._q.exact_match(syntax, os, version)
        if rows:
            warning = None
            if rows[0]["version"] == "*" and version != "*":
                warning = (
                    f"Validated against universal entry; "
                    f"not confirmed for version {version}"
                )
            return ValidationResult(
                status=ValidationStatus.EXACT,
                matched_syntax=rows[0]["syntax"],
                description=rows[0].get("description"),
                kb_coverage="indexed",
                warning=warning,
            )

        rows = self._q.prefix_match(syntax, os, version, limit=5)
        if rows:
            return ValidationResult(
                status=ValidationStatus.PREFIX,
                matched_syntax=rows[0]["syntax"],
                description=rows[0].get("description"),
                suggestions=[r["syntax"] for r in rows],
                kb_coverage="indexed",
                warning="Matched as command prefix; confirm full syntax",
            )

        rows = self._q.fts_search(syntax, os=os, limit=5)
        suggestions = [r["syntax"] for r in rows]

        if rows:
            return ValidationResult(
                status=ValidationStatus.FTS,
                suggestions=suggestions,
                kb_coverage="not_indexed",
                warning=(
                    f"No exact match for os={os}, version={version}. "
                    f"Closest FTS matches shown in suggestions."
                ),
            )

        return ValidationResult(
            status=ValidationStatus.NOT_FOUND,
            kb_coverage="not_indexed",
            warning=f"Command not found in KB for os={os}, version={version}.",
        )
