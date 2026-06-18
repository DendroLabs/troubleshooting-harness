---
description: "Retrieve and walk through an operational procedure with validated commands"
---

# Procedure

## When to Use

The user needs to follow a runbook — software upgrade, password recovery, config reload, container restart, etc. Standalone — does not require an open case.

## Tools

1. `get_procedure(procedure_id, os, version)` — step-by-step procedure with pre-validated commands
2. `validate_command(command, os, version)` — validate any additional commands beyond the procedure

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Commands within the procedure response are pre-validated; additional commands must be validated explicitly.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- Present steps in order. Do not skip or reorder steps.

## Workflow

1. Identify the procedure and the target OS/version.
2. Call `get_procedure` with the procedure ID, OS, and version.
3. Present the procedure step by step. Each step includes:
   - Description of what the step does
   - The command to run (pre-validated)
   - Expected output or success criteria
4. Wait for the user to complete each step before presenting the next.
5. If a step fails, help diagnose before continuing — do not skip ahead.
