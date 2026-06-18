from harness.src.retrieval.scope_filter import Scope, filter_scoped
from harness.src.tools.base import ToolContext, wrap_result


class ProcedureTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_procedure(self, procedure_id: str, os: str,
                      version: str) -> dict:
        doc = self._ctx.loader.get_procedure(procedure_id)
        if doc is None:
            return wrap_result(
                "get_procedure",
                {"procedure_id": procedure_id, "os": os, "version": version},
                None,
                kb_coverage="not_indexed",
            )

        scope = Scope(os=os, version=version)
        steps = []
        for step in doc.get("steps", []):
            filtered_step = {
                "step_id": step.get("step_id"),
                "step": step.get("step"),
                "action": step.get("action"),
                "warning": step.get("warning"),
                "notes": step.get("notes"),
            }
            filtered_step["commands"] = self._validate_commands(
                filter_scoped(step.get("commands", []), scope), os, version
            )
            verification = step.get("verification", [])
            if verification:
                filtered_step["verification"] = filter_scoped(verification, scope)
            steps.append(filtered_step)

        data = {
            "procedure_id": doc.get("procedure_id"),
            "procedure_name": doc.get("procedure_name"),
            "category": doc.get("category"),
            "risk_level": doc.get("risk_level"),
            "purpose": doc.get("purpose"),
            "steps": steps,
            "prerequisites": doc.get("prerequisites", []),
            "warnings": doc.get("warnings", []),
            "rollback": doc.get("rollback", []),
        }
        return wrap_result(
            "get_procedure",
            {"procedure_id": procedure_id, "os": os, "version": version},
            data,
        )

    def _validate_commands(self, commands: list[dict], os: str,
                           version: str) -> list[dict]:
        result = []
        for cmd in commands:
            syntax = cmd.get("command", "")
            validation = self._ctx.cmd_validator.validate(syntax, os, version)
            entry = dict(cmd)
            entry["validation"] = validation.to_dict()
            result.append(entry)
        return result
