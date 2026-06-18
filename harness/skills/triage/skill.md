---
description: "Start troubleshooting: open a case, gather symptoms, check KB coverage, search for known bugs and common mistakes"
---

# Triage

## When to Use

The user reports a network problem, outage, or unexpected behavior. This is always the first skill invoked — it opens a case and establishes the initial scope.

## Tools

1. `open_case(symptom, os, version, platform?)` — creates a new case, returns case_id
2. `check_kb_coverage(topic, os)` — determines whether the KB covers this problem domain
3. `search_caveats(query, os, version?)` — checks for known bugs matching the symptoms
4. `search_human_errors(symptoms[], os)` — checks for common operator mistakes

## Rules

- Call `open_case` first. Every troubleshooting session requires a case_id.
- Cite `kb_coverage` from every tool response. If `not_indexed`, tell the user: "This topic is not covered in the KB — recommendations beyond this point are not KB-backed."
- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- When symptoms match a caveat but the version doesn't match exactly, say "possible regression" — never "this IS your bug."

## Workflow

1. Ask the user for: symptom description, device OS, version, and platform (if known).
2. Call `open_case` with the gathered info. Record the returned `case_id` — all subsequent phases reference it.
3. Call `check_kb_coverage` for the symptom topic. Report coverage status to the user.
4. Call `search_caveats` with symptom keywords. Present any matches with their `match_confidence`.
5. Call `search_human_errors` with symptom descriptions. Flag any matching operator mistake patterns.
6. Summarize findings: KB coverage status, candidate caveats, possible human errors.
7. Call `advance_phase(case_id, "triage", <summary>)` to record findings and move to platform-intel.
