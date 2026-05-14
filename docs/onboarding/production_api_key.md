## Production Step 3 — Generate and Store Your Production API Key

[PLACEHOLDER — steps for generating a production API key to be added here]

Once you have your production API key, store it securely in your Mac keychain:

  security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_production_key_here"

If you already have a sandbox key stored under NEXHEALTH_API_KEY, use a
different service name to avoid overwriting it:

  security add-generic-password -a "$USER" -s "NEXHEALTH_PROD_API_KEY" -w "your_production_key_here"

Then update your start script to use the correct key for whichever environment
you are targeting.