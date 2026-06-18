---
description: "Hardware topology and scalability limits for a platform"
---

# Hardware Map

## When to Use

The user asks about a platform's hardware specs, ASIC details, port layout, or scalability limits. Standalone — does not require an open case.

## Tools

1. `get_platform(platform_id)` — hardware details (ASIC, ports, bandwidth, chassis type)
2. `get_scalability(platform_family, os, version)` — scalability limits (route tables, TCAM, etc.)

## Rules

- Cite `kb_coverage` from every tool response. If `not_indexed`, state it explicitly.

## Workflow

1. Ask the user for the platform ID and (for scalability) OS and version.
2. Call `get_platform` with the platform ID. Present ASIC family, chassis type, port layout, and bandwidth.
3. Call `get_scalability` with the platform family (from get_platform), OS, and version. Present relevant scalability limits.
4. If the user's issue is capacity-related, flag any limits that may be relevant to their problem.
