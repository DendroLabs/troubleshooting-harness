#!/usr/bin/env python3
"""Shared helpers for the Phase 2 protocol importers.

All operational data points produced here carry an explicit applicability scope
(os + version_range). Source provenance is synthesised at a baseline level
(RFC reference + originating-KB pointer, confidence "medium"); the Step B
sourcing pass upgrades these with verified quotes and authoritative doc URLs.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
ARCHIVED = REPO_ROOT / "archived-kb"

SCHEMA_VERSION = "1.0.0"
CONFIDENCE = "medium"

# Applicability constants.
ALL_VR = {"min": "*", "max": "*"}          # universal / vendor-agnostic
SONIC_VR = {"min": "202511", "max": "*"}   # SONiC release floor (Nov 2025 image)
CISCO_OSES = ["nxos", "iosxe", "iosxr"]     # OSes the Cisco KB targets

# Cisco dependency.type values that are not in the target enum
# [protocol, daemon, infrastructure, database, service].
DEP_TYPE_MAP = {
    "transport": "infrastructure",
    "config": "infrastructure",
    "hardware": "infrastructure",
}
VALID_DEP_TYPES = {"protocol", "daemon", "infrastructure", "database", "service"}


def norm(text: str) -> str:
    """Normalise a name/scenario for dedup matching: lowercase, alnum only."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def map_dependency_type(dep_type: str) -> str:
    if dep_type in VALID_DEP_TYPES:
        return dep_type
    return DEP_TYPE_MAP.get(dep_type, "infrastructure")


# --- source synthesis -------------------------------------------------------

def parse_standards(standard: str) -> list[dict]:
    """Derive structured sources from a free-text ``standard`` field.

    Handles RFC references (possibly several, comma-separated), IEEE/ITU
    standards, and other named standards. Vendor-proprietary strings yield no
    source (provenance covers them). No verifying_quote — Step B adds those.
    """
    sources: list[dict] = []
    standard = (standard or "").strip()
    if not standard:
        return sources

    rfc_nums = [int(n) for n in re.findall(r"RFC\s*(\d+)", standard, flags=re.I)]
    for num in rfc_nums:
        sources.append(
            {
                "id": f"rfc-{num}",
                "title": f"RFC {num}",
                "type": "rfc",
                "rfc_number": num,
                "url": f"https://www.rfc-editor.org/rfc/rfc{num}.txt",
            }
        )
    if rfc_nums:
        return sources

    if re.search(r"\bIEEE\b", standard, flags=re.I):
        sources.append({"id": f"ieee-{norm(standard)}", "title": standard, "type": "ieee_standard"})
    elif re.search(r"\bITU\b", standard, flags=re.I):
        sources.append({"id": f"itu-{norm(standard)}", "title": standard, "type": "itu_standard"})
    elif "proprietary" not in standard.lower():
        sources.append({"id": f"std-{norm(standard)}", "title": standard, "type": "standard"})
    return sources


def provenance_source(kb_name: str, rel_path: str) -> dict:
    """A pointer back to the originating KB file this data was imported from."""
    return {
        "id": f"{kb_name}:{rel_path}",
        "title": f"{kb_name} knowledge base — {rel_path}",
        "type": "documentation",
    }


# --- scoped operational-data builders ---------------------------------------

def scoped_cause(cause: str, os: str, version_range: dict) -> dict:
    return {"cause": cause, "os": os, "version_range": copy.deepcopy(version_range)}


def scoped_resolution(action: str, os: str, version_range: dict, command: str | None = None) -> dict:
    out = {"action": action, "os": os, "version_range": copy.deepcopy(version_range)}
    if command:
        out["command"] = command
    return out


def verify_cmd(src: dict, os: str, version_range: dict) -> dict:
    return {
        "os": os,
        "version_range": copy.deepcopy(version_range),
        "command": src["command"],
        "look_for": src.get("look_for", ""),
        "confirms_if": src.get("confirms_if", ""),
    }


# --- merge registry ---------------------------------------------------------

def _dedup_append(target: list, items: list, key):
    """Append items whose key() is not already present in target."""
    seen = {key(x) for x in target}
    for item in items:
        k = key(item)
        if k not in seen:
            target.append(item)
            seen.add(k)


class Registry:
    """Accumulates protocols keyed by protocol_id, merging on exact-id collision.

    Distinct protocol IDs (e.g. cisco rstp/mst vs sonic stp) are NOT merged —
    they are kept as separate files and cross-linked elsewhere.
    """

    def __init__(self) -> None:
        self.by_id: dict[str, dict] = {}
        self.merge_log: list[str] = []

    def add(self, proto: dict) -> None:
        pid = proto["protocol_id"]
        if pid not in self.by_id:
            self.by_id[pid] = copy.deepcopy(proto)
        else:
            self._merge(self.by_id[pid], proto)
            self.merge_log.append(pid)

    def _merge(self, base: dict, inc: dict) -> None:
        # Scalar core fields: fill gaps, keep base (Cisco/first as RFC core).
        for field in ("protocol_name", "protocol_family", "standard", "purpose",
                      "operates_at", "transport"):
            if not base.get(field) and inc.get(field):
                base[field] = inc[field]

        # states / transitions / messages: union by identity.
        base.setdefault("states", [])
        _dedup_append(base["states"], inc.get("states", []), lambda s: norm(s["name"]))
        base.setdefault("transitions", [])
        _dedup_append(base["transitions"], inc.get("transitions", []),
                      lambda t: (norm(t["from_state"]), norm(t["to_state"]), norm(t["trigger"])))
        base.setdefault("messages", [])
        _dedup_append(base["messages"], inc.get("messages", []), lambda m: norm(m["name"]))

        # timers: merge os_defaults on matching name, else append.
        base.setdefault("timers", [])
        base_timers = {norm(t["name"]): t for t in base["timers"]}
        for timer in inc.get("timers", []):
            match = base_timers.get(norm(timer["name"]))
            if match:
                match.setdefault("os_defaults", [])
                _dedup_append(match["os_defaults"], timer.get("os_defaults", []),
                              lambda d: (d["os"], d.get("default")))
            else:
                base["timers"].append(timer)
                base_timers[norm(timer["name"])] = timer

        # failure_modes: merge contents on matching scenario, else append.
        base.setdefault("failure_modes", [])
        base_fm = {norm(f["scenario"]): f for f in base["failure_modes"]}
        for fm in inc.get("failure_modes", []):
            match = base_fm.get(norm(fm["scenario"]))
            if match:
                _dedup_append(match["symptoms"], fm.get("symptoms", []), norm)
                _dedup_append(match["root_causes"], fm.get("root_causes", []),
                              lambda c: (norm(c["cause"]), c["os"]))
                _dedup_append(match["resolutions"], fm.get("resolutions", []),
                              lambda r: (norm(r["action"]), r["os"]))
                match.setdefault("verify_commands", [])
                _dedup_append(match["verify_commands"], fm.get("verify_commands", []),
                              lambda v: (norm(v["command"]), v["os"]))
            else:
                base["failure_modes"].append(fm)
                base_fm[norm(fm["scenario"])] = fm

        # dependencies: union by (type, name).
        base.setdefault("dependencies", [])
        _dedup_append(base["dependencies"], inc.get("dependencies", []),
                      lambda d: (d["type"], norm(d["name"])))

        # def_refs / tags / related_protocols: ordered union.
        for field in ("def_refs", "tags", "related_protocols"):
            base.setdefault(field, [])
            _dedup_append(base[field], inc.get(field, []), lambda x: x)

        # vendor_notes: merge per-OS keys (cisco OS keys vs sonic don't collide).
        base.setdefault("vendor_notes", {})
        for os_key, notes in inc.get("vendor_notes", {}).items():
            base["vendor_notes"].setdefault(os_key, notes)

        # sources: union by id.
        base.setdefault("sources", [])
        _dedup_append(base["sources"], inc.get("sources", []), lambda s: s["id"])

    def values(self) -> list[dict]:
        return list(self.by_id.values())
