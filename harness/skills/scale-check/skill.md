---
description: "Check scalability limits and compare platform capacity for planning"
---

# Scale Check

## When to Use

The user is planning capacity, checking whether a platform can handle a workload, or comparing scalability across platforms. Standalone — does not require an open case.

## Tools

1. `get_scalability(platform_family, os, version)` — scalability limits (route tables, TCAM, MAC, etc.)
2. `compare_platforms(platform_ids[])` — side-by-side hardware comparison
3. `get_platform(platform_id)` — platform details to determine family

## Rules

- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

1. Ask the user for: platform family (or platform ID to look up the family), OS, and version.
2. If the user provides a platform ID instead of a family, call `get_platform` first to determine the family.
3. Call `get_scalability` with the platform family, OS, and version.
4. Present the relevant scalability limits: route table sizes, TCAM entries, MAC addresses, VRFs, etc.
5. If the user wants to compare scalability across platforms, call `get_scalability` for each and present side-by-side.
6. If the user provides their expected workload numbers, compare against the limits and flag any that are near or over capacity.
