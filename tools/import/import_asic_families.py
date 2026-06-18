#!/usr/bin/env python3
"""Build the asic-families definition atom from platform hardware references.

Every distinct ``asic_family`` referenced by a hardware platform doc becomes one
asic_family entry (def_id, vendor, platforms list). Descriptions stay factual and
minimal — we do not invent pipeline/capability details that aren't in the source.

Exposes ``build() -> definition_doc`` for build_supporting.py.
"""
from __future__ import annotations

import import_platforms
from common import SCHEMA_VERSION

# The only non-Cisco ASIC families present in the Cisco hardware topology.
NON_CISCO_VENDORS = {
    "asic:trident2": "Broadcom",
}


def build() -> dict:
    platforms = import_platforms.load()
    registry = import_platforms.asic_registry(platforms)

    entries = []
    for def_id in sorted(registry):
        name = registry[def_id]["name"]
        plats = registry[def_id]["platforms"]
        vendor = NON_CISCO_VENDORS.get(def_id, "Cisco")
        entries.append({
            "def_id": def_id,
            "def_type": "asic_family",
            "name": name,
            "vendor": vendor,
            "description": (
                f"{vendor} {name} ASIC family. Referenced by "
                f"{len(plats)} platform topology file(s) in the dataset."
            ),
            "platforms": plats,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "def_type": "asic_families",
        "description": "ASIC families referenced by hardware platform topology files.",
        "entries": entries,
    }


if __name__ == "__main__":
    doc = build()
    print(f"asic-families: {len(doc['entries'])} entries")
    for e in doc["entries"]:
        print(f"  {e['def_id']:28} {e['vendor']:9} {len(e['platforms'])} platforms")
