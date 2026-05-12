## Step 5 — Make Your First Sandbox API Call

Now that everything is configured, let's verify the full setup with a complete
booking flow. The sandbox comes pre-populated with test patients, providers,
and operatories.

### Step-by-Step in Claude

Ask Claude to run through these tools in order:

  1. list_institutions()                  — find your sandbox subdomain
  2. select_institution(subdomain=...)    — activate it for this session
  3. list_locations()                     — find your location ID
  4. select_location(location_id=...)     — lock in the location
  5. list_providers()                     — pick a provider
  6. list_operatories()                   — pick an operatory
  7. get_available_slots(provider_id=...) — find an open time slot
  8. book_appointment(...)                — create the appointment


### You Are Ready

Your sandbox appointment has been successfully created. The sandbox environment
confirms the API is working correctly. You are now ready to start building!

You are now ready to start building!