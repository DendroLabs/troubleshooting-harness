#!/usr/bin/env python3
"""Transform the agent-cisco-kb protocol files into the unified TSH schema.

Same transform logic as import_cisco_kb.py but reads from the agent-cisco-kb
archive which has additional subdirectories (multicast, security, services).
Only imports protocols NOT already present in the cisco-kb source to avoid
duplicate merge overhead on identical content.

Exposes ``load(skip_ids) -> list[protocol]`` for build_protocols.py.
"""
from __future__ import annotations

import json

from common import (
    ARCHIVED, ALL_VR, CISCO_OSES, SCHEMA_VERSION, CONFIDENCE,
    map_dependency_type, parse_standards, provenance_source,
    scoped_cause, scoped_resolution, verify_cmd,
)

AGENT_CISCO_KB = ARCHIVED / "agent-cisco-kb" / "knowledge-base"
PROTOCOL_SUBDIRS = [
    "routing", "switching", "transport", "adjacency", "fhrp", "overlay",
    "vendor", "multicast", "security", "services",
]

# Stateless protocols that should still be imported (they have failure_modes).
STATELESS_ALLOW = {
    "static-routing", "pbr", "vrf", "netflow", "snmp",
    "span-erspan", "l2-infrastructure",
}

_dropped_state_cmds = 0
_concept_files: list[str] = []


def _transform_timers(src_timers: list[dict]) -> list[dict]:
    out = []
    for t in src_timers:
        timer = {
            "name": t["name"],
            "description": t.get("description", ""),
            "default_rfc": t.get("default", ""),
            "on_expiry": t.get("on_expiry", ""),
        }
        if t.get("range"):
            timer["range"] = t["range"]
        if t.get("tuning_advice"):
            timer["tuning_advice"] = t["tuning_advice"]
        os_defaults = []
        for ov in t.get("os_overrides", []):
            default_val = ov.get("default") or ov.get("value") or ""
            if not default_val and not ov.get("notes") and not ov.get("note"):
                continue
            entry = {"os": ov["os"], "version_range": dict(ALL_VR), "default": default_val}
            note = ov.get("notes") or ov.get("note")
            if note:
                entry["notes"] = note
            os_defaults.append(entry)
        if os_defaults:
            timer["os_defaults"] = os_defaults
        out.append(timer)
    return out


def _transform_failure_modes(src_modes: list[dict]) -> list[dict]:
    out = []
    for fm in src_modes:
        causes = [scoped_cause(c, "*", ALL_VR) for c in fm.get("root_causes", [])]
        resolutions = [
            scoped_resolution(r, os, ALL_VR)
            for r in fm.get("resolution", [])
            for os in CISCO_OSES
        ]
        verifies = [
            verify_cmd(v, os, ALL_VR)
            for v in fm.get("verify_commands", [])
            for os in CISCO_OSES
        ]
        mode = {
            "scenario": fm["scenario"],
            "description": fm.get("description", ""),
            "symptoms": fm.get("symptoms", []),
            "root_causes": causes,
            "resolutions": resolutions,
        }
        if verifies:
            mode["verify_commands"] = verifies
        out.append(mode)
    return out


def _transform_states(src_states: list[dict]) -> list[dict]:
    global _dropped_state_cmds
    out = []
    for s in src_states:
        _dropped_state_cmds += len(s.get("verify_commands", []))
        out.append({
            "name": s["name"],
            "description": s.get("description", ""),
            "is_steady": s["is_steady"],
            "is_failure": s["is_failure"],
        })
    return out


def _transform_transitions(src: list[dict]) -> list[dict]:
    out = []
    for t in src:
        tr = {"from_state": t["from_state"], "to_state": t["to_state"], "trigger": t["trigger"]}
        if t.get("failure_if_stuck"):
            tr["failure_if_stuck"] = t["failure_if_stuck"]
        out.append(tr)
    return out


def _vendor_notes(os_notes: list[dict]) -> dict:
    notes: dict[str, dict] = {}
    for n in os_notes:
        bucket = notes.setdefault(n["os"], {"notes": [], "config_examples": []})
        bucket["notes"].append({"note": n["note"], "versions": n.get("versions", "all")})
        if n.get("config_example"):
            bucket["config_examples"].append(n["config_example"])
    for bucket in notes.values():
        if not bucket["config_examples"]:
            bucket.pop("config_examples")
    return notes


def _transform_file(raw: dict, rel_path: str) -> dict:
    sources = parse_standards(raw.get("standard", ""))
    sources.append(provenance_source("agent-cisco-kb", rel_path))

    proto = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "protocol_id": raw["protocol_id"],
        "protocol_name": raw["protocol_name"],
        "protocol_family": raw["protocol_family"],
        "purpose": raw["purpose"],
        "states": _transform_states(raw.get("states", [])),
        "failure_modes": _transform_failure_modes(raw.get("failure_modes", [])),
        "sources": sources,
    }
    for opt_field, src_field in (("standard", "standard"), ("operates_at", "operates_at"),
                                 ("transport", "transport")):
        if raw.get(src_field):
            proto[opt_field] = raw[src_field]

    transitions = _transform_transitions(raw.get("transitions", []))
    if transitions:
        proto["transitions"] = transitions
    timers = _transform_timers(raw.get("timers", []))
    if timers:
        proto["timers"] = timers
    if raw.get("messages"):
        proto["messages"] = raw["messages"]

    deps = []
    for d in raw.get("dependencies", []):
        deps.append({"type": map_dependency_type(d["type"]), "name": d["name"],
                     "description": d.get("description", "")})
    if deps:
        proto["dependencies"] = deps

    vendor_notes = _vendor_notes(raw.get("os_notes", []))
    if vendor_notes:
        proto["vendor_notes"] = vendor_notes

    tags = list(raw.get("tags", []))
    category = raw.get("category")
    if category and category not in tags:
        tags.append(category)
    if tags:
        proto["tags"] = tags
    if raw.get("related_protocols"):
        proto["related_protocols"] = raw["related_protocols"]
    return proto


def load(skip_ids: set[str] | None = None) -> list[dict]:
    """Load and transform protocols, skipping any IDs in skip_ids."""
    if skip_ids is None:
        skip_ids = set()
    protocols = []
    for subdir in PROTOCOL_SUBDIRS:
        d = AGENT_CISCO_KB / "protocols" / subdir
        if not d.exists():
            continue
        for path in sorted(d.glob("*.json")):
            if path.name.startswith("_"):
                continue
            raw = json.loads(path.read_text())
            pid = raw.get("protocol_id", path.stem)
            if pid in skip_ids:
                continue
            proto = _transform_file(raw, f"{subdir}/{path.name}")
            if not proto["states"] and pid not in STATELESS_ALLOW:
                _concept_files.append(f"{subdir}/{path.name}")
                continue
            protocols.append(proto)
    return protocols


def main() -> int:
    protos = load()
    print(f"agent-cisco-kb: transformed {len(protos)} protocols, dropped {_dropped_state_cmds} "
          f"string-only state verify_commands")
    for p in protos:
        print(f"  {p['protocol_id']:25} {len(p.get('failure_modes', []))} failure modes, "
              f"{len(p.get('states', []))} states")
    if _concept_files:
        print(f"routed to concepts: {', '.join(_concept_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
