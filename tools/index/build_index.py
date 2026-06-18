#!/usr/bin/env python3
"""Build data/protocols/_index.json and the master data/_index.json.

The protocol index is a lightweight catalogue (id, name, family, file, tags,
os_coverage) for fast listing without loading every full protocol file.
"""
from __future__ import annotations

import json

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"


def os_coverage(proto: dict) -> list[str]:
    """Distinct OSes that carry operational data in this protocol (excl. '*')."""
    found: set[str] = set()
    for timer in proto.get("timers", []):
        for d in timer.get("os_defaults", []):
            found.add(d["os"])
    for fm in proto.get("failure_modes", []):
        for c in fm.get("root_causes", []):
            found.add(c["os"])
        for r in fm.get("resolutions", []):
            found.add(r["os"])
        for v in fm.get("verify_commands", []):
            found.add(v["os"])
    found.update(proto.get("vendor_notes", {}).keys())
    found.discard("*")
    return sorted(found)


def build_protocol_index() -> list[dict]:
    entries = []
    for path in sorted((DATA / "protocols").glob("*.json")):
        if path.name.startswith("_"):
            continue
        proto = json.loads(path.read_text())
        entries.append({
            "protocol_id": proto["protocol_id"],
            "protocol_name": proto["protocol_name"],
            "protocol_family": proto["protocol_family"],
            "file": f"protocols/{path.name}",
            "tags": proto.get("tags", []),
            "os_coverage": os_coverage(proto),
        })
    return entries


def count_data_files(subdir: str) -> int:
    root = DATA / subdir
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*.json") if not p.name.startswith("_"))


def main() -> int:
    proto_index = build_protocol_index()
    (DATA / "protocols" / "_index.json").write_text(
        json.dumps({"schema_version": "1.0.0", "protocols": proto_index}, indent=2,
                   ensure_ascii=False) + "\n")

    master = {
        "schema_version": "1.0.0",
        "datasets": {
            "protocols": {"count": len(proto_index), "index": "protocols/_index.json"},
            "definitions": {"count": count_data_files("definitions")},
            "diagnostics": {"count": count_data_files("diagnostics")},
            "procedures": {"count": count_data_files("procedures")},
            "human-errors": {"count": count_data_files("human-errors")},
            "platforms": {"count": count_data_files("platforms")},
            "concepts": {"count": count_data_files("concepts")},
            "best-practices": {"count": count_data_files("best-practices")},
            "interpretation-rules": {"count": count_data_files("interpretation-rules")},
        },
    }
    (DATA / "_index.json").write_text(json.dumps(master, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote protocols/_index.json ({len(proto_index)} protocols) and data/_index.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
