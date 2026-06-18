# TSH — Network Troubleshooting Harness

## Session Start

If no specific task is given, read `continue.txt` for context on where the project left off and what to do next.

## What This Is

A vendor-agnostic network troubleshooting datastore and deterministic LLM harness. Two layers:

- **`data/`** — Structured JSON + SQLite. Pure data, zero LLM dependency. Consumed by the harness, Canopy, Watchtower, or any other program.
- **`harness/`** — Forces any LLM to use the datastore deterministically. MCP server, CLI, REST API interfaces. Skills enforce a 7-phase troubleshooting methodology.

## Data Rules

### Every Operational Data Point Is Scoped

Every command, timer default, failure resolution, verify_command, and diagnostic step carries:
- `os` (required) — nxos, iosxe, iosxr, sonic, junos, eos, or `*` for universal
- `version_range` (required) — `{"min": "9.3", "max": "*"}` or use `versions` array for non-contiguous
- `platforms` (optional) — array of platform families, null = all
- `asic_family` (optional) — ASIC family name, null = platform-agnostic

**Never leave os or version_range unspecified on operational data. If truly universal, use `"*"`.**

### Schema Discipline

- All JSON data files must validate against their schema in `data/_schema/`
- `schema_version: "1.0.0"` on every file — the harness rejects mismatched versions
- Run `python tools/validate/validate_all.py` before committing

### def_id System

Shared atoms (daemons, databases, timers, services, ASIC families) use globally unique IDs:
- `daemon:orchagent`, `daemon:bgpd`
- `db:appl_db`, `db:config_db`
- `timer:bgp-holdtime`
- `service:bgp`
- `asic:cloud-scale-fx3`

Domain files reference atoms via `def_refs: ["daemon:bgpd", "db:config_db"]`. The resolver inlines the full atom content at query time.

### No Raw Device Data

The datastore contains curated knowledge, not collected evidence. No real device hostnames, IP addresses, serial numbers, or CLI output captures from production or lab devices.

### Sources Required

Every data file must have a `sources` array with at least one entry. Use `verifying_quote` to prove the data was sourced, not hallucinated. Confidence starts at `medium` for imported data; promote to `high` after verification against source material.

## Harness Rules

### Command Validation Is Mandatory

Before suggesting ANY command to a user, the harness must call `validate_command(os, version, command)`. Unvalidated commands never reach the user.

### KB Citation Is Structural

Every tool response includes `kb_coverage: "indexed" | "not_indexed"`. Skills require citing which tool produced each claim. If the KB doesn't cover a topic, say so explicitly — do not fall back to training data without flagging it.

### Bug-Matching Rule

When symptoms match a known caveat but the version doesn't match exactly: flag as "possible regression." Never say "this IS your bug."

### Phase Sequencing

The 7-phase methodology runs in order: triage → platform-intel → hypothesize → test-hypothesis → root-cause → resolve → verify-fix. Each phase writes state to `harness/cases/<number>.md`. Can't skip phases — resolve requires a confirmed root cause.

## Build Commands

```bash
# Validate all JSON against schemas
python tools/validate/validate_all.py

# Rebuild indexes and cross-references
python tools/index/build_index.py
python tools/index/build_cross_refs.py

# Initialize SQLite databases (safe to re-run)
python tools/migrate/init_databases.py

# Populate SQLite from JSON + archived-kb sources
cd tools/migrate && python3 build_sqlite.py

# Export vendor-specific subset
python tools/export/subset.py --os sonic --output ./sonic-only/

# Start MCP server (stdio transport)
python harness/interfaces/mcp/server.py

# CLI queries
python3 harness/interfaces/cli/tsh_cli.py query protocol bgp-4 --os nxos --version 10.4
python3 harness/interfaces/cli/tsh_cli.py validate "show bgp summary" --os nxos --version "*"
python3 harness/interfaces/cli/tsh_cli.py search caveats bgp --os nxos --format compact
python3 harness/interfaces/cli/tsh_cli.py search interpretation-rules "CRC counters" --os nxos --format compact
python3 harness/interfaces/cli/tsh_cli.py query interpretation-rule interface-crc-counters-without-clearing --os nxos --format compact
python3 harness/interfaces/cli/tsh_cli.py case open "BGP flapping" --os nxos --version 10.4

# Quick tool test (from repo root)
python3 -c "
import sys; sys.path.insert(0, '.')
from harness.src.tools.base import build_context
from harness.interfaces.mcp.tool_dispatch import build_dispatch
from pathlib import Path
ctx = build_context(Path('.'))
d = build_dispatch(ctx)
print(d['validate_command'](command='show bgp summary', os='nxos', version='*'))
"
```

## Harness Architecture

```
harness/
  src/
    retrieval/          scope_filter, json_loader, sqlite_query, resolver
    validation/         command_validator (3-step: exact -> prefix -> FTS)
    tools/              base (ToolContext) + 10 tool modules
    cases/              case_manager (file-backed state with YAML front matter)
  methodology/          phase_rules (7-phase sequence + gates)
  interfaces/
    mcp/                server.py (stdio), tool_registry (18 tools), tool_dispatch
    cli/                tsh_cli.py (20 ops, 5 subcommands), formatters.py (full/compact/minimal)
    api/                NOT YET IMPLEMENTED (deferred post-v1)
  skills/               15 skill.md files (7 methodology + 8 utility)
  cases/                Case .md files created at runtime
```

Key patterns:
- `ToolContext` built once at startup, shared by all tools
- Every tool response wraps as: `{kb_coverage, source_tool, scope, data}`
- `Scope(os, version, platform_family, asic_family)` filters all operational data
- Tools are sync Python; MCP server is async (stdio serial, no concurrency needed)
- Case front matter parsed with regex (no pyyaml dependency)

## Directory Layout

```
data/                   Datastore (JSON + SQLite)
  _schema/              JSON Schema definitions
  definitions/          Shared atoms (def_id system)
  protocols/            One file per protocol
  platforms/            Hardware topology + scalability
  procedures/           Operational runbooks
  diagnostics/          Decision trees
  human-errors/         Common operator mistakes
  interpretation-rules/ Experience-based troubleshooting guidance
  best-practices/       Per OS/version
  db/                   SQLite databases (commands, caveats, field-notices, platforms)

harness/                Methodology enforcer
  src/                  Core retrieval + validation + tools
  interfaces/           MCP, CLI, REST API
  skills/               Claude Code skill definitions (7-phase + utilities)
  methodology/          Coordination rules, grounding rules
  cases/                File-backed case state

tools/                  Build/maintenance tooling
  import/               Import from archived-kb sources
  validate/             Schema validation
  index/                Rebuild indexes
  migrate/              SQLite population
  export/               Vendor-specific subset generation

archived-kb/            Symlinks to original KBs (read-only reference)
```

## Adding Data

### New OS Version
1. Add commands to `data/db/commands.db`
2. Add caveats to `data/db/caveats.db`
3. Add `os_defaults` entries to relevant protocol timers
4. Add scalability file to `data/platforms/scalability/<os>/`
5. Run `validate_all.py`

### New Vendor
1. Add definition atoms (daemons, databases) in `data/definitions/`
2. Add `os_defaults` entries to protocol timers
3. Add `verify_commands` with the new OS to failure modes
4. Add diagnostic tree commands/branches
5. Populate `commands.db` with command catalog
6. Add platform + scalability data
7. Run `validate_all.py`
