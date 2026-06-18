---
description: "Gather hardware context: platform details, scalability limits, platform-specific caveats"
---

# Platform Intel

## When to Use

After triage, when the case needs hardware context. Also usable standalone when the user asks about a specific platform's capabilities or limits.

## Tools

1. `get_platform(platform_id)` — hardware details (ASIC, ports, bandwidth, chassis type)
2. `get_scalability(platform_family, os, version)` — scalability limits (route tables, TCAM, etc.)
3. `search_caveats(query, os, version?)` — platform-specific bug search

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

1. Retrieve the case with `get_case(case_id)` to confirm we're in the platform-intel phase.
2. Call `get_platform` with the device's platform ID. Present ASIC family, chassis type, and port layout.
3. Call `get_scalability` with the platform family, OS, and version. Report relevant limits (route table sizes, TCAM capacity, MAC table size).
4. Call `search_caveats` with the platform name as query to find platform-specific bugs.
5. Assess whether the reported symptom could be a scalability/capacity issue based on the limits.
6. Call `advance_phase(case_id, "platform-intel", <summary>)` to record findings and move to hypothesize.
