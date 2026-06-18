---
description: "Compare protocol behavior across different operating systems"
---

# Cross-OS Comparison

## When to Use

The user asks how a protocol behaves differently across NX-OS, IOS-XE, IOS-XR, SONiC, or other supported OSes. Useful for multi-vendor environments or migrations.

## Tools

1. `get_protocol(protocol_id, os, version)` — called once per OS to compare
2. `validate_command(command, os, version)` — validate commands for each OS

## Rules

- Before suggesting ANY command, call `validate_command(command, os, version)` for the specific OS. Never present an unvalidated command.
- Cite `kb_coverage` from every tool response. If `not_indexed` for an OS, state it explicitly.

## Workflow

1. Identify the protocol and the OS variants to compare.
2. Call `get_protocol` once per OS (e.g., `os=nxos`, `os=iosxe`, `os=iosxr`).
3. Compare across the responses:
   - Timer defaults (hold time, keepalive, MRAI) — note any OS-specific differences
   - Failure modes present on one OS but not another
   - Verify commands — different syntax per OS
   - Vendor-specific notes
4. Present a summary highlighting the meaningful differences, not an exhaustive dump.
5. If the user needs commands for a specific OS, validate each one with `validate_command`.
