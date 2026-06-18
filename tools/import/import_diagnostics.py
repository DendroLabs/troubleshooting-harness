#!/usr/bin/env python3
"""Transform the SONiC KB diagnostic trees into the unified TSH schema.

Exposes ``load() -> list[diagnostic_tree]`` for build_supporting.py.

Transform rules (locked):
  - add schema_version + confidence + applicable_os=["sonic"]
  - every command string becomes a scoped_command {os, version_range, command}
    scoped to os="sonic", version_range=202511..*
  - keep related_protocol / related_errors (when non-empty); branches pass through
  - drop related_code_paths (no home in the target schema)
  - sources synthesised from KB provenance
"""
from __future__ import annotations

import copy
import json

from common import (
    ARCHIVED, SONIC_VR, SCHEMA_VERSION, CONFIDENCE, provenance_source,
)

SONIC_DIAGNOSTICS = ARCHIVED / "sonic-kb" / "knowledge-base" / "diagnostics"


def _scoped(command: str) -> dict:
    return {"os": "sonic", "version_range": copy.deepcopy(SONIC_VR), "command": command}


def _transform_node(node: dict) -> dict:
    if node["node_type"] == "branch":
        out = {
            "node_id": node["node_id"],
            "node_type": "branch",
            "question": node["question"],
            "commands": [_scoped(c) for c in node.get("commands", [])],
            "branches": node["branches"],
        }
    else:  # leaf
        out = {
            "node_id": node["node_id"],
            "node_type": "leaf",
            "finding": node["finding"],
            "action": node["action"],
        }
        cmds = [_scoped(c) for c in node.get("commands", [])]
        if cmds:
            out["commands"] = cmds
    return out


def _transform_file(raw: dict, rel_path: str) -> dict:
    tree = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "tree_id": raw["tree_id"],
        "display_name": raw["display_name"],
        "entry_symptom": raw["entry_symptom"],
        "applicable_os": ["sonic"],
        "nodes": [_transform_node(n) for n in raw["nodes"]],
        "sources": [provenance_source("sonic", rel_path)],
    }
    if raw.get("related_protocol"):
        tree["related_protocol"] = raw["related_protocol"]
    if raw.get("related_errors"):
        tree["related_errors"] = raw["related_errors"]
    return tree


def load() -> list[dict]:
    trees = []
    for path in sorted(SONIC_DIAGNOSTICS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        trees.append(_transform_file(raw, f"diagnostics/{path.name}"))
    return trees


if __name__ == "__main__":
    trees = load()
    print(f"diagnostics: transformed {len(trees)} trees")
    for t in trees:
        print(f"  {t['tree_id']:28} {len(t['nodes'])} nodes")
