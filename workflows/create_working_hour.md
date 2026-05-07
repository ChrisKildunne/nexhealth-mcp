# Workflow: Create a Working Hour (Provider Availability)

## Overview
Working hours define when a provider is available for appointments. They must be linked to a specific provider and operatory at the session location. Choose exactly one scheduling mode.

---

## Required Session State
Confirm with current_session() that both are set:
- active_subdomain
- active_location_id

---

## Step-by-Step Flow

### 1. Identify the Provider
Call list_providers() if the provider_id is not already known.
Present the list and ask the user which provider this availability is for.

### 2. Identify the Operatory
Call list_operatories() if the operatory_id is not already known.
Operatory is REQUIRED — a working hour cannot be created without one.

### 3. Get the Time Range
Ask the user for:
- begin_time — start time in HH:MM format (e.g. "09:00")
- end_time — end time in HH:MM format (e.g. "17:00")

Times are in the location's local timezone (shown in current_session).

### 4. Choose a Scheduling Mode
Ask the user which type of schedule this is. Only ONE mode can be used per working hour:

**Option A — Recurring Weekly (days)**
Provider works the same days every week.
Example: every Monday and Wednesday.
Pass as: days=["Monday", "Wednesday"]
Valid values: Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday

**Option B — One-Off Date (specific_date)**
Provider is available on a single specific date only.
Example: July 4th cover shift.
Pass as: specific_date="2026-07-04"

**Option C — Custom Recurrence (custom_recurrence)**
Provider works every N days/weeks/months starting from a reference date.
Requires all three fields together:
- custom_recurrence_num: the interval count (e.g. 1)
- custom_recurrence_unit: "day", "week", or "month"
- custom_recurrence_ref: start date in YYYY-MM-DD format

Example: every 1 day starting 2026-05-05

### 5. Confirm Before Creating
Summarise the working hour and ask the user to confirm:

  Provider:  [provider name]
  Operatory: [operatory name]
  Hours:     [begin_time] – [end_time]
  Schedule:  [mode description]
  Active:    Yes

### 6. Create the Working Hour
Call create_working_hour() with all collected fields.

On success, present the returned working hour ID and confirm it is active.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| 422 — overlapping schedule | Another working hour already covers this time | Check existing schedules before creating |
| 422 — invalid days value | Day name not recognised | Check spelling — must be full name e.g. "Monday" not "Mon" |
| 422 — operatory not found | operatory_id not valid at this location | Call list_operatories() and pick a valid one |
| Validation error — missing recurrence fields | custom_recurrence requires all three fields | Ensure num, unit, and ref are all provided |
