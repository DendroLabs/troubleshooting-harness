#!/usr/bin/env python3
"""Build unified protocol files from the Cisco and SONiC importers.

Cisco loads first (RFC-level core), SONiC merges into matching protocol_ids.
Only the 6 exact-id overlaps merge (bfd, bgp-4, lacp, lldp, ospfv2,
static-routing). Distinct IDs in the STP and EVPN/VXLAN families are kept
separate and cross-linked via related_protocols rather than force-merged.

Writes data/protocols/<protocol_id>.json (sorted keys, 2-space indent).
"""
from __future__ import annotations

import json

import import_agent_cisco_kb
import import_cisco_kb
import import_sonic_kb
from common import DATA, Registry

# Families that are conceptually related but are distinct protocols — link, don't merge.
CROSS_LINK_FAMILIES = [
    ["rstp", "mst", "stp"],
    ["evpn", "vxlan", "vxlan-evpn"],
]


def cross_link(by_id: dict[str, dict]) -> None:
    for family in CROSS_LINK_FAMILIES:
        present = [pid for pid in family if pid in by_id]
        for pid in present:
            proto = by_id[pid]
            related = proto.setdefault("related_protocols", [])
            for other in present:
                if other != pid and other not in related:
                    related.append(other)


def main() -> int:
    reg = Registry()
    for proto in import_cisco_kb.load():
        reg.add(proto)
    cisco_ids = set(reg.by_id.keys())
    for proto in import_agent_cisco_kb.load(skip_ids=cisco_ids):
        reg.add(proto)
    for proto in import_sonic_kb.load():
        reg.add(proto)

    cross_link(reg.by_id)

    out_dir = DATA / "protocols"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clear stale protocol files so removed/skipped protocols don't linger.
    for stale in out_dir.glob("*.json"):
        if not stale.name.startswith("_"):
            stale.unlink()
    for proto in reg.values():
        path = out_dir / f"{proto['protocol_id']}.json"
        path.write_text(json.dumps(proto, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    merged = sorted(set(reg.merge_log))
    print(f"cisco dropped {import_cisco_kb._dropped_state_cmds} + "
          f"agent-cisco dropped {import_agent_cisco_kb._dropped_state_cmds} + "
          f"sonic dropped {import_sonic_kb._dropped_state_cmds} string-only state verify_commands")
    print(f"wrote {len(reg.by_id)} protocol files to data/protocols/")
    print(f"merged (both vendors): {', '.join(merged)}")
    if import_cisco_kb._concept_files:
        print(f"routed to concepts (cisco): {', '.join(import_cisco_kb._concept_files)}")
    if import_agent_cisco_kb._concept_files:
        print(f"routed to concepts (agent-cisco): {', '.join(import_agent_cisco_kb._concept_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
