#!/bin/bash
export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null)

if [ -z "$NEXHEALTH_API_KEY" ]; then
    echo "ERROR: NEXHEALTH_API_KEY not found in keychain."
    echo "Run: security add-generic-password -a \"\$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_api_key_here\""
    exit 1
fi

export NEXHEALTH_SYSTEM_PROMPT=$(cat "$HOME/Nexhealth/nexhealth_system_prompt.txt" 2>/dev/null)
export SSL_CERT_FILE="/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/certifi/cacert.pem"
export REQUESTS_CA_BUNDLE="/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/certifi/cacert.pem"
exec /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 "$HOME/Nexhealth/server.py"
