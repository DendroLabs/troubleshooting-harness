#!/usr/bin/env python3
"""Import SONiC shared-atom definitions into data/definitions/.

The SONiC KB ships daemons.json, redis_dbs.json and timers.json. Protocol
``def_refs`` (daemon:/db:/timer:) resolve against these, so they must exist
before the resolver can inline atoms. Source-only fields absent from
definition.schema.json (repo, source_path, human_error_note, sonic_version,
tuning_advice, sonic_*) are dropped; the operational SONiC timer values are
preserved per-protocol in each protocol's timer os_defaults.
"""
from __future__ import annotations

import json

from common import DATA, ARCHIVED, SCHEMA_VERSION, SONIC_VR

SONIC_DEFS = ARCHIVED / "sonic-kb" / "knowledge-base" / "definitions"


def _wrap(def_type: str, description: str, entries: list[dict]) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "def_type": def_type,
        "description": description,
        "entries": entries,
    }


def import_daemons() -> dict:
    raw = json.loads((SONIC_DEFS / "daemons.json").read_text())
    entries = []
    for d in raw:
        entry = {
            "def_id": d["def_id"],
            "def_type": "daemon",
            "process_name": d["process_name"],
            "os": "sonic",
            "version_range": dict(SONIC_VR),
            "purpose": d["purpose"],
        }
        for opt in ("container", "subscribes_to", "writes_to", "restart_command",
                    "restart_warning", "restart_safe", "related_daemons"):
            if opt in d:
                entry[opt] = d[opt]
        entries.append(entry)
    return _wrap("daemons", "SONiC daemons (FRR + SWSS + platform).", entries)


def import_databases() -> dict:
    raw = json.loads((SONIC_DEFS / "redis_dbs.json").read_text())
    entries = []
    for d in raw:
        entry = {
            "def_id": d["def_id"],
            "def_type": "database",
            "os": "sonic",
            "version_range": dict(SONIC_VR),
            "name": d["name"],
            "purpose": d["purpose"],
        }
        for opt in ("db_number", "separator", "written_by", "read_by",
                    "persistence", "human_error_risk"):
            if opt in d:
                entry[opt] = d[opt]
        entries.append(entry)
    return _wrap("databases", "SONiC Redis databases (DB 0-14).", entries)


def import_timers() -> dict:
    raw = json.loads((SONIC_DEFS / "timers.json").read_text())
    entries = []
    for t in raw:
        entry = {
            "def_id": t["def_id"],
            "def_type": "timer",
            "name": t["name"],
            # Source carries no description; synthesise a factual one from the
            # protocol + role rather than inventing detail.
            "description": f"{t['name']} ({t['protocol']} timer).",
        }
        if t.get("protocol"):
            entry["protocol"] = t["protocol"]
        if t.get("default"):
            entry["default_rfc"] = t["default"]
        if t.get("range"):
            entry["range"] = t["range"]
        if t.get("on_expiry"):
            entry["on_expiry"] = t["on_expiry"]
        entries.append(entry)
    return _wrap("timers", "Protocol timer atoms shared across the datastore.", entries)


def main() -> int:
    out_dir = DATA / "definitions"
    out_dir.mkdir(parents=True, exist_ok=True)
    builders = {
        "daemons.json": import_daemons,
        "databases.json": import_databases,
        "timers.json": import_timers,
    }
    for filename, builder in builders.items():
        doc = builder()
        (out_dir / filename).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote definitions/{filename}: {len(doc['entries'])} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
