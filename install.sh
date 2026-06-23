#!/usr/bin/env bash
#
# TSH harness installer.
#
# Installs the vendor-agnostic network troubleshooting harness as an MCP server
# for Claude Code and/or OpenCode. Re-run it any time to pull GitHub updates and
# refresh the install.
#
#   Fresh install (clones into ~/.local/share/tsh-harness):
#     curl -fsSL https://raw.githubusercontent.com/DendroLabs/troubleshooting-harness/main/install.sh | bash
#
#   From a clone (installs/updates in place):
#     ./install.sh
#
# Environment overrides:
#   TSH_DIR   install location          (default: ~/.local/share/tsh-harness)
#   TSH_REPO  git URL to clone          (default: the DendroLabs repo)
#   PYTHON    python interpreter to use (default: python3)
#
set -euo pipefail

REPO_URL="${TSH_REPO:-https://github.com/DendroLabs/troubleshooting-harness.git}"
DEFAULT_DIR="${HOME}/.local/share/tsh-harness"
PYTHON="${PYTHON:-python3}"
SERVER_NAME="tsh-harness"

# ---------- output helpers ----------------------------------------------------
if [ -t 1 ]; then
  B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; D=$'\033[2m'; X=$'\033[0m'
else
  B=""; G=""; Y=""; R=""; D=""; X=""
fi
info() { printf '%s==>%s %s\n' "$G" "$X" "$*"; }
step() { printf '%s -%s %s\n' "$D" "$X" "$*"; }
warn() { printf '%s!!%s %s\n' "$Y" "$X" "$*" >&2; }
die()  { printf '%sxx%s %s\n' "$R" "$X" "$*" >&2; exit 1; }

# ---------- locate the repo ---------------------------------------------------
# If this script lives inside a checkout, install in place. Otherwise clone.
SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [ -n "$SOURCE" ] && [ -f "$SOURCE" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
fi

if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/.git" ] \
   && [ -f "$SCRIPT_DIR/harness/interfaces/mcp/server.py" ]; then
  INSTALL_DIR="$SCRIPT_DIR"
  info "Installing in place from ${B}${INSTALL_DIR}${X}"
else
  INSTALL_DIR="${TSH_DIR:-$DEFAULT_DIR}"
fi

# ---------- preflight ---------------------------------------------------------
info "Checking prerequisites"
command -v git >/dev/null 2>&1 || die "git is required but not found on PATH."
command -v "$PYTHON" >/dev/null 2>&1 || die "$PYTHON is required but not found on PATH."

PYVER="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' \
  || die "Python 3.10+ required (found $PYVER)."
"$PYTHON" -c 'import venv' 2>/dev/null \
  || die "The Python 'venv' module is required (install python3-venv)."
step "git $(git --version | awk '{print $3}'), python $PYVER"

# ---------- clone or update ---------------------------------------------------
CHANGED=0
if [ -d "$INSTALL_DIR/.git" ]; then
  info "Updating existing install at ${B}${INSTALL_DIR}${X}"
  BEFORE="$(git -C "$INSTALL_DIR" rev-parse HEAD)"
  git -C "$INSTALL_DIR" fetch --quiet origin || warn "git fetch failed; using local copy."
  # Resolve the upstream ref (tracked branch, else origin/main).
  if UPSTREAM="$(git -C "$INSTALL_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"; then
    :
  else
    UPSTREAM="origin/main"
  fi
  if git -C "$INSTALL_DIR" merge-base --is-ancestor "$UPSTREAM" HEAD 2>/dev/null; then
    step "Already up to date ($(git -C "$INSTALL_DIR" rev-parse --short HEAD))."
  else
    if git -C "$INSTALL_DIR" pull --ff-only --quiet; then
      AFTER="$(git -C "$INSTALL_DIR" rev-parse HEAD)"
      [ "$BEFORE" != "$AFTER" ] && CHANGED=1
      step "Updated to $(git -C "$INSTALL_DIR" rev-parse --short HEAD)."
    else
      warn "Could not fast-forward (local changes?). Continuing with current checkout."
    fi
  fi
else
  info "Cloning ${B}${REPO_URL}${X}"
  step "into $INSTALL_DIR"
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone --quiet "$REPO_URL" "$INSTALL_DIR" \
    || die "git clone failed. If the repo is private, clone it manually then run ./install.sh from inside it."
  CHANGED=1
fi

SERVER="$INSTALL_DIR/harness/interfaces/mcp/server.py"
[ -f "$SERVER" ] || die "Server entry point not found at $SERVER"

# ---------- python venv + deps -----------------------------------------------
VENV="$INSTALL_DIR/.venv"
VENV_PY="$VENV/bin/python"
if [ ! -x "$VENV_PY" ]; then
  info "Creating virtualenv"
  "$PYTHON" -m venv "$VENV"
  CHANGED=1
fi

info "Installing Python dependencies"
"$VENV_PY" -m pip install --quiet --upgrade pip >/dev/null
"$VENV_PY" -m pip install --quiet -r "$INSTALL_DIR/requirements.txt" \
  || die "pip install failed."
step "mcp + jsonschema + referencing ready"

# ---------- build SQLite databases -------------------------------------------
DB_DIR="$INSTALL_DIR/data/db"
if [ "$CHANGED" -eq 1 ] || [ ! -f "$DB_DIR/commands.db" ]; then
  info "Building SQLite databases"
  ( cd "$INSTALL_DIR/tools/migrate" && "$VENV_PY" build_sqlite.py ) | sed "s/^/${D} - ${X}/"
else
  step "Databases present and up to date."
fi

# ---------- register the MCP server ------------------------------------------
SERVER_JSON="$("$VENV_PY" - "$VENV_PY" "$SERVER" <<'PY'
import json, sys
print(json.dumps({"type": "stdio", "command": sys.argv[1], "args": [sys.argv[2]]}))
PY
)"

REGISTERED=0

if [ "${TSH_SKIP_REGISTER:-0}" = "1" ]; then
  info "Skipping editor registration (TSH_SKIP_REGISTER=1)"
  step "Server command: $VENV_PY $SERVER"
else
info "Registering with editors"
if command -v claude >/dev/null 2>&1; then
  claude mcp remove "$SERVER_NAME" -s user >/dev/null 2>&1 || true
  if claude mcp add-json "$SERVER_NAME" "$SERVER_JSON" -s user >/dev/null 2>&1; then
    step "Claude Code: registered (user scope)."
    REGISTERED=1
  else
    warn "Claude Code: 'claude mcp add-json' failed. Add it manually:"
    printf '    claude mcp add-json %s %q -s user\n' "$SERVER_NAME" "$SERVER_JSON" >&2
  fi
else
  step "Claude Code: 'claude' not on PATH — skipped."
fi

OPENCODE_CONFIG="${OPENCODE_CONFIG:-$HOME/.config/opencode/opencode.json}"
if command -v opencode >/dev/null 2>&1 || [ -e "$OPENCODE_CONFIG" ]; then
  if "$PYTHON" "$INSTALL_DIR/tools/install/configure_opencode.py" \
        "$OPENCODE_CONFIG" "$SERVER_NAME" "$VENV_PY" "$SERVER" \
        | sed "s/^/${D} - ${X}OpenCode: /"; then
    REGISTERED=1
  fi
else
  step "OpenCode: not detected — skipped."
fi
fi

# ---------- verify ------------------------------------------------------------
info "Verifying install"
"$VENV_PY" - "$INSTALL_DIR" <<'PY' || die "Verification failed — the harness did not load."
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
from harness.src.tools.base import build_context
from harness.interfaces.mcp.tool_dispatch import build_dispatch
ctx = build_context(root)
disp = build_dispatch(ctx)
rules = len(ctx.loader.list_all("interpretation-rules"))
print(f"   {len(disp)} MCP tools, {rules} interpretation rules loaded")
PY

# ---------- summary -----------------------------------------------------------
SHA="$(git -C "$INSTALL_DIR" rev-parse --short HEAD 2>/dev/null || echo '?')"
echo
info "${B}TSH harness installed${X} (${SHA})"
step "location: $INSTALL_DIR"
if [ "$REGISTERED" -eq 1 ]; then
  step "Restart Claude Code / OpenCode, then ask it to use the ${B}${SERVER_NAME}${X} tools."
else
  warn "No editor was registered. Register the server manually with this command:"
  printf '    %s %s\n' "$VENV_PY" "$SERVER" >&2
fi
step "Re-run this installer any time to pull updates."
