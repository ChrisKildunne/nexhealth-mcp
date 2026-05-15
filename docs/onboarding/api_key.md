## Step 4 — Store Your API Key

Your API key authenticates every request the MCP server makes to NexHealth.
Never hardcode it into source files — store it in your Mac keychain instead.

### Save the Key

  security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_key_here"

Replace "your_key_here" with the API key you copied from the developer portal.

### Verify It Was Saved

  security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w

This should print your key. If it throws an error, run the add command again.

### How the MCP Server Uses It

Your start script retrieves the key from the keychain at runtime:

  #!/bin/bash
  export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w)
  exec /usr/bin/python3 /Users/YOUR_USERNAME/Nexhealth/server.py

The key is never written to any file — it is only loaded into memory for the
duration of the server session.