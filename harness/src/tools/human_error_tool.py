from harness.src.tools.base import ToolContext, wrap_result


class HumanErrorTool:

    def __init__(self, ctx: ToolContext):
        self._ctx = ctx

    def get_human_error(self, error_id: str, os: str) -> dict:
        doc = self._ctx.loader.get_human_error(error_id)
        if doc is None:
            return wrap_result(
                "get_human_error",
                {"error_id": error_id, "os": os},
                None,
                kb_coverage="not_indexed",
            )

        if os != "*" and os not in doc.get("applicable_os", []):
            return wrap_result(
                "get_human_error",
                {"error_id": error_id, "os": os},
                None,
                kb_coverage="not_indexed",
            )

        data = {
            "error_id": doc.get("error_id"),
            "display_name": doc.get("display_name"),
            "severity": doc.get("severity"),
            "category": doc.get("category"),
            "pattern": doc.get("pattern"),
            "what_goes_wrong": doc.get("what_goes_wrong"),
            "symptoms": doc.get("symptoms", []),
            "correct_procedure": doc.get("correct_procedure"),
            "why_it_breaks": doc.get("why_it_breaks", []),
            "prevention": doc.get("prevention"),
            "detection_commands": [
                c for c in doc.get("detection_commands", [])
                if c.get("os") in (os, "*")
            ],
        }
        return wrap_result(
            "get_human_error", {"error_id": error_id, "os": os}, data
        )

    def search_human_errors(self, symptoms: list[str], os: str) -> dict:
        all_errors = self._ctx.loader.list_all("human-errors")
        query = " ".join(symptoms).lower()
        matches = []
        for doc in all_errors:
            if os != "*" and os not in doc.get("applicable_os", []):
                continue
            doc_symptoms = " ".join(doc.get("symptoms", [])).lower()
            doc_keywords = " ".join(doc.get("keywords", [])).lower()
            doc_text = doc_symptoms + " " + doc_keywords
            score = sum(1 for term in query.split() if term in doc_text)
            if score > 0:
                matches.append((score, {
                    "error_id": doc.get("error_id"),
                    "display_name": doc.get("display_name"),
                    "severity": doc.get("severity"),
                    "pattern": doc.get("pattern"),
                    "score": score,
                }))

        matches.sort(key=lambda x: x[0], reverse=True)
        results = [m[1] for m in matches[:10]]
        kb = "indexed" if results else "not_indexed"
        return wrap_result(
            "search_human_errors", {"os": os}, {"errors": results}, kb_coverage=kb
        )
