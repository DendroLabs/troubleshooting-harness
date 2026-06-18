#!/usr/bin/env python3
"""Transform the SONiC KB protocol files into the unified TSH schema.

Exposes ``load() -> list[protocol]`` for build_protocols.py.

Transform rules (locked):
  - add schema_version + confidence; keep def_refs
  - timers: default -> default_rfc; sonic_default/config_path/frr_path -> a
    single os_defaults entry scoped os="sonic", version_range=202511..*
  - failure modes scoped entirely to os="sonic" (causes, resolutions, verify_commands)
  - drop state.verify_commands (string-only)
  - config_db_tables / sonic_notes / sonic_frr_mapping / key_commands -> vendor_notes.sonic
  - sources synthesised from `standard` (RFC) + KB provenance (sonic_notes keep
    their own source_ref inside vendor_notes.sonic.notes)
  - dependency.type remapped to the target enum
"""
from __future__ import annotations

import json

from common import (
    ARCHIVED, SONIC_VR, SCHEMA_VERSION, CONFIDENCE,
    map_dependency_type, parse_standards, provenance_source,
    scoped_cause, scoped_resolution, verify_cmd,
)

SONIC_PROTOCOLS = ARCHIVED / "sonic-kb" / "knowledge-base" / "protocols"

_dropped_state_cmds = 0


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
        if t.get("sonic_default"):
            entry = {"os": "sonic", "version_range": dict(SONIC_VR), "default": t["sonic_default"]}
            if t.get("sonic_config_path"):
                entry["config_path"] = t["sonic_config_path"]
            if t.get("sonic_frr_path"):
                entry["frr_path"] = t["sonic_frr_path"]
            timer["os_defaults"] = [entry]
        out.append(timer)
    return out


def _transform_failure_modes(src_modes: list[dict]) -> list[dict]:
    out = []
    for fm in src_modes:
        mode = {
            "scenario": fm["scenario"],
            "description": fm.get("description", ""),
            "symptoms": fm.get("symptoms", []),
            "root_causes": [scoped_cause(c, "sonic", SONIC_VR) for c in fm.get("root_causes", [])],
            "resolutions": [scoped_resolution(r, "sonic", SONIC_VR) for r in fm.get("resolution", [])],
        }
        verifies = [verify_cmd(v, "sonic", SONIC_VR) for v in fm.get("verify_commands", [])]
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


def _vendor_notes(raw: dict) -> dict:
    sonic: dict = {}
    if raw.get("config_db_tables"):
        sonic["config_db_tables"] = raw["config_db_tables"]
    if raw.get("sonic_notes"):
        sonic["notes"] = raw["sonic_notes"]
    if raw.get("sonic_frr_mapping"):
        sonic["frr_mapping"] = raw["sonic_frr_mapping"]
    if raw.get("key_commands"):
        sonic["key_commands"] = raw["key_commands"]
    return {"sonic": sonic} if sonic else {}


def _transform_file(raw: dict, rel_path: str) -> dict:
    sources = parse_standards(raw.get("standard", ""))
    sources.append(provenance_source("sonic", rel_path))

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
    for field in ("standard", "operates_at", "transport"):
        if raw.get(field):
            proto[field] = raw[field]
    if raw.get("def_refs"):
        proto["def_refs"] = raw["def_refs"]

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

    vendor_notes = _vendor_notes(raw)
    if vendor_notes:
        proto["vendor_notes"] = vendor_notes
    if raw.get("tags"):
        proto["tags"] = raw["tags"]
    if raw.get("related_protocols"):
        proto["related_protocols"] = raw["related_protocols"]
    return proto


def load() -> list[dict]:
    protocols = []
    for path in sorted(SONIC_PROTOCOLS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        protocols.append(_transform_file(raw, f"protocols/{path.name}"))
    return protocols


def main() -> int:
    protos = load()
    print(f"sonic: transformed {len(protos)} protocols, dropped {_dropped_state_cmds} "
          f"string-only state verify_commands")
    for p in protos:
        print(f"  {p['protocol_id']:18} {len(p.get('failure_modes', []))} failure modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
