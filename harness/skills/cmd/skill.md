---
description: "Validate or search for CLI commands by OS and version"
---

# Command Lookup

## When to Use

The user wants to validate a specific command, find the right syntax for an OS/version, or search for commands by keyword. Standalone — does not require an open case.

## Tools

1. `validate_command(command, os, version)` — validate a specific command string
2. `search_commands(query, os, version, limit?)` — full-text search over command database

## Rules

- Every command presented to the user MUST be validated first. No exceptions.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

### Validate a command
1. Call `validate_command` with the user's command, OS, and version.
2. Report the validation status: `exact`, `prefix`, `fts` (fuzzy match), or `not_found`.
3. If `prefix` or `fts`, present the matched syntax and suggestions.
4. If `not_found`, suggest the user try `search_commands` with keywords.

### Search for commands
1. Call `search_commands` with the user's keywords, OS, and version.
2. Present matching commands with their syntax and description.
3. If too many results, suggest narrowing the search terms or reducing the limit.
