# Workflow: Session Setup

## Overview
Every session must establish an institution and location before any patient, provider, or appointment tools can be used. This workflow should be completed at the start of every conversation.

---

## When to Run This
Run session setup if current_session() shows:
- active_subdomain is not set
- active_location_id is not set
- The developer is starting a new conversation

---

## Step-by-Step Flow

### 1. Authenticate
Authentication is automatic — the server exchanges the API key for a bearer token on the first tool call. No action needed.

If authentication fails, ask the developer to verify their API key:
  security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w

### 2. Select Institution
Call list_institutions() to retrieve all institutions accessible with this API key.

Present the list to the developer:
- Show institution name and subdomain
- If there is only one institution, confirm with the developer before selecting it automatically

Call select_institution(subdomain="...") with the chosen subdomain.

The server will return a list of locations under that institution as confirmation.

### 3. Select Location
Call list_locations() to retrieve all locations under the active institution.

Present the list:
- Show location name, city, and state
- If there is only one location, confirm before selecting automatically

Call select_location(location_id=...) with the chosen location.

The server will return a confirmation including the detected timezone for the location.

### 4. Confirm Session State
Call current_session() and confirm:
- authenticated: true
- active_subdomain is set
- active_location_id is set
- active_timezone is set (used for all time conversions)

If any of these are missing, repeat the relevant step above.

---

## Session Persistence
- The session state (subdomain, location, timezone) persists for the lifetime of the server process.
- If the server is restarted, session setup must be repeated.
- Switching institutions automatically clears the active location — select_location() must be called again.

---

## Shortcut: Environment Variable
If NEXHEALTH_SUBDOMAIN is set in the environment, the institution step is skipped automatically. Only select_location() is needed in this case.
