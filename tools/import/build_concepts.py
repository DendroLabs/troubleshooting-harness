#!/usr/bin/env python3
"""Build concept files from the concept importer.

Writes data/concepts/<concept_id>.json (sorted keys, 2-space indent).
"""
from __future__ import annotations

import json

from common import DATA
import import_concepts


def main() -> int:
    concepts = import_concepts.load()

    out_dir = DATA / "concepts"
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.json"):
        if not stale.name.startswith("_"):
            stale.unlink()
    for concept in concepts:
        path = out_dir / f"{concept['concept_id']}.json"
        path.write_text(json.dumps(concept, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    print(f"wrote {len(concepts)} concept files to data/concepts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
