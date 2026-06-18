from harness.src.tools.base import ToolContext, wrap_result


class PlatformTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_platform(self, platform_id: str) -> dict:
        row = self._ctx.platform_query.by_id(platform_id)
        if row is None:
            doc = self._ctx.loader.get_platform(platform_id)
            if doc is None:
                return wrap_result(
                    "get_platform", {"platform_id": platform_id},
                    None, kb_coverage="not_indexed",
                )
            return wrap_result(
                "get_platform", {"platform_id": platform_id},
                _summarize_platform_json(doc),
            )

        ports = self._ctx.platform_query.ports(platform_id)
        data = dict(row)
        data["ports"] = ports
        return wrap_result("get_platform", {"platform_id": platform_id}, data)

    def compare_platforms(self, platform_ids: list[str]) -> dict:
        platforms = []
        for pid in platform_ids:
            row = self._ctx.platform_query.by_id(pid)
            if row:
                ports = self._ctx.platform_query.ports(pid)
                entry = dict(row)
                entry["port_count"] = len(ports)
                platforms.append(entry)
            else:
                platforms.append({"platform_id": pid, "error": "not found"})

        kb = "indexed" if any("error" not in p for p in platforms) else "not_indexed"
        return wrap_result(
            "compare_platforms",
            {"platform_ids": platform_ids},
            {"platforms": platforms},
            kb_coverage=kb,
        )

    def get_scalability(self, platform_family: str, os: str,
                        version: str) -> dict:
        docs = self._ctx.loader.list_all("platforms")
        for doc in docs:
            scalability = doc.get("scalability", {})
            key = f"{os}-{version}"
            if key in scalability:
                return wrap_result(
                    "get_scalability",
                    {"platform_family": platform_family, "os": os, "version": version},
                    scalability[key],
                )
            for sk, sv in scalability.items():
                if sv.get("os") == os:
                    return wrap_result(
                        "get_scalability",
                        {"platform_family": platform_family, "os": os, "version": version},
                        sv,
                    )

        return wrap_result(
            "get_scalability",
            {"platform_family": platform_family, "os": os, "version": version},
            None,
            kb_coverage="not_indexed",
        )


def _summarize_platform_json(doc: dict) -> dict:
    return {
        "platform_id": doc.get("platform_id"),
        "platform_name": doc.get("platform_name"),
        "os": doc.get("os"),
        "platform_family": doc.get("platform_family"),
        "chassis_type": doc.get("chassis_type"),
        "total_bandwidth_tbps": doc.get("total_bandwidth_tbps"),
        "total_ports": doc.get("total_ports"),
        "asics": [
            {"asic_model": a.get("asic_model"), "asic_family": a.get("asic_family")}
            for a in doc.get("asics", [])
        ],
    }
