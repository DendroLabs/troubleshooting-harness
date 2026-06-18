#!/usr/bin/env python3
"""Attach canonical cisco.com documentation URLs to protocol/concept files.

Reads manifest.json files from the raw-downloads command-refs cache.
Extracts og:url from HTML files and maps technology/feature-area directories
to protocol_ids. Re-runnable: deduplicates by URL before writing.

Only processes technology-grouped dirs (iosxe-base, iosxr feature_areas).
NX-OS and iosxe-catalyst chapters are alphabetical, not protocol-specific.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
CMD_REFS = REPO_ROOT / "archived-kb" / "agent-cisco-kb" / "raw-downloads" / "command-refs"

TECH_PROTOCOLS = {
    # iosxe-base technologies
    "iproute-bgp":   ["bgp-4"],
    "iproute-ospf":  ["ospfv2", "ospfv3"],
    "iproute-eigrp": ["eigrp"],
    "iproute-pi":    ["static-routing"],
    "fhrp":          ["hsrp", "vrrp"],
    "lanswitch":     ["rstp", "mst", "stp", "l2-infrastructure"],
    # iosxr feature areas
    "bgp":           ["bgp-4"],
    "routing":       ["ospfv2", "ospfv3", "isis", "bfd", "static-routing"],
    "mpls":          ["mpls-ldp"],
    "vpn-ethernet":  ["evpn", "vxlan", "vxlan-evpn"],
}

DIR_META = {
    "iosxe-base":              ("iosxe", None),
    "iosxr-cisco8000-252":     ("iosxr", "25.2"),
    "iosxr-cisco8000-242":     ("iosxr", "24.2"),
    "iosxr-cisco8000-75":      ("iosxr", "7.5"),
    "iosxr-ncs5500-252":       ("iosxr", "25.2"),
    "iosxr-ncs5500-242":       ("iosxr", "24.2"),
    "iosxr-ncs5500-75":        ("iosxr", "7.5"),
}


def extract_og_url(html_path: Path) -> str | None:
    try:
        with open(html_path) as f:
            for line in f:
                m = re.search(r'og:url.*?content="([^"]+)"', line)
                if m:
                    return m.group(1)
    except (OSError, UnicodeDecodeError):
        pass
    return None


def get_technology_urls(manifest_dir: Path, manifest: dict) -> dict[str, str]:
    """Map technology/feature_area → first og:url found in its subdir."""
    result = {}
    # iosxe-base: technologies is a dict {name: [file_paths]}
    for tech in manifest.get("technologies", {}):
        subdir = manifest_dir / tech
        if subdir.is_dir():
            for html in sorted(subdir.glob("*.html")):
                url = extract_og_url(html)
                if url:
                    result[tech] = url
                    break
    # iosxr: feature_areas is a list of subdir names
    for area in manifest.get("feature_areas", []):
        subdir = manifest_dir / area
        if subdir.is_dir():
            for html in sorted(subdir.glob("*.html")):
                url = extract_og_url(html)
                if url:
                    result[area] = url
                    break
    return result


def build_url_map() -> dict[str, list[dict]]:
    """Build protocol_id/concept_id → list of {url, os, version, source_dir}."""
    url_map: dict[str, list[dict]] = {}
    seen_urls: dict[str, set[str]] = {}

    for manifest_dir in sorted(CMD_REFS.iterdir()):
        dir_name = manifest_dir.name
        if dir_name not in DIR_META:
            continue
        manifest_path = manifest_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        os_name, version = DIR_META[dir_name]
        manifest = json.loads(manifest_path.read_text())
        tech_urls = get_technology_urls(manifest_dir, manifest)

        for tech, url in tech_urls.items():
            for pid in TECH_PROTOCOLS.get(tech, []):
                pid_seen = seen_urls.setdefault(pid, set())
                if url not in pid_seen:
                    url_map.setdefault(pid, []).append({
                        "url": url,
                        "os": os_name,
                        "version": version,
                        "source_dir": dir_name,
                    })
                    pid_seen.add(url)

    return url_map


def attach_urls(url_map: dict[str, list[dict]]) -> tuple[int, int]:
    updated = 0
    sources_added = 0

    for subdir, id_field in (("protocols", "protocol_id"), ("concepts", "concept_id")):
        data_dir = DATA / subdir
        if not data_dir.exists():
            continue
        for path in sorted(data_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue
            doc = json.loads(path.read_text())
            pid = doc.get(id_field)
            if pid not in url_map:
                continue

            existing_urls = {s.get("url") for s in doc.get("sources", []) if s.get("url")}
            added = False
            for entry in url_map[pid]:
                if entry["url"] in existing_urls:
                    continue
                ver_label = entry["version"] or "base"
                doc.setdefault("sources", []).append({
                    "id": f"cisco-doc:{entry['source_dir']}:{pid}",
                    "title": f"Cisco {entry['os'].upper()} {ver_label} command reference",
                    "type": "vendor_doc",
                    "url": entry["url"],
                })
                existing_urls.add(entry["url"])
                sources_added += 1
                added = True

            if added:
                path.write_text(
                    json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
                updated += 1

    return updated, sources_added


def main() -> int:
    url_map = build_url_map()
    total_urls = sum(len(v) for v in url_map.values())
    print(f"extracted {total_urls} URLs for {len(url_map)} protocols/concepts")
    for pid, entries in sorted(url_map.items()):
        oses = sorted({e["os"] for e in entries})
        print(f"  {pid:20} {len(entries):2} URLs ({', '.join(oses)})")

    updated, sources_added = attach_urls(url_map)
    print(f"\nupdated {updated} files, added {sources_added} vendor_doc sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
