---
description: "Search known bugs and caveats by keyword, OS, version, or severity"
---

# Bug Search

## When to Use

The user asks about known bugs, caveats, or CSC IDs. Standalone — does not require an open case.

## Tools

1. `search_caveats(query, os, version?, severity?, limit?)` — full-text search over caveat database
2. `validate_command(command, os, version)` — if any diagnostic commands are suggested

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- When symptoms match a caveat but the version doesn't match exactly, say "possible regression" — never "this IS your bug."
- Always report `match_confidence` for each result.

## Workflow

1. Ask the user for: search keywords, target OS, and optionally version and severity filter.
2. Call `search_caveats` with the provided parameters.
3. Present results with: CSC ID, headline, severity, affected versions, and `match_confidence`.
4. If the user provides a device version, highlight version match vs. mismatch for each caveat.
5. For caveats with a version mismatch, explicitly flag as "possible regression — version not in affected range."
