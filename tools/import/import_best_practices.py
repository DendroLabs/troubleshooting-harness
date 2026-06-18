#!/usr/bin/env python3
"""Transform the Cisco best-practice link indexes into the TSH schema.

These are curated reference indexes (categories of authoritative doc links plus
Cisco Live sessions), one per OS. The category/document shape already matches the
schema; we add schema_version/confidence/best_practice_id and a provenance source.

Exposes ``load() -> list[best_practice]`` for build_supporting.py.
"""
from __future__ import annotations

import json

from common import (
    ARCHIVED, SCHEMA_VERSION, CONFIDENCE, provenance_source,
)

BEST_PRACTICES = ARCHIVED / "cisco-kb" / "best-practices"


def _transform_file(raw: dict, rel_path: str) -> dict:
    os = raw["os"]
    bp = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "best_practice_id": f"{os}-best-practices",
        "os": os,
        "categories": raw["categories"],
        "sources": [provenance_source("cisco", rel_path)],
    }
    if raw.get("cisco_live_sessions"):
        bp["cisco_live_sessions"] = raw["cisco_live_sessions"]
    if raw.get("notes"):
        bp["notes"] = raw["notes"]
    if raw.get("tags"):
        bp["tags"] = raw["tags"]
    return bp


def load() -> list[dict]:
    out = []
    for path in sorted(BEST_PRACTICES.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        rel_path = f"best-practices/{path.parent.name}/{path.name}"
        out.append(_transform_file(raw, rel_path))
    return out


if __name__ == "__main__":
    docs = load()
    print(f"best-practices: transformed {len(docs)} indexes")
    for d in docs:
        cats = len(d["categories"])
        docs_n = sum(len(c["documents"]) for c in d["categories"])
        print(f"  {d['best_practice_id']:24} {cats} categories, {docs_n} documents")
