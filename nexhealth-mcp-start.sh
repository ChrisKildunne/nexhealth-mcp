#!/bin/bash
# NexHealth MCP Server — start script
# Retrieves secrets from the macOS Keychain and launches the server.

# ── Required ────────────────────────────────────────────────────────────────
export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null)

if [ -z "$NEXHEALTH_API_KEY" ]; then
    echo "ERROR: NEXHEALTH_API_KEY not found in keychain."
    echo "Run: security add-generic-password -a \"\$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_api_key_here\""
    exit 1
fi

# ── Optional ─────────────────────────────────────────────────────────────────
# Skip institution selection by pre-setting a subdomain:
# export NEXHEALTH_SUBDOMAIN="your-subdomain"

# Override the timezone for your location (useful for split-timezone states
# like Tennessee where the state default may be wrong for your area):
# export NEXHEALTH_TIMEZONE_OVERRIDE="America/New_York"  # e.g. for Eastern TN

export NEXHEALTH_SYSTEM_PROMPT=$(cat "$HOME/Nexhealth/nexhealth_system_prompt.txt" 2>/dev/null)

# ── Python detection ─────────────────────────────────────────────────────────
# Find python3 without hardcoding a version path. Works on any machine.
PYTHON=$(command -v python3)
if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Install Python 3.11+ and try again."
    exit 1
fi

exec "$PYTHON" "$HOME/Nexhealth/server.py"
