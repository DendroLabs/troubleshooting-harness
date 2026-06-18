---
description: "Test hypotheses using diagnostic decision trees and validated commands"
---

# Test Hypothesis

## When to Use

After hypothesize, when ranked hypotheses need to be confirmed or eliminated through diagnostic commands.

## Tools

1. `get_diagnostic_tree(tree_id, os, version)` — diagnostic decision tree with scope-filtered commands
2. `validate_command(command, os, version)` — MANDATORY before suggesting any command
3. `search_commands(query, os, version)` — find additional diagnostic commands
4. `get_case(case_id)` — review hypotheses from prior phase

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)`. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.
- Walk the diagnostic tree in order. Do not skip nodes.
- Present one command at a time. Wait for the user to provide output before proceeding.

## Workflow

1. Retrieve the case with `get_case(case_id)`. Review the ranked hypotheses.
2. For the top hypothesis, find the matching diagnostic tree via `diagnostic_tree_ref` from the failure mode.
3. Call `get_diagnostic_tree` with the tree ID. All commands in the tree are pre-validated.
4. Walk the user through the tree node by node:
   - Present the current node's question/check
   - Provide the validated command to run
   - Based on the user's output, follow the appropriate branch (yes/no/condition)
5. If additional commands are needed beyond the tree, call `search_commands` then `validate_command` before presenting.
6. Record which hypotheses were confirmed or eliminated based on the diagnostic results.
7. Call `advance_phase(case_id, "test-hypothesis", <results per hypothesis>)` to move to root-cause.
