import json
from pathlib import Path


class JsonLoader:

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache: dict[str, dict] = {}

    def get_protocol(self, protocol_id: str) -> dict | None:
        return self._find("protocols", protocol_id)

    def get_concept(self, concept_id: str) -> dict | None:
        return self._find("concepts", concept_id)

    def get_diagnostic(self, tree_id: str) -> dict | None:
        return self._find("diagnostics", tree_id)

    def get_procedure(self, procedure_id: str) -> dict | None:
        return self._find("procedures", procedure_id)

    def get_human_error(self, error_id: str) -> dict | None:
        return self._find("human-errors", error_id)

    def get_interpretation_rule(self, rule_id: str) -> dict | None:
        return self._find("interpretation-rules", rule_id)

    def get_platform(self, platform_id: str) -> dict | None:
        return self._find("platforms", platform_id)

    def get_best_practices(self, os: str) -> dict | None:
        d = self._data_dir / "best-practices"
        if not d.exists():
            return None
        for p in d.iterdir():
            if p.suffix == ".json" and not p.name.startswith("_"):
                doc = self._load(p)
                if doc and doc.get("os") == os:
                    return doc
        return None

    def list_protocols(self) -> list[dict]:
        idx = self._load(self._data_dir / "protocols" / "_index.json")
        return idx.get("protocols", []) if idx else []

    def list_all(self, subdir: str) -> list[dict]:
        d = self._data_dir / subdir
        if not d.exists():
            return []
        results = []
        for p in sorted(d.rglob("*.json")):
            if p.name.startswith("_"):
                continue
            doc = self._load(p)
            if doc:
                results.append(doc)
        return results

    def get_definitions(self) -> dict[str, dict]:
        flat: dict[str, dict] = {}
        d = self._data_dir / "definitions"
        if not d.exists():
            return flat
        for p in sorted(d.glob("*.json")):
            if p.name.startswith("_"):
                continue
            doc = self._load(p)
            if doc:
                for entry in doc.get("entries", []):
                    did = entry.get("def_id")
                    if did:
                        flat[did] = entry
        return flat

    def get_cross_refs(self) -> dict:
        return self._load(self._data_dir / "_cross-references.json") or {}

    def get_index(self) -> dict:
        return self._load(self._data_dir / "_index.json") or {}

    def get_protocol_index(self) -> list[dict]:
        return self.list_protocols()

    def _find(self, subdir: str, stem: str) -> dict | None:
        path = self._data_dir / subdir / f"{stem}.json"
        if path.exists():
            return self._load(path)
        d = self._data_dir / subdir
        if not d.exists():
            return None
        for p in d.rglob("*.json"):
            if p.stem == stem and not p.name.startswith("_"):
                return self._load(p)
        return None

    def _load(self, path: Path) -> dict | None:
        key = str(path)
        if key in self._cache:
            return self._cache[key]
        if not path.exists():
            return None
        try:
            doc = json.loads(path.read_text())
            self._cache[key] = doc
            return doc
        except (json.JSONDecodeError, OSError):
            return None
