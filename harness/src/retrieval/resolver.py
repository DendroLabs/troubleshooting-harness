from harness.src.retrieval.json_loader import JsonLoader


class DefIdResolver:

    def __init__(self, loader: JsonLoader):
        self._loader = loader
        self._index: dict[str, dict] | None = None

    def resolve(self, def_id: str) -> dict | None:
        self._ensure_index()
        return self._index.get(def_id)

    def resolve_all(self, def_refs: list[str]) -> dict[str, dict | None]:
        self._ensure_index()
        return {did: self._index.get(did) for did in def_refs}

    def find_usages(self, def_id: str) -> list[str]:
        xrefs = self._loader.get_cross_refs()
        usage = xrefs.get("def_ref_usage", {})
        return usage.get(def_id, [])

    def inline_refs(self, doc: dict) -> dict:
        refs = doc.get("def_refs", [])
        if not refs:
            return doc
        resolved = self.resolve_all(refs)
        result = dict(doc)
        result["resolved_def_refs"] = {
            k: v for k, v in resolved.items() if v is not None
        }
        return result

    def _ensure_index(self):
        if self._index is None:
            self._index = self._loader.get_definitions()
