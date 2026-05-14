## Production Step 4 — Make Your First Production API Call

[PLACEHOLDER — production first call verification steps to be added here]

The flow mirrors the sandbox flow but uses your production institution,
production location, real providers, and real operatories:

  1. list_institutions()                  — confirm your production institution appears
  2. select_institution(subdomain=...)    — activate it for this session
  3. list_locations()                     — find your production location ID
  4. select_location(location_id=...)     — lock in the location
  5. list_providers()                     — confirm real providers are synced
  6. list_operatories()                   — confirm real operatories are synced
  7. get_available_slots(provider_id=...) — find an available slot
  8. book_appointment(...)                — create the appointment

Verify the appointment appears in your live Open Dental instance.