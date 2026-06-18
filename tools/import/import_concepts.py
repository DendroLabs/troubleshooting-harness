#!/usr/bin/env python3
"""Transform stateless cisco concept files into the TSH concept schema.

These are files that don't fit the FSM-based protocol schema (states minItems:1)
but contain valuable operational data (failure modes, timers, vendor notes).
Reuses the cisco-KB transform helpers since the source format is identical.
"""
from __future__ import annotations

import json

from common import (
    ARCHIVED, SCHEMA_VERSION, CONFIDENCE,
    map_dependency_type, parse_standards, provenance_source,
)
from import_cisco_kb import _transform_timers, _transform_failure_modes, _vendor_notes

CISCO_KB = ARCHIVED / "cisco-kb"

CONCEPT_SOURCES = [
    "switching/l2-infrastructure.json",
]


def _transform_file(raw: dict, rel_path: str) -> dict:
    sources = parse_standards(raw.get("standard", ""))
    sources.append(provenance_source("cisco", rel_path))

    concept = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "concept_id": raw["protocol_id"],
        "concept_name": raw["protocol_name"],
        "concept_family": raw["protocol_family"],
        "purpose": raw["purpose"],
        "failure_modes": _transform_failure_modes(raw.get("failure_modes", [])),
        "sources": sources,
    }
    for field in ("standard", "operates_at"):
        if raw.get(field):
            concept[field] = raw[field]

    timers = _transform_timers(raw.get("timers", []))
    if timers:
        concept["timers"] = timers

    deps = []
    for d in raw.get("dependencies", []):
        deps.append({"type": map_dependency_type(d["type"]), "name": d["name"],
                     "description": d.get("description", "")})
    if deps:
        concept["dependencies"] = deps

    vendor_notes = _vendor_notes(raw.get("os_notes", []))
    if vendor_notes:
        concept["vendor_notes"] = vendor_notes

    tags = list(raw.get("tags", []))
    category = raw.get("category")
    if category and category not in tags:
        tags.append(category)
    if tags:
        concept["tags"] = tags
    if raw.get("related_protocols"):
        concept["related_protocols"] = raw["related_protocols"]
    return concept


def load() -> list[dict]:
    concepts = []
    for rel_path in sorted(CONCEPT_SOURCES):
        path = CISCO_KB / rel_path
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        concepts.append(_transform_file(raw, rel_path))
    return concepts


if __name__ == "__main__":
    concepts = load()
    print(f"concepts: transformed {len(concepts)} files")
    for c in concepts:
        print(f"  {c['concept_id']:18} {len(c.get('failure_modes', []))} failure modes")
