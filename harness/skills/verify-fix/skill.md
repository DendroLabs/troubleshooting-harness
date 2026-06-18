---
description: "Verify the fix worked: re-run diagnostic commands, confirm symptoms resolved, close case"
---

# Verify Fix

## When to Use

After resolve, when the fix has been applied and needs verification. This phase is gated — it requires the resolve phase to be completed.

## Tools

1. `validate_command(command, os, version)` — MANDATORY before suggesting any command
2. `get_protocol(protocol_id, os, version)` — verify_commands from the failure mode
3. `get_diagnostic_tree(tree_id, os, version)` — re-run diagnostic checks
4. `get_case(case_id)` — review the full case history

## Rules

- **Gate**: This phase cannot be entered without resolve phase completed.
- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- Verification must confirm the original symptom is resolved, not just that the config was applied.

## Workflow

1. Retrieve the case with `get_case(case_id)`. Review the original symptom and the resolution applied.
2. Call `get_protocol` for the relevant protocol. Retrieve `verify_commands` from the failure mode.
3. Present verification commands to the user (all pre-validated). These should confirm:
   - The original symptom is no longer present
   - The fix is operating as expected (e.g., BGP session established, routes installed)
   - No new issues were introduced
4. If the diagnostic tree was used during test-hypothesis, re-run key nodes to confirm the tree now follows the healthy path.
5. Ask the user to confirm the issue is resolved.
6. Call `advance_phase(case_id, "verify-fix", <verification results>)` to complete the methodology.
7. The case is now complete. Summarize the full case: symptom, root cause, resolution, verification.
