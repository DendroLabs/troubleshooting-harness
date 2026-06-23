# TSH — Network Troubleshooting Harness

A **vendor-agnostic network troubleshooting datastore** plus a **deterministic LLM
harness** that forces any model to ground its answers in that data instead of
guessing from training memory.

TSH ships as an [MCP](https://modelcontextprotocol.io) server, so you can drop it
straight into [Claude Code](https://claude.com/claude-code) or
[OpenCode](https://opencode.ai) and start troubleshooting with validated, cited
commands across NX-OS, IOS-XE, IOS-XR, SONiC, Junos, and EOS.

## Quick start

From a clone (installs and updates in place):

```bash
git clone https://github.com/DendroLabs/troubleshooting-harness.git
cd troubleshooting-harness
./install.sh
```

Or as a one-liner (clones into `~/.local/share/tsh-harness`):

```bash
curl -fsSL https://raw.githubusercontent.com/DendroLabs/troubleshooting-harness/main/install.sh | bash
```

Then **restart Claude Code / OpenCode** and ask it to use the `tsh-harness` tools.

The installer creates an isolated Python virtualenv, builds the local SQLite
databases, registers the MCP server with whichever editors you have installed
(Claude Code and OpenCode), and verifies the harness loads. **Re-run `./install.sh`
any time** to pull GitHub updates and refresh the install — it only rebuilds when
something actually changed.

See [INSTALL.md](INSTALL.md) for prerequisites, environment overrides
(`TSH_DIR`, `PYTHON`, `TSH_SKIP_REGISTER`, …), and uninstall steps.

## What you get

- **44 protocols** — BGP, OSPF, IS-IS, EVPN/VXLAN, segment routing, MPLS, PIM,
  HSRP/VRRP, NAT, and more, each with states, timers, and scoped failure modes.
- **65 interpretation rules** — experience-based guidance for reading *ambiguous
  or misleading* device output (e.g. "an adjacency log is point-in-time, not
  current state"; "received ≠ installed routes").
- **Curated caveats, platforms, diagnostics, procedures, and human-error data** —
  198 JSON files, all schema-validated, plus SQLite catalogs for fast command and
  caveat search.
- **18 MCP tools** + a CLI, exposing the whole datastore to any LLM.

## Two layers

| Layer | Path | What it is |
| --- | --- | --- |
| **Datastore** | `data/` | Structured JSON + SQLite. Pure data, **zero LLM dependency** — consumable by the harness or any other program. |
| **Harness** | `harness/` | Forces an LLM to use the datastore deterministically via MCP/CLI interfaces and a 7-phase troubleshooting methodology. |

Every operational data point is **scoped** by OS, version range, platform family,
and ASIC family, so a command suggested for NX-OS 9.3 is never offered on a release
or platform where it doesn't exist.

## Guarantees the harness enforces

- **Command validation is mandatory** — every suggested command is checked against
  the catalog (`validate_command`) before it can reach you.
- **KB citation is structural** — each tool response reports
  `kb_coverage: indexed | not_indexed`; if the KB doesn't cover a topic, the
  harness says so instead of silently falling back to training data.
- **No raw device data** — the datastore is curated knowledge, not collected
  evidence: no real hostnames, IPs, serials, or production CLI captures.

## Using it without an editor

```bash
# Validate a command for a specific OS/version
python3 harness/interfaces/cli/tsh_cli.py validate "show bgp summary" --os nxos --version "*"

# Query a protocol or search interpretation rules
python3 harness/interfaces/cli/tsh_cli.py query protocol bgp-4 --os nxos --version 10.4
python3 harness/interfaces/cli/tsh_cli.py search interpretation-rules "CRC counters" --os nxos --format compact
```

See [CLAUDE.md](CLAUDE.md) for the full build, data, and architecture reference.

## Requirements

- `git`
- Python **3.10+** (with the `venv` module)

The installer handles the rest (dependencies are isolated in a per-install
virtualenv — nothing touches your global Python).

## License

Released under the [MIT License](LICENSE).
