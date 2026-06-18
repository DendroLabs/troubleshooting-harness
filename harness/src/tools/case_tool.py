from harness.src.tools.base import ToolContext, wrap_result


class CaseTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def open_case(self, symptom: str, os: str, version: str,
                  platform: str | None = None) -> dict:
        state = self._ctx.case_manager.create(symptom, os, version, platform)
        return wrap_result(
            "open_case",
            {"os": os, "version": version},
            state,
        )

    def get_case(self, case_id: str) -> dict:
        state = self._ctx.case_manager.read(case_id)
        if state is None:
            return wrap_result("get_case", {}, None, kb_coverage="not_indexed")
        return wrap_result("get_case", {}, state)

    def advance_phase(self, case_id: str, current_phase: str,
                      output: str) -> dict:
        result = self._ctx.case_manager.advance(case_id, current_phase, output)
        if "error" in result:
            return wrap_result(
                "advance_phase", {"case_id": case_id},
                result, kb_coverage="indexed",
            )
        return wrap_result("advance_phase", {"case_id": case_id}, result)

    def close_case(self, case_id: str, resolution: str) -> dict:
        result = self._ctx.case_manager.close(case_id, resolution)
        return wrap_result("close_case", {"case_id": case_id}, result)

    def list_cases(self) -> dict:
        cases = self._ctx.case_manager.list_cases()
        return wrap_result("list_cases", {}, {"cases": cases})
