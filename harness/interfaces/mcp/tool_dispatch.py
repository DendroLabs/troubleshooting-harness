from harness.src.tools.base import ToolContext
from harness.src.tools.protocol_tool import ProtocolTool
from harness.src.tools.command_tool import CommandTool
from harness.src.tools.caveat_tool import CaveatTool
from harness.src.tools.platform_tool import PlatformTool
from harness.src.tools.diagnostic_tool import DiagnosticTool
from harness.src.tools.procedure_tool import ProcedureTool
from harness.src.tools.human_error_tool import HumanErrorTool
from harness.src.tools.case_tool import CaseTool
from harness.src.tools.grounding_tool import GroundingTool
from harness.src.tools.interpretation_rule_tool import InterpretationRuleTool


def build_dispatch(ctx: ToolContext) -> dict[str, callable]:
    protocol = ProtocolTool(ctx)
    command = CommandTool(ctx)
    caveat = CaveatTool(ctx)
    platform = PlatformTool(ctx)
    diagnostic = DiagnosticTool(ctx)
    procedure = ProcedureTool(ctx)
    human_error = HumanErrorTool(ctx)
    case = CaseTool(ctx)
    grounding = GroundingTool(ctx)
    interp = InterpretationRuleTool(ctx)

    return {
        "get_protocol": protocol.get_protocol,
        "validate_command": command.validate_command,
        "search_commands": command.search_commands,
        "search_caveats": caveat.search_caveats,
        "get_platform": platform.get_platform,
        "compare_platforms": platform.compare_platforms,
        "get_scalability": platform.get_scalability,
        "get_diagnostic_tree": diagnostic.get_diagnostic_tree,
        "get_procedure": procedure.get_procedure,
        "get_human_error": human_error.get_human_error,
        "search_human_errors": human_error.search_human_errors,
        "open_case": case.open_case,
        "get_case": case.get_case,
        "advance_phase": case.advance_phase,
        "check_kb_coverage": grounding.check_kb_coverage,
        "get_best_practices": grounding.get_best_practices,
        "get_interpretation_rule": interp.get_interpretation_rule,
        "search_interpretation_rules": interp.search_interpretation_rules,
    }
