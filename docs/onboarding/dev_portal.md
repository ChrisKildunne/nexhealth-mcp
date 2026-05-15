## Step 1 — Developer Portal Signup

If you haven't already, you'll need a NexHealth developer account.

1. Sign up at: https://developers.nexhealth.com/signup
2. Once your account is created you'll land on the developer dashboard.

### Collect Your Sandbox API Key

1. In the left panel of the developer portal, click "API Key".
2. Click "Create sandbox API key".
3. A modal will appear showing your generated API key — copy it now.

### Store Your API Key Securely (Mac)

Do NOT paste your API key into the server file directly. Instead, store it in
your Mac keychain so the MCP server can retrieve it securely at runtime:

  security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_key_here"

To verify it was saved correctly:

  security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w

This should print your API key. Once confirmed, your MCP start script will
automatically pull it from the keychain each time it runs.

### Your MCP Start Script

Make sure your start script at ~/Nexhealth/nexhealth-mcp-start.sh contains:

  #!/bin/bash
  export NEXHEALTH_API_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w)
  exec /usr/bin/python3 /Users/YOUR_USERNAME/Nexhealth/server.py

And that your Claude Desktop config points to it:

  {
    "mcpServers": {
      "nexhealth": {
        "command": "/Users/YOUR_USERNAME/Nexhealth/nexhealth-mcp-start.sh",
        "args": []
      }
    }
  }

Once this is done, Claude has access to your sandbox environment.