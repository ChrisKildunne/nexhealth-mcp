# Workflow: Troubleshooting

## Overview
When a tool returns an error, read the structured error response and use this guide to explain what went wrong and what the developer should do next. Always explain errors in plain English — never just surface the raw API response.

---

## Reading a Structured Error Response

Every error from the server looks like this:

```json
{
  "error": true,
  "code": 422,
  "path": "/appointments",
  "message": "Provider not available at this location",
  "explanation": "The request was valid but could not be processed",
  "detail": { ... }
}
```

Use the message and detail fields to give the developer a specific, actionable explanation.

---

## HTTP Error Code Reference

### 400 — Bad Request
The request body is malformed or missing required fields.
- Check that all required fields are present.
- Check that date formats are YYYY-MM-DD and datetime formats are ISO 8601.
- Check that IDs are integers, not strings.

### 401 — Unauthorized
Authentication failed. The bearer token is invalid or expired.
- The server automatically retries with a fresh token on 401.
- If the error persists, the API key itself may be invalid.
- Ask the developer to verify their API key: security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w

### 403 — Forbidden
The API key does not have permission for this action.
- Sandbox keys cannot make production calls.
- Check that the developer is using the correct key for their environment.

### 404 — Not Found
The requested resource does not exist.
- Verify the ID is correct.
- Confirm the resource belongs to the active session location.
- The resource may have been deleted or may belong to a different institution.

### 422 — Unprocessable Entity
The request is valid but the API cannot process it. This is the most common error. Common causes:

| Message contains | Likely cause | Fix |
|---|---|---|
| already confirmed | Appointment is already confirmed | No action needed — inform the user |
| already cancelled | Appointment is already cancelled | No action needed — inform the user |
| operatory not available | Slot was taken between search and booking | Re-run get_available_slots and pick a new slot |
| patient not found | Patient ID invalid at this location | Re-run search_patients |
| provider not found | Provider ID invalid at this location | Re-run list_providers |
| email already exists | Duplicate patient email | Surface the existing patient |
| overlapping schedule | Working hour conflicts with existing one | Check existing working hours before creating |

### 429 — Too Many Requests
The API rate limit has been hit.
- Wait 30–60 seconds before retrying.
- Avoid calling list endpoints in rapid succession.

### 500 — Server Error
A NexHealth server-side error. Not caused by the request.
- Wait a moment and retry.
- If it persists, the issue is on NexHealth's side.

---

## Session State Errors

These are not HTTP errors — they come from the MCP server itself.

| Message | Cause | Fix |
|---|---|---|
| No institution selected | select_institution() has not been called | Call list_institutions() then select_institution() |
| No location selected | select_location() has not been called | Call list_locations() then select_location() |
| Location mismatch | Passed location_id differs from session location | Always use the session location — do not pass a different location_id |
| No fields to patch | patch_appointment() called with no fields | Pass at least one of: confirmed, cancelled, checkin_at |

---

## General Debugging Steps

1. Call current_session() — confirm subdomain, location, and timezone are all set correctly.
2. Check the error code and message against the tables above.
3. Verify the IDs being passed (patient, provider, operatory) are valid at the session location.
4. If the error is a 401, ask the developer to verify their API key in the keychain.
5. If the error is a 500, wait and retry — do not change the request.
