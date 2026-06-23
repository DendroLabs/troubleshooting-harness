# Installing the TSH harness

`install.sh` adds the TSH network-troubleshooting harness as an **MCP server** for
[Claude Code](https://claude.com/claude-code) and [OpenCode](https://opencode.ai).
Run it once to install; run it again any time to pull GitHub updates.

## Quick start

From a clone (installs/updates in place):

```bash
git clone https://github.com/DendroLabs/troubleshooting-harness.git
cd troubleshooting-harness
./install.sh
```

Or one-line (clones into `~/.local/share/tsh-harness`):

```bash
curl -fsSL https://raw.githubusercontent.com/DendroLabs/troubleshooting-harness/main/install.sh | bash
```

Then **restart Claude Code / OpenCode** and ask it to use the `tsh-harness` tools.

## What it does

1. **Preflight** — checks for `git` and Python 3.10+ (with `venv`).
2. **Clone or update** — clones the repo, or `git pull`s an existing install and
   notes whether anything changed.
3. **Isolated deps** — creates a virtualenv at `<install>/.venv` and installs
   `mcp`, `jsonschema`, `referencing` (from `requirements.txt`). Nothing is
   installed into your global Python.
4. **Builds the SQLite databases** (`commands`, `caveats`, `platforms`) from the
   committed JSON data. Only rebuilds on first install or after an update.
5. **Registers the MCP server** at **user scope** (available in every project):
   - Claude Code via `claude mcp add-json tsh-harness … -s user`
   - OpenCode by merging an `mcp.tsh-harness` entry into
     `~/.config/opencode/opencode.json` (existing keys preserved)
6. **Verifies** the harness loads, then prints a summary.

Re-running is safe and idempotent — it updates the registration in place and only
rebuilds the databases when the repo actually changed.

## Options

| Variable | Default | Purpose |
| --- | --- | --- |
| `TSH_DIR` | `~/.local/share/tsh-harness` | Install location (clone mode only). |
| `TSH_REPO` | DendroLabs repo URL | Git URL to clone. |
| `PYTHON` | `python3` | Interpreter used to build the venv. |
| `OPENCODE_CONFIG` | `~/.config/opencode/opencode.json` | OpenCode config to edit. |
| `TSH_SKIP_REGISTER` | `0` | Set `1` to install without touching editor configs. |

## Notes

- The full command/caveat catalogs are sourced from local KBs that are not part of
  this repo. Without them the install still works — `commands.db` is built from the
  curated JSON and `caveats.db` is empty. All curated `data/` knowledge is included.
- If the repo is private, clone it yourself first, then run `./install.sh` from
  inside the checkout (no network clone needed).

## Uninstall

```bash
claude mcp remove tsh-harness -s user           # Claude Code
# OpenCode: delete the "tsh-harness" entry under "mcp" in your opencode.json
rm -rf ~/.local/share/tsh-harness               # if installed via clone mode
```
