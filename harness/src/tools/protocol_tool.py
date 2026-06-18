from harness.src.retrieval.scope_filter import Scope, filter_scoped
from harness.src.tools.base import ToolContext, wrap_result


class ProtocolTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_protocol(self, protocol_id: str, os: str, version: str,
                     platform: str | None = None,
                     asic_family: str | None = None,
                     include_def_refs: bool = True) -> dict:
        doc = self._ctx.loader.get_protocol(protocol_id)
        if doc is None:
            doc = self._ctx.loader.get_concept(protocol_id)
        if doc is None:
            return wrap_result(
                "get_protocol",
                {"os": os, "version": version},
                None,
                kb_coverage="not_indexed",
            )

        platform_family = None
        if platform:
            platform_family = self._ctx.platform_resolver.resolve_family(platform)

        scope = Scope(os=os, version=version, platform_family=platform_family,
                      asic_family=asic_family)

        result = {
            "protocol_id": doc.get("protocol_id") or doc.get("concept_id"),
            "protocol_name": doc.get("protocol_name") or doc.get("concept_name"),
            "protocol_family": doc.get("protocol_family") or doc.get("concept_family"),
            "purpose": doc.get("purpose"),
            "confidence": doc.get("confidence"),
        }

        if "states" in doc:
            result["states"] = doc["states"]
        if "transitions" in doc:
            result["transitions"] = doc["transitions"]
        if "messages" in doc:
            result["messages"] = doc["messages"]
        if "dependencies" in doc:
            result["dependencies"] = doc["dependencies"]

        if "timers" in doc:
            result["timers"] = self._filter_timers(doc["timers"], scope)

        if "failure_modes" in doc:
            result["failure_modes"] = self._filter_failure_modes(
                doc["failure_modes"], scope
            )

        if "vendor_notes" in doc:
            vn = doc["vendor_notes"]
            if isinstance(vn, dict):
                result["vendor_notes"] = vn.get(os) or vn.get("*")
            else:
                result["vendor_notes"] = vn

        if include_def_refs and doc.get("def_refs"):
            enriched = self._ctx.resolver.inline_refs(doc)
            result["resolved_def_refs"] = enriched.get("resolved_def_refs", {})

        return wrap_result(
            "get_protocol",
            {"os": os, "version": version, "platform": platform},
            result,
        )

    def _filter_timers(self, timers: list[dict], scope: Scope) -> list[dict]:
        filtered = []
        for t in timers:
            entry = {k: v for k, v in t.items() if k != "os_defaults"}
            os_defaults = t.get("os_defaults", [])
            entry["os_defaults"] = filter_scoped(os_defaults, scope)
            filtered.append(entry)
        return filtered

    def _filter_failure_modes(self, fms: list[dict], scope: Scope) -> list[dict]:
        filtered = []
        for fm in fms:
            entry = {
                "scenario": fm.get("scenario"),
                "description": fm.get("description"),
                "symptoms": fm.get("symptoms", []),
                "diagnostic_tree_ref": fm.get("diagnostic_tree_ref"),
            }
            entry["root_causes"] = filter_scoped(fm.get("root_causes", []), scope)
            entry["resolutions"] = filter_scoped(fm.get("resolutions", []), scope)
            entry["verify_commands"] = filter_scoped(
                fm.get("verify_commands", []), scope
            )
            if entry["root_causes"] or entry["resolutions"] or entry["verify_commands"]:
                filtered.append(entry)
        return filtered
