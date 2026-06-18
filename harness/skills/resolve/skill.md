---
description: "Apply the fix: retrieve procedures, validate all commands, check best practices"
---

# Resolve

## When to Use

After root-cause, when a confirmed root cause needs a fix applied. This phase is gated — it requires `root_cause_confirmed` from the root-cause phase.

## Tools

1. `get_procedure(procedure_id, os, version)` — operational procedure with validated commands
2. `validate_command(command, os, version)` — MANDATORY before suggesting any command
3. `get_best_practices(os)` — best practices index for the OS
4. `get_protocol(protocol_id, os, version)` — resolution steps from the failure mode
5. `get_case(case_id)` — review root cause determination

## Rules

- **Gate**: This phase cannot be entered without `root_cause_confirmed`. If the gate fails, return to root-cause.
- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- Present resolution steps in order. Do not skip steps.

## Workflow

1. Retrieve the case with `get_case(case_id)`. Confirm root_cause_confirmed is set.
2. Call `get_protocol` for the relevant protocol. Locate the resolution steps for the confirmed failure mode.
3. If a procedure exists for the fix, call `get_procedure` with the procedure ID. All commands are pre-validated.
4. Call `get_best_practices` for the OS. Cross-reference the fix against best practices.
5. Present the resolution plan to the user:
   - Step-by-step commands (all validated)
   - Any best practice considerations
   - Expected impact and rollback plan if applicable
6. Guide the user through each step, waiting for confirmation before proceeding.
7. Call `advance_phase(case_id, "resolve", <resolution summary>)` to move to verify-fix.
