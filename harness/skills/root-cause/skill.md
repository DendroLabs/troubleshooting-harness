---
description: "Confirm root cause by correlating test results against caveats, failure modes, and human errors"
---

# Root Cause

## When to Use

After test-hypothesis, when diagnostic results are available and a root cause needs to be confirmed.

## Tools

1. `search_caveats(query, os, version?)` — correlate confirmed hypothesis against known bugs
2. `search_human_errors(symptoms[], os)` — check if root cause is a common operator mistake
3. `get_protocol(protocol_id, os, version)` — review failure mode resolutions
4. `get_case(case_id)` — review all prior phase findings

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- When symptoms match a caveat but version doesn't match exactly, say "possible regression" — never "this IS your bug."
- A root cause must be backed by diagnostic evidence from the test-hypothesis phase. Do not guess.

## Workflow

1. Retrieve the case with `get_case(case_id)`. Review test-hypothesis results.
2. For the confirmed hypothesis, call `search_caveats` with specific keywords to verify against known bugs.
3. Call `search_human_errors` to check if the root cause is operator error.
4. Call `get_protocol` to pull the specific failure mode's resolution steps.
5. Present the root cause determination to the user:
   - What was confirmed and what evidence supports it
   - Whether it matches a known caveat (with match_confidence and version caveat)
   - Whether it's a human error pattern
6. If the root cause is confirmed, call `advance_phase(case_id, "root-cause", <root cause statement>)`. This sets `root_cause_confirmed`, which is required to enter the resolve phase.
