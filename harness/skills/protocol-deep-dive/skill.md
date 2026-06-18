---
description: "Deep dive into a protocol: failure modes, timers, dependencies, and resolved definitions"
---

# Protocol Deep Dive

## When to Use

The user wants a comprehensive understanding of a protocol's failure modes, timer defaults, dependencies, and internal components. More thorough than what the triage/hypothesize phases provide.

## Tools

1. `get_protocol(protocol_id, os, version, include_def_refs=true)` — full protocol data with resolved definitions
2. `validate_command(command, os, version)` — validate any commands before presenting
3. `check_kb_coverage(topic, os)` — check if sub-topics are covered

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

1. Call `get_protocol` with `include_def_refs=true` to get the full protocol data with resolved atoms (daemons, databases, services).
2. Present a structured overview:
   - **Failure Modes**: Each scenario with symptoms, root causes, and resolution pointers
   - **Timers**: Name, purpose, default values per OS, and what happens on expiry
   - **Dependencies**: What this protocol depends on and what depends on it
   - **Internal Components**: Resolved def_refs (daemons, databases, services) with their roles
3. If the user asks about a specific failure mode, drill into its diagnostic tree ref and resolution steps.
4. For cross-OS comparisons within the deep dive, call `get_protocol` for each OS as needed.
