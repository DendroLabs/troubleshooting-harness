PHASE_SEQUENCE = [
    "triage",
    "platform-intel",
    "hypothesize",
    "test-hypothesis",
    "root-cause",
    "resolve",
    "verify-fix",
]

PHASE_GATES = {
    "resolve": lambda state: state.get("root_cause_confirmed", False),
    "verify-fix": lambda state: "resolve" in state.get("phases_completed", []),
}


def next_phase(current: str) -> str | None:
    try:
        idx = PHASE_SEQUENCE.index(current)
        return PHASE_SEQUENCE[idx + 1] if idx + 1 < len(PHASE_SEQUENCE) else None
    except ValueError:
        return None


def can_advance(current_phase: str, state: dict) -> tuple[bool, str | None]:
    nxt = next_phase(current_phase)
    if nxt is None:
        return False, f"No phase after '{current_phase}'."
    gate = PHASE_GATES.get(nxt)
    if gate and not gate(state):
        return False, f"Gate for '{nxt}' not satisfied."
    return True, None
