#!/usr/bin/env python3
"""TSH — Network Troubleshooting Harness CLI."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from harness.src.tools.base import build_context
from harness.src.tools.case_tool import CaseTool
from harness.interfaces.mcp.tool_dispatch import build_dispatch
from harness.interfaces.cli.formatters import format_result


def build_parser() -> argparse.ArgumentParser:
    fmt = argparse.ArgumentParser(add_help=False)
    fmt.add_argument("--format", choices=["full", "compact", "minimal"], default="full",
                     help="Output format (default: full)")

    p = argparse.ArgumentParser(prog="tsh", description="TSH Network Troubleshooting Harness",
                                parents=[fmt])
    sub = p.add_subparsers(dest="command", required=True)

    # --- query ---
    query = sub.add_parser("query", help="Query the knowledge base")
    qsub = query.add_subparsers(dest="query_type", required=True)

    qp = qsub.add_parser("protocol", parents=[fmt], help="Get protocol/concept definition")
    qp.add_argument("id", help="Protocol ID (e.g. bgp-4, ospfv2)")
    qp.add_argument("--os", required=True)
    qp.add_argument("--version", required=True)
    qp.add_argument("--platform", default=None)
    qp.add_argument("--asic-family", default=None)
    qp.add_argument("--no-def-refs", action="store_true", help="Exclude resolved def_refs")

    qpl = qsub.add_parser("platform", parents=[fmt], help="Get platform hardware details")
    qpl.add_argument("id", help="Platform ID (e.g. n93180yc-fx3)")

    qs = qsub.add_parser("scalability", parents=[fmt], help="Get scalability limits")
    qs.add_argument("family", help="Platform family (e.g. nexus-9300)")
    qs.add_argument("--os", required=True)
    qs.add_argument("--version", required=True)

    qd = qsub.add_parser("diagnostic", parents=[fmt], help="Get diagnostic decision tree")
    qd.add_argument("id", help="Tree ID (e.g. bgp-not-establishing)")
    qd.add_argument("--os", required=True)
    qd.add_argument("--version", required=True)

    qpr = qsub.add_parser("procedure", parents=[fmt], help="Get operational procedure")
    qpr.add_argument("id", help="Procedure ID (e.g. software-install-nxos)")
    qpr.add_argument("--os", required=True)
    qpr.add_argument("--version", required=True)

    qhe = qsub.add_parser("human-error", parents=[fmt], help="Get operator mistake pattern")
    qhe.add_argument("id", help="Human error ID")
    qhe.add_argument("--os", required=True)

    qbp = qsub.add_parser("best-practices", parents=[fmt], help="Get best practices index")
    qbp.add_argument("--os", required=True)

    qir = qsub.add_parser("interpretation-rule", parents=[fmt], help="Get interpretation rule")
    qir.add_argument("id", help="Rule ID (e.g. interface-crc-counters-without-clearing)")
    qir.add_argument("--os", required=True)

    # --- validate ---
    val = sub.add_parser("validate", parents=[fmt], help="Validate a CLI command")
    val.add_argument("cmd", help="Command string to validate")
    val.add_argument("--os", required=True)
    val.add_argument("--version", required=True)

    # --- search ---
    search = sub.add_parser("search", help="Search the knowledge base")
    ssub = search.add_subparsers(dest="search_type", required=True)

    sc = ssub.add_parser("commands", parents=[fmt], help="Full-text search commands")
    sc.add_argument("query", help="Search terms")
    sc.add_argument("--os", required=True)
    sc.add_argument("--version", required=True)
    sc.add_argument("--limit", type=int, default=20)

    scv = ssub.add_parser("caveats", parents=[fmt], help="Search known bugs/caveats")
    scv.add_argument("query", help="Search terms")
    scv.add_argument("--os", required=True)
    scv.add_argument("--version", default=None)
    scv.add_argument("--severity", default=None)
    scv.add_argument("--limit", type=int, default=10)

    she = ssub.add_parser("human-errors", parents=[fmt], help="Search operator mistakes by symptoms")
    she.add_argument("symptoms", nargs="+", help="Symptom descriptions")
    she.add_argument("--os", required=True)

    sir = ssub.add_parser("interpretation-rules", parents=[fmt], help="Search interpretation rules")
    sir.add_argument("query", help="Search terms")
    sir.add_argument("--os", required=True)
    sir.add_argument("--limit", type=int, default=10)

    scov = ssub.add_parser("coverage", parents=[fmt], help="Check KB coverage for a topic")
    scov.add_argument("topic", help="Topic to check")
    scov.add_argument("--os", required=True)

    # --- compare ---
    cmp = sub.add_parser("compare", parents=[fmt], help="Compare hardware platforms")
    cmp.add_argument("platform_ids", nargs="+", help="Platform IDs to compare")

    # --- case ---
    case = sub.add_parser("case", help="Manage troubleshooting cases")
    csub = case.add_subparsers(dest="case_action", required=True)

    co = csub.add_parser("open", parents=[fmt], help="Open a new case")
    co.add_argument("symptom", help="Problem description")
    co.add_argument("--os", required=True)
    co.add_argument("--version", required=True)
    co.add_argument("--platform", default=None)

    cg = csub.add_parser("get", parents=[fmt], help="Read case state")
    cg.add_argument("case_id", help="Case ID")

    ca = csub.add_parser("advance", parents=[fmt], help="Advance case to next phase")
    ca.add_argument("case_id", help="Case ID")
    ca.add_argument("--phase", required=True, help="Phase being completed")
    ca.add_argument("--output", required=True, help="Phase findings/conclusion")

    cl = csub.add_parser("list", parents=[fmt], help="List all cases")

    cc = csub.add_parser("close", parents=[fmt], help="Close a case")
    cc.add_argument("case_id", help="Case ID")
    cc.add_argument("--resolution", required=True, help="Resolution summary")

    return p


def run(args: argparse.Namespace) -> dict:
    ctx = build_context(REPO_ROOT)
    dispatch = build_dispatch(ctx)
    case_tool = CaseTool(ctx)

    if args.command == "validate":
        return dispatch["validate_command"](command=args.cmd, os=args.os, version=args.version)

    if args.command == "compare":
        return dispatch["compare_platforms"](platform_ids=args.platform_ids)

    if args.command == "query":
        if args.query_type == "protocol":
            kwargs = dict(protocol_id=args.id, os=args.os, version=args.version)
            if args.platform:
                kwargs["platform"] = args.platform
            if args.asic_family:
                kwargs["asic_family"] = args.asic_family
            if args.no_def_refs:
                kwargs["include_def_refs"] = False
            return dispatch["get_protocol"](**kwargs)
        if args.query_type == "platform":
            return dispatch["get_platform"](platform_id=args.id)
        if args.query_type == "scalability":
            return dispatch["get_scalability"](platform_family=args.family, os=args.os, version=args.version)
        if args.query_type == "diagnostic":
            return dispatch["get_diagnostic_tree"](tree_id=args.id, os=args.os, version=args.version)
        if args.query_type == "procedure":
            return dispatch["get_procedure"](procedure_id=args.id, os=args.os, version=args.version)
        if args.query_type == "human-error":
            return dispatch["get_human_error"](error_id=args.id, os=args.os)
        if args.query_type == "best-practices":
            return dispatch["get_best_practices"](os=args.os)
        if args.query_type == "interpretation-rule":
            return dispatch["get_interpretation_rule"](rule_id=args.id, os=args.os)

    if args.command == "search":
        if args.search_type == "commands":
            return dispatch["search_commands"](query=args.query, os=args.os, version=args.version, limit=args.limit)
        if args.search_type == "caveats":
            kwargs = dict(query=args.query, os=args.os, limit=args.limit)
            if args.version:
                kwargs["version"] = args.version
            if args.severity:
                kwargs["severity"] = args.severity
            return dispatch["search_caveats"](**kwargs)
        if args.search_type == "human-errors":
            return dispatch["search_human_errors"](symptoms=args.symptoms, os=args.os)
        if args.search_type == "interpretation-rules":
            return dispatch["search_interpretation_rules"](query=args.query, os=args.os, limit=args.limit)
        if args.search_type == "coverage":
            return dispatch["check_kb_coverage"](topic=args.topic, os=args.os)

    if args.command == "case":
        if args.case_action == "open":
            kwargs = dict(symptom=args.symptom, os=args.os, version=args.version)
            if args.platform:
                kwargs["platform"] = args.platform
            return dispatch["open_case"](**kwargs)
        if args.case_action == "get":
            return dispatch["get_case"](case_id=args.case_id)
        if args.case_action == "advance":
            return dispatch["advance_phase"](case_id=args.case_id, current_phase=args.phase, output=args.output)
        if args.case_action == "list":
            return case_tool.list_cases()
        if args.case_action == "close":
            return case_tool.close_case(case_id=args.case_id, resolution=args.resolution)

    return {"error": f"Unknown command: {args.command}"}


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
        print(format_result(result, args.format))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
