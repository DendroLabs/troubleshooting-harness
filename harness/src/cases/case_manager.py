import re
from datetime import datetime, timezone
from pathlib import Path

from harness.methodology.phase_rules import PHASE_SEQUENCE, can_advance, next_phase


class CaseManager:

    def __init__(self, cases_dir: Path):
        self._dir = cases_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def create(self, symptom: str, os: str, version: str,
               platform: str | None = None) -> dict:
        case_id = self._next_case_id()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = {
            "case_id": case_id,
            "opened": now,
            "os": os,
            "version": version,
            "platform": platform or "",
            "current_phase": "triage",
            "phases_completed": [],
            "root_cause_confirmed": False,
            "closed": False,
        }
        body = (
            f"\n# Case {case_id}: {symptom}\n\n"
            f"## Triage [{now}]\n"
            f"**Symptom:** {symptom}\n"
            f"**OS:** {os}  **Version:** {version}"
        )
        if platform:
            body += f"  **Platform:** {platform}"
        body += "\n"
        self._write(case_id, state, body)
        return state

    def read(self, case_id: str) -> dict | None:
        path = self._dir / f"{case_id}.md"
        if not path.exists():
            return None
        text = path.read_text()
        state = self._parse_front_matter(text)
        state["body"] = self._strip_front_matter(text)
        return state

    def advance(self, case_id: str, from_phase: str,
                output: str) -> dict:
        state = self.read(case_id)
        if state is None:
            return {"error": f"Case {case_id} not found."}

        if state["current_phase"] != from_phase:
            return {
                "error": (
                    f"Phase mismatch. Case is in '{state['current_phase']}', "
                    f"not '{from_phase}'."
                ),
                "current_phase": state["current_phase"],
            }

        # Update state BEFORE gate check — gates reference phases_completed and root_cause_confirmed
        completed = state.get("phases_completed", [])
        if from_phase not in completed:
            completed.append(from_phase)
        state["phases_completed"] = completed

        if from_phase == "root-cause":
            state["root_cause_confirmed"] = True

        ok, reason = can_advance(from_phase, state)
        if not ok:
            return {"error": reason, "current_phase": state["current_phase"]}

        nxt = next_phase(from_phase)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state["current_phase"] = nxt
        body = state.pop("body", "")
        body += f"\n---\n\n## {_phase_title(nxt)} [{now}]\n{output}\n"
        self._write(case_id, state, body)
        return {
            "case_id": case_id,
            "previous_phase": from_phase,
            "current_phase": nxt,
            "next_phase": next_phase(nxt),
        }

    def close(self, case_id: str, resolution: str) -> dict:
        state = self.read(case_id)
        if state is None:
            return {"error": f"Case {case_id} not found."}

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        completed = state.get("phases_completed", [])
        if state["current_phase"] not in completed:
            completed.append(state["current_phase"])
        state["phases_completed"] = completed
        state["closed"] = True
        state["closed_at"] = now
        body = state.pop("body", "")
        body += f"\n---\n\n## Closed [{now}]\n{resolution}\n"
        self._write(case_id, state, body)
        return {"case_id": case_id, "closed": True, "closed_at": now}

    def list_cases(self) -> list[dict]:
        results = []
        for p in sorted(self._dir.glob("*.md")):
            if p.stem.isdigit():
                state = self.read(p.stem)
                if state:
                    state.pop("body", None)
                    results.append(state)
        return results

    def _next_case_id(self) -> str:
        existing = [
            int(p.stem) for p in self._dir.glob("*.md") if p.stem.isdigit()
        ]
        n = max(existing, default=0) + 1
        return f"{n:03d}"

    def _write(self, case_id: str, state: dict, body: str):
        path = self._dir / f"{case_id}.md"
        fm = "---\n"
        for k, v in state.items():
            if k == "body":
                continue
            if isinstance(v, list):
                fm += f"{k}:\n"
                for item in v:
                    fm += f"  - {item}\n"
            elif isinstance(v, bool):
                fm += f"{k}: {'true' if v else 'false'}\n"
            else:
                fm += f"{k}: {v}\n"
        fm += "---\n"
        path.write_text(fm + body)

    def _parse_front_matter(self, text: str) -> dict:
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not m:
            return {}
        state = {}
        lines = m.group(1).split("\n")
        current_key = None
        current_list = None
        for line in lines:
            list_match = re.match(r"^  - (.+)$", line)
            if list_match and current_key:
                current_list.append(list_match.group(1).strip())
                continue
            if current_key and current_list is not None:
                state[current_key] = current_list
                current_key = None
                current_list = None
            kv = re.match(r"^(\w[\w_]*): ?(.*)$", line)
            if kv:
                key, val = kv.group(1), kv.group(2).strip()
                if val == "":
                    current_key = key
                    current_list = []
                elif val == "true":
                    state[key] = True
                elif val == "false":
                    state[key] = False
                else:
                    state[key] = val
        if current_key and current_list is not None:
            state[current_key] = current_list
        return state

    def _strip_front_matter(self, text: str) -> str:
        m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
        return text[m.end():] if m else text


def _phase_title(phase: str) -> str:
    return phase.replace("-", " ").title()
