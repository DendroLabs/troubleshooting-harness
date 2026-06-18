#!/usr/bin/env python3
"""Build the RFC catalog and attach verifying quotes to protocol sources.

Two modes:
  --scan     List RFCs referenced by protocols (dry run, no fetch)
  --process  Read cached RFC texts, extract quotes, update protocol files

RFC texts must be fetched via PIF (pif_fetch) and cached in data/references/rfc/
before --process can run. The --scan output shows what needs fetching.

Re-runnable: skips protocols that already have verifying_quote populated.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
RFC_CACHE = DATA / "references" / "rfc"

MAX_QUOTE_LEN = 250

# protocol_id → list of key search terms for RFC quote extraction.
# Falls back to protocol_name if not listed.
SEARCH_TERMS: dict[str, list[str]] = {
    "bgp-4": ["BGP", "Border Gateway Protocol", "autonomous system"],
    "ospfv2": ["OSPF", "Open Shortest Path First", "link state"],
    "ospfv3": ["OSPF", "Open Shortest Path First", "IPv6"],
    "bfd": ["BFD", "Bidirectional Forwarding Detection"],
    "isis": ["IS-IS", "Intermediate System", "link state"],
    "eigrp": ["EIGRP", "Enhanced Interior Gateway"],
    "hsrp": ["HSRP", "Hot Standby Router"],
    "vrrp": ["VRRP", "Virtual Router Redundancy"],
    "mpls-ldp": ["LDP", "Label Distribution Protocol", "MPLS"],
    "evpn": ["EVPN", "Ethernet VPN", "BGP MPLS"],
    "vxlan": ["VXLAN", "Virtual eXtensible", "Network Identifier"],
    "vxlan-evpn": ["VXLAN", "EVPN", "Network Virtualization Overlay"],
    "mclag": ["ICCP", "Inter-Chassis Communication"],
    "static-routing": ["static route", "routing table"],
}


def scan_rfcs() -> dict[int, list[str]]:
    """Return {rfc_number: [protocol_ids]} from all protocol/concept files."""
    rfcs: dict[int, list[str]] = {}
    for subdir, id_field in (("protocols", "protocol_id"), ("concepts", "concept_id")):
        d = DATA / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.json")):
            if p.name.startswith("_"):
                continue
            doc = json.loads(p.read_text())
            pid = doc.get(id_field)
            for s in doc.get("sources", []):
                if s.get("type") == "rfc" and s.get("rfc_number"):
                    rfcs.setdefault(s["rfc_number"], []).append(pid)
    return rfcs


_SECTION_ANCHOR = re.compile(
    r"^\s*(Status of [Tt]his Memo|Abstract|Table of Contents)\b", re.I)
_MONTH_YEAR = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{4}$", re.I)
_HEADER_KW = re.compile(
    r"(Request for Comments|Category:|Status:|ISSN:|STD:|BCP:|Obsoletes:|"
    r"Updates:|Network Working Group|Internet Engineering|Independent Submission)",
    re.I)


def parse_rfc_title(text: str) -> str:
    """Extract an RFC title.

    The title is a centered block that sits between the two-column header
    (author/affiliation/date) and the first 'Abstract'/'Status of this Memo'
    section. Walk backward from that section anchor, collecting the contiguous
    block of centered, indented lines — that block is the title.
    """
    lines = text.split("\n")
    anchor = next((i for i, ln in enumerate(lines) if _SECTION_ANCHOR.match(ln)), None)
    if anchor is None:
        return "Unknown"

    collected: list[str] = []
    for ln in reversed(lines[:anchor]):
        stripped = ln.strip()
        if not stripped:
            if collected:
                break  # blank line above the title block ends it
            continue
        # A title line is indented (header keywords start at column 0) and
        # carries no header keyword/date. Long titles may indent only 1-2 spaces,
        # so the discriminator is column-0 vs indented, not a fixed width.
        indent = len(ln) - len(ln.lstrip())
        if indent < 1 or _HEADER_KW.search(stripped) or _MONTH_YEAR.match(stripped):
            break
        collected.append(stripped)
    return " ".join(reversed(collected)) if collected else "Unknown"


def extract_quote(rfc_text: str, search_terms: list[str], title: str = "") -> str | None:
    """Find the first substantive RFC paragraph mentioning a search term.

    Requires prose (sentence punctuation, reasonable length) and rejects the
    title line and table-of-contents entries (dotted leaders) so the quote is
    always a real descriptive paragraph — typically the Abstract or Introduction.
    """
    # Drop only the PIF sanitization banner (first line), keep the body.
    body = "\n".join(rfc_text.split("\n")[1:])
    paragraphs = re.split(r"\n\s*\n", body)
    for para in paragraphs:
        clean = " ".join(para.split())
        # Require real prose; reject TOC (4+ dotted leaders) and the title.
        if len(clean) < 80 or ". " not in clean or "...." in clean:
            continue
        if title and clean.startswith(title):
            continue
        for term in search_terms:
            if term.lower() in clean.lower():
                if len(clean) > MAX_QUOTE_LEN:
                    return clean[:MAX_QUOTE_LEN].rstrip() + "..."
                return clean
    return None


def process(rfcs: dict[int, list[str]]) -> None:
    """Read cached RFCs, extract quotes, update protocol files, build catalog."""
    RFC_CACHE.mkdir(parents=True, exist_ok=True)
    catalog_entries = []
    quote_map: dict[str, dict[int, str]] = {}  # pid → {rfc_num: quote}

    for rfc_num in sorted(rfcs):
        rfc_path = RFC_CACHE / f"rfc{rfc_num}.txt"
        if not rfc_path.exists():
            print(f"  SKIP rfc{rfc_num}.txt (not cached — fetch via pif_fetch first)")
            continue

        text = rfc_path.read_text(errors="replace")
        title = parse_rfc_title(text)
        catalog_entries.append({
            "rfc_number": rfc_num,
            "title": title,
            "url": f"https://www.rfc-editor.org/rfc/rfc{rfc_num}.txt",
            "protocols_referencing": sorted(rfcs[rfc_num]),
        })

        for pid in rfcs[rfc_num]:
            terms = SEARCH_TERMS.get(pid, [pid.replace("-", " ")])
            quote = extract_quote(text, terms, title)
            if quote:
                quote_map.setdefault(pid, {})[rfc_num] = quote

    # Write catalog
    catalog = {"schema_version": "1.0.0", "rfcs": catalog_entries}
    catalog_path = DATA / "references" / "rfc-catalog.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {catalog_path.relative_to(REPO_ROOT)} ({len(catalog_entries)} RFCs)")

    # Update protocol/concept files with verifying_quote and confidence
    updated = 0
    for subdir, id_field in (("protocols", "protocol_id"), ("concepts", "concept_id")):
        d = DATA / subdir
        if not d.exists():
            continue
        for path in sorted(d.glob("*.json")):
            if path.name.startswith("_"):
                continue
            doc = json.loads(path.read_text())
            pid = doc.get(id_field)
            if pid not in quote_map:
                continue

            changed = False
            for src in doc.get("sources", []):
                if src.get("type") != "rfc" or not src.get("rfc_number"):
                    continue
                if src.get("verifying_quote"):
                    continue
                rfc_num = src["rfc_number"]
                if rfc_num in quote_map.get(pid, {}):
                    src["verifying_quote"] = quote_map[pid][rfc_num]
                    changed = True

            if changed:
                has_any_quote = any(
                    s.get("verifying_quote") for s in doc.get("sources", [])
                    if s.get("type") == "rfc"
                )
                if has_any_quote and doc.get("confidence") == "medium":
                    doc["confidence"] = "high"
                path.write_text(
                    json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
                updated += 1
                print(f"  updated {pid}: {len(quote_map[pid])} quotes, "
                      f"confidence={doc.get('confidence')}")

    print(f"updated {updated} files with verifying quotes")


def main() -> int:
    rfcs = scan_rfcs()
    if "--scan" in sys.argv or len(sys.argv) < 2:
        print(f"{len(rfcs)} unique RFCs referenced:")
        for num, pids in sorted(rfcs.items()):
            cached = (RFC_CACHE / f"rfc{num}.txt").exists()
            status = "cached" if cached else "NEEDS FETCH"
            print(f"  RFC {num:5} [{status:11}] → {', '.join(pids)}")
        uncached = [n for n in rfcs if not (RFC_CACHE / f"rfc{n}.txt").exists()]
        if uncached:
            print(f"\n{len(uncached)} RFCs need fetching. URLs:")
            for n in sorted(uncached):
                print(f"  https://www.rfc-editor.org/rfc/rfc{n}.txt")
        return 0

    if "--process" in sys.argv:
        process(rfcs)
        return 0

    print("usage: build_rfc_catalog.py [--scan | --process]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
