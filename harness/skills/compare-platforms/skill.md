---
description: "Side-by-side comparison of two or more hardware platforms"
---

# Compare Platforms

## When to Use

The user wants to compare hardware platforms — ASIC, port density, bandwidth, chassis type. Standalone — does not require an open case.

## Tools

1. `compare_platforms(platform_ids[])` — side-by-side comparison
2. `get_platform(platform_id)` — detailed info for a single platform (if deeper detail needed)

## Rules

- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

1. Ask the user for two or more platform IDs to compare.
2. Call `compare_platforms` with the platform ID list.
3. Present the comparison in a table format: ASIC family, chassis type, port counts, bandwidth, and any notable differences.
4. If the user wants more detail on a specific platform, call `get_platform` for that platform.
