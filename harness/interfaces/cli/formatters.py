import json


def format_result(result: dict, fmt: str = "full") -> str:
    if fmt == "compact":
        return _compact(result)
    if fmt == "minimal":
        return _minimal(result)
    return json.dumps(result, indent=2, default=str)


def _compact(result: dict) -> str:
    tool = result.get("source_tool", "")
    data = result.get("data")
    if data is None:
        return f"[{tool}] No data returned."

    extractor = _COMPACT_EXTRACTORS.get(tool)
    if extractor:
        return extractor(result)
    return json.dumps(data, indent=2, default=str)


def _minimal(result: dict) -> str:
    tool = result.get("source_tool", "")
    data = result.get("data")
    if data is None:
        return "no data"

    summarizer = _MINIMAL_SUMMARIZERS.get(tool)
    if summarizer:
        return summarizer(result)
    return json.dumps(data, separators=(",", ":"), default=str)


def _compact_validate(r: dict) -> str:
    d = r["data"]
    lines = [f"status: {d['status']}"]
    if d.get("matched_syntax"):
        lines.append(f"syntax: {d['matched_syntax']}")
    if d.get("suggestions"):
        lines.append("suggestions:")
        for s in d["suggestions"]:
            lines.append(f"  - {s}")
    return "\n".join(lines)


def _compact_protocol(r: dict) -> str:
    d = r["data"]
    lines = [f"protocol: {d.get('protocol_id', '?')}"]
    fm = d.get("failure_modes", [])
    if fm:
        lines.append(f"failure_modes ({len(fm)}):")
        for f in fm:
            lines.append(f"  - {f.get('scenario', f.get('name', '?'))}")
    timers = d.get("timers", [])
    if timers:
        lines.append(f"timers ({len(timers)}):")
        for t in timers:
            lines.append(f"  - {t.get('name', t.get('id', '?'))}")
    return "\n".join(lines)


def _compact_search_commands(r: dict) -> str:
    d = r["data"]
    cmds = d.get("commands", [])
    lines = [f"commands ({d.get('total', len(cmds))}):"]
    for c in cmds:
        lines.append(f"  {c.get('syntax', '?')}")
    return "\n".join(lines)


def _compact_search_caveats(r: dict) -> str:
    d = r["data"]
    caveats = d.get("caveats", [])
    lines = [f"caveats ({d.get('total', len(caveats))}):"]
    for c in caveats:
        conf = c.get("match_confidence", "")
        label = f" [{conf}]" if conf else ""
        csc = c.get("csc_id", "")
        tag = csc if csc else f"#{c.get('id', '?')}"
        lines.append(f"  {tag}: {c.get('headline', '?')}{label}")
    return "\n".join(lines)


def _compact_platform(r: dict) -> str:
    d = r["data"]
    lines = [f"platform: {d.get('platform_id', '?')}"]
    for key in ("asic_family", "chassis_type", "total_ports", "bandwidth"):
        if d.get(key):
            lines.append(f"  {key}: {d[key]}")
    return "\n".join(lines)


def _compact_case(r: dict) -> str:
    d = r["data"]
    if isinstance(d, dict) and "case_id" in d:
        lines = [f"case: {d['case_id']}", f"phase: {d.get('current_phase', '?')}"]
        if d.get("closed"):
            lines.append("status: closed")
        return "\n".join(lines)
    return json.dumps(d, indent=2, default=str)


def _compact_cases_list(r: dict) -> str:
    d = r["data"]
    cases = d.get("cases", [])
    if not cases:
        return "no open cases"
    lines = [f"cases ({len(cases)}):"]
    for c in cases:
        lines.append(f"  {c.get('case_id', '?')}: {c.get('current_phase', '?')}")
    return "\n".join(lines)


def _compact_coverage(r: dict) -> str:
    d = r["data"]
    lines = [f"covered: {d.get('covered', '?')}"]
    matches = d.get("matches", [])
    if isinstance(matches, list):
        for m in matches:
            if isinstance(m, dict):
                mid = m.get("id", "?")
                mtype = m.get("type", "?")
                mname = m.get("name", mid)
                lines.append(f"  [{mtype}] {mname}")
            else:
                lines.append(f"  - {m}")
    elif isinstance(matches, dict):
        for key, items in matches.items():
            if items:
                lines.append(f"  {key}: {', '.join(str(i) for i in items)}")
    return "\n".join(lines)


def _minimal_validate(r: dict) -> str:
    d = r["data"]
    s = d.get("matched_syntax", d.get("command", ""))
    return f"{d['status']}: {s}" if s else d["status"]


def _minimal_protocol(r: dict) -> str:
    d = r["data"]
    fm = len(d.get("failure_modes", []))
    return f"{d.get('protocol_id', '?')}: {fm} failure modes"


def _minimal_search_commands(r: dict) -> str:
    d = r["data"]
    return f"{d.get('total', len(d.get('commands', [])))} commands found"


def _minimal_search_caveats(r: dict) -> str:
    d = r["data"]
    return f"{d.get('total', len(d.get('caveats', [])))} caveats found"


def _minimal_platform(r: dict) -> str:
    d = r["data"]
    return f"{d.get('platform_id', '?')}: {d.get('asic_family', '?')} / {d.get('chassis_type', '?')}"


def _minimal_case(r: dict) -> str:
    d = r["data"]
    if isinstance(d, dict) and "case_id" in d:
        return f"case {d['case_id']}: {d.get('current_phase', '?')}"
    return str(d)


def _minimal_cases_list(r: dict) -> str:
    cases = r["data"].get("cases", [])
    return f"{len(cases)} cases"


def _minimal_coverage(r: dict) -> str:
    return f"covered: {r['data'].get('covered', '?')}"


def _compact_interpretation_rule(r: dict) -> str:
    d = r["data"]
    lines = [
        f"rule: {d.get('rule_id', '?')}",
        f"category: {d.get('category', '?')}",
        f"context: {d.get('context', '?')}",
        f"observation: {d.get('observation', '?')}",
        f"naive: {d.get('naive_interpretation', '?')}",
        f"correct: {d.get('correct_interpretation', '?')}",
    ]
    traps = d.get("traps", [])
    if traps:
        lines.append(f"traps ({len(traps)}):")
        for t in traps:
            lines.append(f"  - {t}")
    return "\n".join(lines)


def _compact_search_interp_rules(r: dict) -> str:
    d = r["data"]
    rules = d.get("rules", [])
    lines = [f"interpretation rules ({d.get('total', len(rules))}):"]
    for rule in rules:
        lines.append(f"  [{rule.get('category', '?')}] {rule.get('display_name', '?')}")
    return "\n".join(lines)


def _minimal_interpretation_rule(r: dict) -> str:
    d = r["data"]
    return f"{d.get('rule_id', '?')}: {d.get('display_name', '?')}"


def _minimal_search_interp_rules(r: dict) -> str:
    d = r["data"]
    return f"{d.get('total', len(d.get('rules', [])))} interpretation rules found"


_COMPACT_EXTRACTORS = {
    "validate_command": _compact_validate,
    "get_protocol": _compact_protocol,
    "search_commands": _compact_search_commands,
    "search_caveats": _compact_search_caveats,
    "get_platform": _compact_platform,
    "compare_platforms": _compact_platform,
    "get_scalability": _compact_platform,
    "get_diagnostic_tree": None,
    "get_procedure": None,
    "get_human_error": None,
    "search_human_errors": None,
    "open_case": _compact_case,
    "get_case": _compact_case,
    "advance_phase": _compact_case,
    "close_case": _compact_case,
    "list_cases": _compact_cases_list,
    "check_kb_coverage": _compact_coverage,
    "get_best_practices": None,
    "get_interpretation_rule": _compact_interpretation_rule,
    "search_interpretation_rules": _compact_search_interp_rules,
}

_MINIMAL_SUMMARIZERS = {
    "validate_command": _minimal_validate,
    "get_protocol": _minimal_protocol,
    "search_commands": _minimal_search_commands,
    "search_caveats": _minimal_search_caveats,
    "get_platform": _minimal_platform,
    "compare_platforms": _minimal_platform,
    "get_scalability": _minimal_platform,
    "open_case": _minimal_case,
    "get_case": _minimal_case,
    "advance_phase": _minimal_case,
    "close_case": _minimal_case,
    "list_cases": _minimal_cases_list,
    "check_kb_coverage": _minimal_coverage,
    "get_interpretation_rule": _minimal_interpretation_rule,
    "search_interpretation_rules": _minimal_search_interp_rules,
}
