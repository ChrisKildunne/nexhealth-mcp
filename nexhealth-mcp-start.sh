#!/bin/bash
# NexHealth MCP Server — macOS/Linux start script for Claude Desktop.
#
# Works whether the package was installed via:
#   uv tool install git+https://github.com/ChrisKildunne/nexhealth-mcp.git
#   uv sync (local dev)
#   pip install -r requirements.txt

# ── Resolve API key from keychain ─────────────────────────────────────────────
export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null)

if [ -z "$NEXHEALTH_API_KEY" ]; then
    echo "ERROR: NEXHEALTH_API_KEY not found in keychain."
    echo ""
    echo "Store it with:"
    echo "  nexhealth-mcp setup"
    echo "  security add-generic-password -a \"\$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_key\""
    exit 1
fi

# ── Load system prompt if present ─────────────────────────────────────────────
PROMPT_FILE="$HOME/nexhealth/nexhealth_system_prompt.txt"
if [ -f "$PROMPT_FILE" ]; then
    export NEXHEALTH_SYSTEM_PROMPT=$(cat "$PROMPT_FILE")
fi

# ── Run the server ────────────────────────────────────────────────────────────
# Try nexhealth-mcp command first (installed via uv tool install or pip)
# Fall back to running server.py directly (local dev / cloned repo)
if command -v nexhealth-mcp &>/dev/null; then
    exec nexhealth-mcp
elif [ -f "$HOME/nexhealth/server.py" ]; then
    PYTHON=$(command -v python3)
    if [ -z "$PYTHON" ]; then
        echo "ERROR: python3 not found."
        exit 1
    fi
    exec "$PYTHON" "$HOME/nexhealth/server.py"
else
    echo "ERROR: Cannot find nexhealth-mcp command or server.py"
    echo "Install with: uv tool install git+https://github.com/ChrisKildunne/nexhealth-mcp.git"
    exit 1
fi
