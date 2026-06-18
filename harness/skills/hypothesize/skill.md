---
description: "Form ranked hypotheses from protocol failure modes, caveats, and platform context"
---

# Hypothesize

## When to Use

After platform-intel, when the case has enough context to form hypotheses. The protocol's known failure modes drive the hypothesis list.

## Tools

1. `get_protocol(protocol_id, os, version)` — failure modes, timers, dependencies, verify commands
2. `search_caveats(query, os, version?)` — narrow caveat search per hypothesis
3. `get_case(case_id)` — review triage and platform-intel findings

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- Hypotheses must be ranked by likelihood. Each hypothesis must reference a specific failure mode or caveat.

## Workflow

1. Retrieve the case with `get_case(case_id)`. Review triage symptoms and platform-intel findings.
2. Call `get_protocol` for the relevant protocol. Review all failure modes.
3. Match reported symptoms against failure mode symptoms. Rank hypotheses by fit.
4. For each top hypothesis, call `search_caveats` with targeted keywords to check for known bugs.
5. Present a ranked hypothesis list to the user. Each entry should include:
   - The failure mode scenario it maps to
   - Why it fits the reported symptoms
   - Any matching caveats (with match_confidence)
6. Call `advance_phase(case_id, "hypothesize", <ranked hypothesis list>)` to move to test-hypothesis.
