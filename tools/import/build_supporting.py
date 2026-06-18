#!/usr/bin/env python3
"""Build all Phase 3 supporting data types into data/.

Writes:
  data/diagnostics/<tree_id>.json
  data/human-errors/<error_id>.json
  data/procedures/<procedure_id>.json
  data/platforms/<platform_id>.json        (hardware models + scalability families)
  data/definitions/asic-families.json      (def atom referenced by platforms)

All files: 2-space indent, sorted keys, trailing newline — matching build_protocols
/ build_concepts. Stale non-index files in each target dir are removed first so the
build is reproducible.
"""
from __future__ import annotations

import json

from common import DATA
import import_diagnostics
import import_human_errors
import import_procedures
import import_platforms
import import_asic_families
import import_best_practices


def _write_dir(subdir: str, docs: list[dict], id_field: str) -> None:
    out_dir = DATA / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.json"):
        if not stale.name.startswith("_"):
            stale.unlink()
    for doc in docs:
        path = out_dir / f"{doc[id_field]}.json"
        path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def main() -> int:
    diagnostics = import_diagnostics.load()
    _write_dir("diagnostics", diagnostics, "tree_id")
    print(f"wrote {len(diagnostics)} diagnostic trees to data/diagnostics/")

    human_errors = import_human_errors.load()
    _write_dir("human-errors", human_errors, "error_id")
    print(f"wrote {len(human_errors)} human-error patterns to data/human-errors/")

    procedures = import_procedures.load()
    _write_dir("procedures", procedures, "procedure_id")
    print(f"wrote {len(procedures)} procedures to data/procedures/ "
          f"(dropped {import_procedures.DROPPED_FAILURE_MODES} cisco procedure-level failure_modes)")

    platforms = import_platforms.load()
    _write_dir("platforms", platforms, "platform_id")
    hw = sum(1 for p in platforms if "scalability" not in p)
    print(f"wrote {len(platforms)} platform docs to data/platforms/ "
          f"({hw} hardware + {len(platforms) - hw} scalability)")

    best_practices = import_best_practices.load()
    _write_dir("best-practices", best_practices, "best_practice_id")
    print(f"wrote {len(best_practices)} best-practice indexes to data/best-practices/")

    asic_doc = import_asic_families.build()
    (DATA / "definitions" / "asic-families.json").write_text(
        json.dumps(asic_doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"wrote data/definitions/asic-families.json ({len(asic_doc['entries'])} families)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
