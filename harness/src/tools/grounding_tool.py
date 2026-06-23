import re

from harness.src.tools.base import ToolContext, wrap_result

# Short/common words that would over-match if treated as topic keywords.
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "not", "was", "are", "has",
    "show", "from", "into", "out", "off", "all", "any", "its", "your",
}


def _topic_tokens(query: str) -> list[str]:
    """Significant keywords from a topic phrase (len >= 3, minus stopwords)."""
    return [
        t for t in re.split(r"[^a-z0-9]+", query)
        if len(t) >= 3 and t not in _STOPWORDS
    ]


def _topic_hit(query: str, tokens: list[str], *fields: str) -> bool:
    """Match the whole phrase OR any significant token against the fields."""
    text = " ".join(f for f in fields if f).lower()
    if query and query in text:
        return True
    return any(t in text for t in tokens)


class GroundingTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def check_kb_coverage(self, topic: str, os: str) -> dict:
        matches = []
        query = topic.lower().strip()
        tokens = _topic_tokens(query)

        for p in self._ctx.loader.list_protocols():
            name = (p.get("protocol_name", "") + " " + p.get("protocol_id", "")).lower()
            tags = " ".join(p.get("tags", [])).lower()
            if _topic_hit(query, tokens, name, tags):
                os_coverage = p.get("os_coverage", [])
                if os == "*" or os in os_coverage:
                    matches.append({
                        "type": "protocol",
                        "id": p.get("protocol_id"),
                        "name": p.get("protocol_name"),
                        "os_coverage": os_coverage,
                    })

        for doc in self._ctx.loader.list_all("diagnostics"):
            name = (doc.get("display_name", "") + " " + doc.get("tree_id", "")).lower()
            symptom = doc.get("entry_symptom", "").lower()
            if _topic_hit(query, tokens, name, symptom):
                applicable = doc.get("applicable_os", [])
                if os == "*" or os in applicable:
                    matches.append({
                        "type": "diagnostic",
                        "id": doc.get("tree_id"),
                        "name": doc.get("display_name"),
                    })

        for doc in self._ctx.loader.list_all("procedures"):
            name = (doc.get("procedure_name", "") + " " + doc.get("procedure_id", "")).lower()
            if _topic_hit(query, tokens, name):
                applicable = doc.get("applicable_os", [])
                if os == "*" or os in applicable:
                    matches.append({
                        "type": "procedure",
                        "id": doc.get("procedure_id"),
                        "name": doc.get("procedure_name"),
                    })

        for doc in self._ctx.loader.list_all("human-errors"):
            name = (doc.get("display_name", "") + " " + doc.get("error_id", "")).lower()
            if _topic_hit(query, tokens, name):
                applicable = doc.get("applicable_os", [])
                if os == "*" or os in applicable:
                    matches.append({
                        "type": "human-error",
                        "id": doc.get("error_id"),
                        "name": doc.get("display_name"),
                    })

        for doc in self._ctx.loader.list_all("interpretation-rules"):
            searchable = (
                doc.get("display_name", "") + " " +
                doc.get("rule_id", "") + " " +
                " ".join(doc.get("keywords", []))
            ).lower()
            if _topic_hit(query, tokens, searchable):
                applicable = doc.get("applicable_os", [])
                if os == "*" or os in applicable:
                    matches.append({
                        "type": "interpretation-rule",
                        "id": doc.get("rule_id"),
                        "name": doc.get("display_name"),
                    })

        covered = len(matches) > 0
        return wrap_result(
            "check_kb_coverage",
            {"topic": topic, "os": os},
            {"covered": covered, "matches": matches},
            kb_coverage="indexed" if covered else "not_indexed",
        )

    def get_best_practices(self, os: str) -> dict:
        doc = self._ctx.loader.get_best_practices(os)
        if doc is None:
            return wrap_result(
                "get_best_practices",
                {"os": os},
                None,
                kb_coverage="not_indexed",
            )
        return wrap_result("get_best_practices", {"os": os}, doc)

    def get_related(self, protocol_id: str) -> dict:
        xrefs = self._ctx.loader.get_cross_refs()
        related = xrefs.get("related_protocols", {}).get(protocol_id, [])
        return wrap_result(
            "get_related",
            {"protocol_id": protocol_id},
            {"related": related},
            kb_coverage="indexed" if related else "not_indexed",
        )
