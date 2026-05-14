## Production Step 3 — Generate and Store Your Production API Key

### Generate a Production API Key

1. Log in to your NexHealth developer portal.

2. Make sure you are in production mode — the purple "Test mode" banner
   should NOT be visible. If it is, flip the toggle at the top right to
   disable test mode.

3. In the left panel, click "API Key".

4. Click "Create API key" (or "Create production API key").

5. A modal will appear showing your generated key — copy it immediately.
   This is the only time the full key is shown.

Once you have your production API key, store it securely in your Mac keychain:

  security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_production_key_here"

If you already have a sandbox key stored under NEXHEALTH_API_KEY, use a
different service name to avoid overwriting it:

  security add-generic-password -a "$USER" -s "NEXHEALTH_PROD_API_KEY" -w "your_production_key_here"

Then update your start script to use the correct key for whichever environment
you are targeting.