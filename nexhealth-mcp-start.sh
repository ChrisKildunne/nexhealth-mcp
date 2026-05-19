#!/bin/bash
# NexHealth MCP Server — macOS/Linux start script for Claude Desktop.
#
# The API key is read automatically from the system keychain at runtime.
# To store your key: python -m nexhealth setup
#
# Optional env var overrides (uncomment and fill in to use):
# export NEXHEALTH_API_KEY="your_key"          # skips keychain lookup
# export NEXHEALTH_SUBDOMAIN="your-subdomain"  # skips institution selection

PYTHON=$(command -v python3)
if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Install Python 3.11+ and try again."
    exit 1
fi

exec "$PYTHON" "$HOME/nexhealth/server.py"
