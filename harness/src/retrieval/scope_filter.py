import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    os: str
    version: str
    platform_family: str | None = None
    asic_family: str | None = None


def version_in_range(version: str, version_range: dict, os: str = "") -> bool:
    vmin = version_range.get("min", "*")
    vmax = version_range.get("max", "*")
    if vmin == "*" and vmax == "*":
        return True
    if version == "*":
        return True
    cmp = _compare_versions
    if vmin != "*" and cmp(version, vmin, os) < 0:
        return False
    if vmax != "*" and cmp(version, vmax, os) > 0:
        return False
    return True


def matches_scope(item: dict, scope: Scope) -> bool:
    item_os = item.get("os", "*")
    if item_os != "*" and scope.os != "*" and item_os != scope.os:
        return False

    vr = item.get("version_range")
    versions = item.get("versions")
    if vr:
        if not version_in_range(scope.version, vr, scope.os):
            return False
    elif versions:
        if scope.version != "*" and scope.version not in versions:
            return False

    if scope.platform_family:
        platforms = item.get("platforms")
        if platforms is not None and scope.platform_family not in platforms:
            return False

    if scope.asic_family:
        item_asic = item.get("asic_family")
        if item_asic is not None and item_asic != scope.asic_family:
            return False

    return True


def filter_scoped(items: list[dict], scope: Scope) -> list[dict]:
    return [item for item in items if matches_scope(item, scope)]


_NXOS_RE = re.compile(r"^(\d+)\.(\d+)(?:\((\d+)\))?")


def _parse_version(v: str, os: str) -> tuple:
    if os == "sonic" and v.isdigit():
        return (int(v),)
    m = _NXOS_RE.match(v)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
    parts = re.split(r"[.\-]", v)
    result = []
    for p in parts:
        digits = re.match(r"(\d+)", p)
        result.append(int(digits.group(1)) if digits else 0)
    return tuple(result) if result else (0,)


def _compare_versions(a: str, b: str, os: str) -> int:
    pa, pb = _parse_version(a, os), _parse_version(b, os)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0
