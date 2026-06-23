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

- Lead with what's already known. The FIRST thing you do is invite the user to share the data and context they already have — do not open with a list of targeted questions. Extract the structured fields from what they give you, then ask only for what's still missing.
- Call `open_case` first. Every troubleshooting session requires a case_id.
- Cite `kb_coverage` from every tool response. If `not_indexed`, tell the user: "This topic is not covered in the KB — recommendations beyond this point are not KB-backed."
- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- When symptoms match a caveat but the version doesn't match exactly, say "possible regression" — never "this IS your bug."

## Workflow

1. **Start with what's already known.** Open with a single, broad prompt that invites the user to dump everything they have before you ask anything specific — for example: *"Before I ask anything targeted, tell me what you already know and paste whatever you've already gathered."* Prompt for, but don't require, any of:
   - the symptom and when it started / what's affected
   - what changed recently (config, upgrade, hardware, traffic)
   - device OS, version, and platform/hardware
   - data already in hand — CLI output (`show version`, `show tech`, interface/protocol output), logs, topology, monitoring/alerts, prior ticket notes
2. **Extract the structured fields** (symptom, OS, version, platform) from what the user shared. Parse OS/version out of pasted output where possible (e.g. `show version`). Ask the user ONLY for the specific fields still missing — never re-ask for anything they already provided.
3. Call `open_case` with the gathered info. Record the returned `case_id` — all subsequent phases reference it. (If version is genuinely unknown, use `"*"` and note it.)
4. Call `check_kb_coverage` for the symptom topic. Report coverage status to the user.
5. Call `search_caveats` with keywords drawn from BOTH the symptom and the data the user already shared (error strings, counters, log messages). Present any matches with their `match_confidence`.
6. Call `search_human_errors` with the symptom descriptions and any recent-change details. Flag any matching operator mistake patterns.
7. **Identify the gaps.** From what's known plus the KB findings, state what additional data is actually needed to form a hypothesis — and ask for exactly that next. This is targeted data collection driven by the evidence, not a generic questionnaire.
8. Summarize findings: what we know, KB coverage status, candidate caveats, possible human errors, and the specific data still needed.
9. Call `advance_phase(case_id, "triage", <summary>)` to record findings and move to platform-intel.
