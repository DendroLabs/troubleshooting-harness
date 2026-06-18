#!/usr/bin/env python3
"""Build data/_cross-references.json.

Two graphs over the protocol set:
  - related_protocols: protocol_id -> [related protocol_ids]
  - def_ref_usage: def_id (daemon:/db:/timer:) -> [protocol_ids that reference it]

The def_ref_usage map also flags any def_ref that does not resolve to an atom
in data/definitions/ so dangling references surface immediately.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"


def load_protocols() -> list[dict]:
    return [json.loads(p.read_text())
            for p in sorted((DATA / "protocols").glob("*.json"))
            if not p.name.startswith("_")]


def load_concepts() -> list[dict]:
    concept_dir = DATA / "concepts"
    if not concept_dir.exists():
        return []
    return [json.loads(p.read_text())
            for p in sorted(concept_dir.glob("*.json"))
            if not p.name.startswith("_")]


def load_dir(subdir: str) -> list[dict]:
    root = DATA / subdir
    if not root.exists():
        return []
    return [json.loads(p.read_text())
            for p in sorted(root.rglob("*.json"))
            if not p.name.startswith("_")]


def load_def_ids() -> set[str]:
    ids: set[str] = set()
    for path in (DATA / "definitions").glob("*.json"):
        if path.name.startswith("_"):
            continue
        doc = json.loads(path.read_text())
        for entry in doc.get("entries", []):
            ids.add(entry["def_id"])
    return ids


def main() -> int:
    protocols = load_protocols()
    concepts = load_concepts()
    diagnostics = load_dir("diagnostics")
    human_errors = load_dir("human-errors")
    procedures = load_dir("procedures")
    known_defs = load_def_ids()

    related = {p["protocol_id"]: p.get("related_protocols", []) for p in protocols
               if p.get("related_protocols")}
    for c in concepts:
        if c.get("related_protocols"):
            related[c["concept_id"]] = c["related_protocols"]

    # def_ref usage spans every doc type that references shared atoms. Each doc is
    # keyed by its own id field so a dangling ref points back to the offending file.
    id_field = {
        "protocol": "protocol_id", "concept": "concept_id", "tree": "tree_id",
        "error": "error_id", "procedure": "procedure_id",
    }

    def _id(doc: dict) -> str:
        for kind, field in id_field.items():
            if field in doc:
                return doc[field]
        return "?"

    usage: dict[str, list[str]] = {}
    for doc in [*protocols, *concepts, *diagnostics, *human_errors, *procedures]:
        for ref in doc.get("def_refs", []):
            usage.setdefault(ref, []).append(_id(doc))
    usage = {k: sorted(v) for k, v in sorted(usage.items())}

    dangling = sorted(ref for ref in usage if ref not in known_defs)

    doc = {
        "schema_version": "1.0.0",
        "related_protocols": dict(sorted(related.items())),
        "def_ref_usage": usage,
        "dangling_def_refs": dangling,
    }
    (DATA / "_cross-references.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote _cross-references.json: {len(related)} related-protocol entries, "
          f"{len(usage)} def_refs used")
    if dangling:
        print(f"WARNING: {len(dangling)} dangling def_refs (no atom found): {', '.join(dangling)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
