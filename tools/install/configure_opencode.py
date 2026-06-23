#!/usr/bin/env python3
"""Register (or update) the TSH MCP server in an OpenCode config file.

Idempotent: reads the existing config, sets a single `mcp.<name>` entry, and
writes it back preserving every other key. Safe to run repeatedly.

Usage:
    python3 configure_opencode.py <config_path> <server_name> <command> [args...]

Exit codes:
    0  registered or already current
    2  config file exists but could not be parsed (left untouched)
"""

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("usage: configure_opencode.py <config_path> <name> <command> [args...]",
              file=sys.stderr)
        return 1

    config_path = Path(argv[1]).expanduser()
    name = argv[2]
    command = argv[3:]  # command + its args, as OpenCode expects a single array

    if config_path.exists() and config_path.read_text().strip():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError as exc:
            # Don't clobber a config we can't understand (e.g. JSONC with comments).
            print(f"could not parse {config_path}: {exc}", file=sys.stderr)
            print("Add this entry under \"mcp\" manually:", file=sys.stderr)
            print(json.dumps({name: _entry(command)}, indent=2), file=sys.stderr)
            return 2
        if not isinstance(config, dict):
            print(f"{config_path} is not a JSON object; leaving untouched",
                  file=sys.stderr)
            return 2
    else:
        config = {}

    config.setdefault("$schema", "https://opencode.ai/config.json")
    mcp = config.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        print(f"{config_path} has a non-object \"mcp\" key; leaving untouched",
              file=sys.stderr)
        return 2

    new_entry = _entry(command)
    if mcp.get(name) == new_entry:
        print(f"unchanged: {name} already current in {config_path}")
        return 0

    mcp[name] = new_entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"registered: {name} -> {config_path}")
    return 0


def _entry(command: list[str]) -> dict:
    return {"type": "local", "command": command, "enabled": True}


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
