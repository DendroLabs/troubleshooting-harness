#!/usr/bin/env python3
"""Transform the SONiC KB human-error patterns into the unified TSH schema.

Exposes ``load() -> list[human_error]`` for build_supporting.py.

Transform rules (locked):
  - add schema_version + confidence + applicable_os=["sonic"] + version_range=202511..*
  - detection_commands: add os + version_range scope to each {command, purpose}
  - ref_daemons + ref_dbs -> def_refs (the def_id atom references)
  - context_keywords merged into keywords (ordered union; no home of its own)
  - sources synthesised from KB provenance
"""
from __future__ import annotations

import copy
import json

from common import (
    ARCHIVED, SONIC_VR, SCHEMA_VERSION, CONFIDENCE, provenance_source,
)

SONIC_HUMAN_ERRORS = ARCHIVED / "sonic-kb" / "knowledge-base" / "human-errors"


def _ordered_union(*lists) -> list:
    seen, out = set(), []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                out.append(item)
    return out


def _transform_file(raw: dict, rel_path: str) -> dict:
    err = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "error_id": raw["error_id"],
        "display_name": raw["display_name"],
        "severity": raw["severity"],
        "category": raw["category"],
        "applicable_os": ["sonic"],
        "version_range": copy.deepcopy(SONIC_VR),
        "pattern": raw["pattern"],
        "what_goes_wrong": raw["what_goes_wrong"],
        "symptoms": raw.get("symptoms", []),
        "correct_procedure": raw["correct_procedure"],
        "sources": [provenance_source("sonic", rel_path)],
    }
    if raw.get("why_it_breaks"):
        err["why_it_breaks"] = raw["why_it_breaks"]
    if raw.get("prevention"):
        err["prevention"] = raw["prevention"]

    detection = []
    for dc in raw.get("detection_commands", []):
        detection.append({
            "os": "sonic",
            "version_range": copy.deepcopy(SONIC_VR),
            "command": dc["command"],
            "purpose": dc.get("purpose", ""),
        })
    if detection:
        err["detection_commands"] = detection

    if raw.get("related_errors"):
        err["related_errors"] = raw["related_errors"]

    def_refs = _ordered_union(raw.get("ref_daemons", []), raw.get("ref_dbs", []))
    if def_refs:
        err["def_refs"] = def_refs

    keywords = _ordered_union(raw.get("keywords", []), raw.get("context_keywords", []))
    if keywords:
        err["keywords"] = keywords
    return err


def load() -> list[dict]:
    errors = []
    for path in sorted(SONIC_HUMAN_ERRORS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        errors.append(_transform_file(raw, f"human-errors/{path.name}"))
    return errors


if __name__ == "__main__":
    errors = load()
    print(f"human-errors: transformed {len(errors)} patterns")
    for e in errors:
        print(f"  {e['error_id']:32} {e['severity']:7} {len(e.get('def_refs', []))} def_refs")
