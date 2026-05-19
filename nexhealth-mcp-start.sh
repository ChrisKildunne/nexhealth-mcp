#!/bin/bash
# NexHealth MCP Server — macOS/Linux start script for Claude Desktop.
#
# The API key is read from the macOS keychain at runtime and exported
# as an environment variable. This works with both:
#   - nexhealth-mcp setup  (stores via keyring)
#   - security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "..."
#
# Optional env var overrides (uncomment and fill in to use):
# export NEXHEALTH_SUBDOMAIN="your-subdomain"  # skips institution selection

# ── Resolve API key from keychain ─────────────────────────────────────────────
export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null)

if [ -z "$NEXHEALTH_API_KEY" ]; then
    echo "ERROR: NEXHEALTH_API_KEY not found in keychain."
    echo ""
    echo "Store it with one of the following:"
    echo "  nexhealth-mcp setup"
    echo "  security add-generic-password -a \"\$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_key\""
    exit 1
fi

# ── Load system prompt if present ─────────────────────────────────────────────
if [ -f "$HOME/nexhealth/nexhealth_system_prompt.txt" ]; then
    export NEXHEALTH_SYSTEM_PROMPT=$(cat "$HOME/nexhealth/nexhealth_system_prompt.txt")
fi

# ── Find Python ───────────────────────────────────────────────────────────────
PYTHON=$(command -v python3)
if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Install Python 3.11+ and try again."
    exit 1
fi

exec "$PYTHON" "$HOME/nexhealth/server.py"
