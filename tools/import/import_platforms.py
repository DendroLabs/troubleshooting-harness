#!/usr/bin/env python3
"""Transform Cisco hardware-topology + verified-scalability into platform docs.

Both source families land in data/platforms/ as platform.schema.json files.

  Hardware (one file per model): asics/slices/ports already match the schema
  field-for-field, so they pass through unchanged except that ``asic_family`` is
  normalised from a display string ("Cloud Scale FX") to its def_id ("asic:cloud-
  scale-fx") so it cross-references data/definitions/asic-families.json. The
  diagram_*, troubleshooting_notes, asic_links, fabric_modules, related_platforms
  and tags fields have no home in the schema and are dropped; the free-text
  ``source`` becomes a documentation source.

  Scalability (several files per family/version): the section/profile/entry shape
  already matches the schema's scalability $defs. All version files for one family
  merge into a single family-level platform doc whose ``scalability`` map is keyed
  by "<os>-<version>". These carry no asics — just the per-version limits.

Exposes ``load() -> list[platform]`` and ``asic_registry(platforms)``.
"""
from __future__ import annotations

import copy
import json
import re

from common import (
    ARCHIVED, ALL_VR, SCHEMA_VERSION, CONFIDENCE, provenance_source,
)

HARDWARE = ARCHIVED / "cisco-kb" / "hardware-topology"
SCALABILITY = ARCHIVED / "cisco-kb" / "verified-scalability"

# Readable family names for the synthesised scalability platform docs.
FAMILY_NAMES = {
    "nexus-9000": "Nexus 9000 Series",
    "catalyst-9300": "Catalyst 9300 Series",
    "cisco-8000": "Cisco 8000 Series",
    "ncs-5500": "NCS 5500 Series",
}


def asic_def_id(family: str) -> str:
    """'Cloud Scale FX' -> 'asic:cloud-scale-fx'; 'Adelaide (M2)' -> 'asic:adelaide-m2'."""
    slug = re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")
    return f"asic:{slug}"


# --- hardware ---------------------------------------------------------------

def _transform_asic(raw: dict) -> dict:
    asic = {
        "asic_id": raw["asic_id"],
        "asic_model": raw["asic_model"],
        "asic_family": asic_def_id(raw["asic_family"]),
    }
    for field in ("total_bandwidth_gbps", "sms_mb", "hbm_gb", "memory_tables", "slices"):
        if field in raw:
            asic[field] = raw[field]
    return asic


def _transform_hardware(raw: dict, rel_path: str) -> dict:
    plat = {
        "schema_version": SCHEMA_VERSION,
        "confidence": CONFIDENCE,
        "platform_id": raw["platform_id"],
        "platform_name": raw["platform_name"],
        "os": raw["os"],
        "platform_family": raw["platform_family"],
        "sources": [provenance_source("cisco", rel_path)],
    }
    for field in ("platform_pid", "total_bandwidth_tbps", "total_ports"):
        if field in raw:
            plat[field] = raw[field]
    # The schema's chassis_type enum is {fixed, modular}; Nexus 7000 line-card
    # entries carry "line_card", which has no enum slot — omit it (the platform_id
    # and family already identify them as modules) rather than mislabel them.
    if raw.get("chassis_type") in ("fixed", "modular"):
        plat["chassis_type"] = raw["chassis_type"]
    if raw.get("asics"):
        plat["asics"] = [_transform_asic(a) for a in raw["asics"]]
    if raw.get("source"):
        plat["sources"].insert(0, {
            "id": f"cisco-hw-{raw['platform_id']}",
            "title": raw["source"],
            "type": "documentation",
        })
    return plat


# --- scalability ------------------------------------------------------------

def _scalability_entry(raw: dict) -> dict:
    entry = {"os": raw["os"], "version": raw["version"], "sections": raw["sections"]}
    if raw.get("source_url"):
        entry["source_url"] = raw["source_url"]
    return entry


def _scalability_platforms() -> list[dict]:
    """Merge every verified-scalability file into one platform doc per family."""
    by_family: dict[str, dict] = {}
    for path in sorted(SCALABILITY.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        family = raw["platform"]
        rel_path = f"verified-scalability/{path.parent.name}/{path.name}"

        plat = by_family.get(family)
        if plat is None:
            plat = {
                "schema_version": SCHEMA_VERSION,
                "confidence": CONFIDENCE,
                "platform_id": family,
                "platform_name": FAMILY_NAMES.get(family, family),
                "os": raw["os"],
                "platform_family": family,
                "scalability": {},
                "sources": [],
            }
            by_family[family] = plat

        key = f"{raw['os']}-{raw['version']}"
        plat["scalability"][key] = _scalability_entry(raw)
        plat["sources"].append(provenance_source("cisco", rel_path))
        if raw.get("source_url"):
            plat["sources"].append({
                "id": f"cisco-scale-{key}",
                "title": f"Cisco Verified Scalability Guide — {plat['platform_name']} {raw['version']}",
                "type": "vendor_doc",
                "url": raw["source_url"],
            })
    return list(by_family.values())


def load() -> list[dict]:
    platforms = []
    for path in sorted(HARDWARE.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        rel_path = f"hardware-topology/{path.parent.name}/{path.name}"
        platforms.append(_transform_hardware(raw, rel_path))
    platforms.extend(_scalability_platforms())
    return platforms


def asic_registry(platforms: list[dict]) -> dict[str, dict]:
    """def_id -> {'name': display, 'platforms': sorted[platform_id]} over hardware docs."""
    # Reverse the def_id back to a display name by re-reading source families,
    # so the atom keeps the human-readable name rather than the slug.
    display = {}
    for path in HARDWARE.rglob("*.json"):
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        for a in raw.get("asics", []):
            display[asic_def_id(a["asic_family"])] = a["asic_family"]

    registry: dict[str, dict] = {}
    for plat in platforms:
        for a in plat.get("asics", []):
            did = a["asic_family"]
            reg = registry.setdefault(did, {"name": display.get(did, did), "platforms": set()})
            reg["platforms"].add(plat["platform_id"])
    for reg in registry.values():
        reg["platforms"] = sorted(reg["platforms"])
    return registry


if __name__ == "__main__":
    plats = load()
    hw = [p for p in plats if "scalability" not in p]
    sc = [p for p in plats if "scalability" in p]
    print(f"platforms: {len(hw)} hardware + {len(sc)} scalability = {len(plats)} docs")
    reg = asic_registry(plats)
    print(f"asic families referenced: {len(reg)}")
    for did in sorted(reg):
        print(f"  {did:28} {len(reg[did]['platforms'])} platforms")
