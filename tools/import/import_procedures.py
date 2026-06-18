#!/usr/bin/env python3
"""Transform operational procedures into the unified TSH procedure schema.

Two source shapes:

  SONiC (one procedure per file): top-level steps[] each with a single ``command``
  string and a single ``verification`` object. We wrap command -> commands[] and
  verification -> verification[] (scoped os="sonic"). A verification whose command
  is null carries no command the schema can hold, so its look_for/confirms_if text
  is folded into the step ``notes`` instead of being dropped.

  Cisco (one file, many os_procedures[]): each os_procedure is a structurally
  distinct step sequence, so it becomes its own procedure doc with id
  ``<procedure_id>-<os>`` and applicable_os=[os]. The procedure-level verification[]
  becomes a synthesised trailing "verify" step. The free-text rollback[] strings
  become rollback steps with no command. The procedure-level failure_modes[] have
  no home in the procedure schema and are dropped (count logged).

Exposes ``load() -> list[procedure]`` and the running ``DROPPED_FAILURE_MODES`` count.
"""
from __future__ import annotations

import copy
import json

from common import (
    ARCHIVED, SONIC_VR, ALL_VR, SCHEMA_VERSION, CONFIDENCE, provenance_source,
)

SONIC_PROCEDURES = ARCHIVED / "sonic-kb" / "knowledge-base" / "procedures"
CISCO_PROCEDURES = ARCHIVED / "cisco-kb" / "procedures"

DROPPED_FAILURE_MODES = 0

RISK_ENUM = {"low", "medium", "high", "critical"}


def _risk_level(value: str) -> str:
    """Map a free-text risk_level onto the schema enum. 'varies' on a container
    restart can take down forwarding, so it floors at 'high'."""
    val = (value or "").strip().lower()
    if val in RISK_ENUM:
        return val
    return "high" if val == "varies" else "medium"


def _daemon_impact(raw: list) -> list[dict]:
    """SONiC sources give daemon_impact either as {daemon, impact} objects or as
    bare def_id strings — normalise both to the schema's object shape."""
    out = []
    for entry in raw:
        if isinstance(entry, str):
            out.append({"daemon": entry, "impact": ""})
        else:
            out.append({"daemon": entry["daemon"], "impact": entry.get("impact", "")})
    return out


# --- SONiC -----------------------------------------------------------------

def _sonic_step(src: dict) -> dict:
    step = {
        "step_id": src["step_id"],
        "step": src["step"],
        "action": src["action"],
        "commands": [],
    }
    if src.get("command"):
        step["commands"].append(
            {"os": "sonic", "version_range": copy.deepcopy(SONIC_VR), "command": src["command"]})

    notes = src.get("notes", "")
    ver = src.get("verification")
    if ver:
        if ver.get("command"):
            step["verification"] = [{
                "os": "sonic",
                "version_range": copy.deepcopy(SONIC_VR),
                "command": ver["command"],
                "look_for": ver.get("look_for", ""),
                "confirms_if": ver.get("confirms_if", ""),
            }]
        else:
            # No command to verify with — preserve the intent in notes.
            fold = f"Verify: {ver.get('look_for', '')}".rstrip()
            if ver.get("confirms_if"):
                fold += f" (confirms if {ver['confirms_if']})"
            notes = f"{notes} {fold}".strip() if notes else fold

    if src.get("next_step_id") is not None:
        step["next_step_id"] = src["next_step_id"]
    if src.get("rollback_step_id") is not None:
        step["rollback_step_id"] = src["rollback_step_id"]
    if src.get("daemon_impact"):
        step["daemon_impact"] = _daemon_impact(src["daemon_impact"])
    if src.get("warning"):
        step["warning"] = src["warning"]
    if notes:
        step["notes"] = notes
    return step


def _sonic_rollback(src: dict) -> dict:
    rb = {"step_id": src["step_id"], "action": src["action"], "commands": []}
    if src.get("command"):
        rb["commands"].append(
            {"os": "sonic", "version_range": copy.deepcopy(SONIC_VR), "command": src["command"]})
    if src.get("notes"):
        rb["notes"] = src["notes"]
    return rb


def _transform_sonic(raw: dict, rel_path: str) -> dict:
    proc = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "procedure_id": raw["procedure_id"],
        "procedure_name": raw["procedure_name"],
        "category": raw["category"],
        "risk_level": _risk_level(raw["risk_level"]),
        "purpose": raw["purpose"],
        "applicable_os": ["sonic"],
        "steps": [_sonic_step(s) for s in raw["steps"]],
        "sources": [provenance_source("sonic", rel_path)],
    }
    if raw.get("def_refs"):
        proc["def_refs"] = raw["def_refs"]
    if raw.get("prerequisites"):
        proc["prerequisites"] = raw["prerequisites"]
    if raw.get("warnings"):
        proc["warnings"] = raw["warnings"]
    rollback = [_sonic_rollback(r) for r in raw.get("rollback", [])]
    if rollback:
        proc["rollback"] = rollback
    return proc


# --- Cisco -----------------------------------------------------------------

def _cisco_step(src: dict, os: str) -> dict:
    step = {
        "step_id": f"step-{src['step']}",
        "step": src["step"],
        "action": src["action"],
        "commands": [],
    }
    if src.get("command"):
        step["commands"].append(
            {"os": os, "version_range": copy.deepcopy(ALL_VR), "command": src["command"]})
    if src.get("notes"):
        step["notes"] = src["notes"]
    return step


def _transform_cisco(raw: dict, rel_path: str) -> list[dict]:
    global DROPPED_FAILURE_MODES
    DROPPED_FAILURE_MODES += len(raw.get("failure_modes", []))

    procs = []
    for op in raw.get("os_procedures", []):
        os = op["os"]
        purpose = raw["purpose"]
        extra = []
        if op.get("method"):
            extra.append(f"method: {op['method']}")
        if op.get("platforms"):
            extra.append(f"platforms: {op['platforms']}")
        if extra:
            purpose = f"{purpose} [{os} — {'; '.join(extra)}]"

        steps = [_cisco_step(s, os) for s in op.get("steps", [])]

        # Procedure-level verification[] -> a synthesised trailing verify step.
        verification = []
        for v in op.get("verification", []):
            verification.append({
                "os": os,
                "version_range": copy.deepcopy(ALL_VR),
                "command": v["command"],
                "look_for": v.get("look_for", ""),
                "confirms_if": v.get("confirms_if", ""),
            })
        if verification:
            steps.append({
                "step_id": "verify",
                "step": len(steps) + 1,
                "action": "Verify the procedure completed successfully",
                "commands": [],
                "verification": verification,
            })

        warnings = []
        for w in (raw.get("warnings", []) + op.get("warnings", [])):
            if w not in warnings:
                warnings.append(w)

        # Free-text rollback strings -> rollback steps (no command).
        rollback = [{"step_id": f"rollback-{i + 1}", "action": s, "commands": []}
                    for i, s in enumerate(op.get("rollback", []))]

        proc = {
            "schema_version": SCHEMA_VERSION,
            "confidence": CONFIDENCE,
            "procedure_id": f"{raw['procedure_id']}-{os}",
            "procedure_name": f"{raw['procedure_name']} ({os})",
            "category": raw["category"],
            "risk_level": _risk_level(raw["risk_level"]),
            "purpose": purpose,
            "applicable_os": [os],
            "steps": steps,
            "sources": [provenance_source("cisco", rel_path)],
        }
        if raw.get("prerequisites"):
            proc["prerequisites"] = raw["prerequisites"]
        if warnings:
            proc["warnings"] = warnings
        if rollback:
            proc["rollback"] = rollback
        procs.append(proc)
    return procs


def load() -> list[dict]:
    procedures = []
    for path in sorted(SONIC_PROCEDURES.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        procedures.append(_transform_sonic(raw, f"procedures/{path.name}"))
    for path in sorted(CISCO_PROCEDURES.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        procedures.extend(_transform_cisco(raw, f"procedures/{path.name}"))
    return procedures


if __name__ == "__main__":
    procs = load()
    print(f"procedures: transformed {len(procs)} docs "
          f"(dropped {DROPPED_FAILURE_MODES} cisco procedure-level failure_modes)")
    for p in procs:
        print(f"  {p['procedure_id']:24} {len(p['steps'])} steps  os={p['applicable_os']}")
