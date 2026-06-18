#!/usr/bin/env python3
"""Populate platforms.db from data/platforms/ JSON files."""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
PLATFORMS_DIR = DATA / "platforms"


def _strip_asic_prefix(asic_family: str | None) -> str | None:
    if asic_family and asic_family.startswith("asic:"):
        return asic_family[5:]
    return asic_family


def _load_platforms() -> tuple[list[tuple], list[tuple]]:
    """Return (platform_rows, port_rows) from all platform JSON files."""
    platform_rows = []
    port_rows = []

    for path in sorted(PLATFORMS_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        doc = json.loads(path.read_text())

        platform_id = doc.get("platform_id", path.stem)
        platform_family = doc.get("platform_family", "")
        os_name = doc.get("os", "")
        chassis_type = doc.get("chassis_type")
        total_ports = doc.get("total_ports")
        total_bw = doc.get("total_bandwidth_tbps")

        asics = doc.get("asics", [])
        asic_family = None
        asic_model = None
        if asics:
            asic_family = _strip_asic_prefix(asics[0].get("asic_family"))
            asic_model = asics[0].get("asic_model")

        platform_rows.append((
            platform_id,
            platform_family,
            os_name,
            chassis_type,
            asic_family,
            asic_model,
            total_ports,
            total_bw,
        ))

        for asic in asics:
            asic_id = asic.get("asic_id")
            for slc in asic.get("slices", []):
                slice_id = slc.get("slice_id")
                for port in slc.get("ports", []):
                    label = port.get("label", "")
                    native_speed = port.get("native_speed", "")
                    breakout = json.dumps(port.get("breakout_options", []))
                    port_rows.append((
                        platform_id,
                        asic_id,
                        slice_id,
                        label,
                        native_speed,
                        breakout,
                    ))

    return platform_rows, port_rows


def populate(db_path: Path) -> dict:
    platform_rows, port_rows = _load_platforms()

    conn = sqlite3.connect(str(db_path))
    conn.execute("DELETE FROM platform_ports")
    conn.execute("DELETE FROM platforms")

    for row in platform_rows:
        conn.execute(
            "INSERT OR REPLACE INTO platforms "
            "(platform_id, platform_family, os, chassis_type, "
            "asic_family, asic_model, total_ports, total_bandwidth_tbps) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )

    for row in port_rows:
        conn.execute(
            "INSERT OR REPLACE INTO platform_ports "
            "(platform_id, asic_id, slice_id, port_label, "
            "native_speed, breakout_options) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            row,
        )

    plat_count = conn.execute("SELECT COUNT(*) FROM platforms").fetchone()[0]
    port_count = conn.execute("SELECT COUNT(*) FROM platform_ports").fetchone()[0]
    conn.commit()
    conn.close()
    return {"platforms": plat_count, "ports": port_count}


if __name__ == "__main__":
    db = DATA / "db" / "platforms.db"
    result = populate(db)
    print(f"platforms.db: {result['platforms']} platforms, {result['ports']} port groups")
