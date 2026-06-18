from harness.src.tools.base import ToolContext, wrap_result


class InterpretationRuleTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_interpretation_rule(self, rule_id: str, os: str) -> dict:
        doc = self._ctx.loader.get_interpretation_rule(rule_id)
        if doc is None:
            return wrap_result(
                "get_interpretation_rule",
                {"rule_id": rule_id, "os": os},
                None,
                kb_coverage="not_indexed",
            )

        if os != "*" and os not in doc.get("applicable_os", []):
            return wrap_result(
                "get_interpretation_rule",
                {"rule_id": rule_id, "os": os},
                None,
                kb_coverage="not_indexed",
            )

        data = {
            "rule_id": doc.get("rule_id"),
            "display_name": doc.get("display_name"),
            "category": doc.get("category"),
            "context": doc.get("context"),
            "observation": doc.get("observation"),
            "naive_interpretation": doc.get("naive_interpretation"),
            "correct_interpretation": doc.get("correct_interpretation"),
            "why": doc.get("why", []),
            "confirmation_commands": [
                c for c in doc.get("confirmation_commands", [])
                if c.get("os") in (os, "*")
            ],
            "traps": doc.get("traps", []),
            "related_rules": doc.get("related_rules", []),
            "related_protocols": doc.get("related_protocols", []),
        }
        return wrap_result(
            "get_interpretation_rule", {"rule_id": rule_id, "os": os}, data
        )

    def search_interpretation_rules(self, query: str, os: str, limit: int = 10) -> dict:
        all_rules = self._ctx.loader.list_all("interpretation-rules")
        q = query.lower()
        terms = q.split()
        matches = []
        for doc in all_rules:
            if os != "*" and os not in doc.get("applicable_os", []):
                continue
            searchable = " ".join([
                doc.get("display_name", ""),
                doc.get("context", ""),
                doc.get("observation", ""),
                doc.get("naive_interpretation", ""),
                doc.get("correct_interpretation", ""),
                doc.get("category", ""),
                " ".join(doc.get("keywords", [])),
                " ".join(doc.get("traps", [])),
                " ".join(doc.get("related_protocols", [])),
            ]).lower()
            score = sum(1 for term in terms if term in searchable)
            if score > 0:
                matches.append((score, {
                    "rule_id": doc.get("rule_id"),
                    "display_name": doc.get("display_name"),
                    "category": doc.get("category"),
                    "context": doc.get("context"),
                    "score": score,
                }))

        matches.sort(key=lambda x: x[0], reverse=True)
        results = [m[1] for m in matches[:limit]]
        kb = "indexed" if results else "not_indexed"
        return wrap_result(
            "search_interpretation_rules", {"query": query, "os": os},
            {"rules": results, "total": len(results)},
            kb_coverage=kb,
        )
