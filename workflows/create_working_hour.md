# Workflow: Create a Working Hour (Provider Availability)

## What is a Working Hour?

A working hour defines when a provider is available to see patients, and in which operatory. Think of it as a **window of availability** — when the window is open, the provider is available and `get_available_slots` will return slots within that window. When the window is fully booked, the working hour still exists but no available slots are returned because the provider is booked up.

Working hours tell the NexHealth API: "When you look for available slots, look at this provider, on this day, in this operatory."

### Key concepts

- **Working hours are a NexHealth construct** — when created via the API, they exist only in NexHealth and are NOT synced back into the PMS/EHR. They take effect immediately and `get_available_slots` will return slots against them right away.
- **Synced working hours** are created in the PMS/EHR and synced INTO NexHealth by the synchronizer. These are read-only from the API perspective.
- **Providers can have multiple working hours** across different operatories, including overlapping time windows. For example, a provider can be configured 9am-5pm in Operatory A and also 9am-5pm in Operatory B simultaneously — this is valid and expected.
- **Slots are returned per operatory** — `get_available_slots` returns slots scoped to the operatory. While operatory is not strictly required in the request, it is highly recommended to specify it for accurate results.

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

Present the list to the user. Remember that a provider can have working hours
in multiple operatories — ask which operatory this specific working hour is for.

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
Example: a cover shift on July 4th.
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
  Hours:     [begin_time] – [end_time] ([local timezone])
  Schedule:  [mode description]
  Active:    Yes

### 6. Create the Working Hour
Call create_working_hour() with all collected fields.

On success, present the returned working hour ID and confirm it is active.
Remind the user that available slots within this window will be returned
immediately by get_available_slots.

---

## After Creating — Verifying Slots

To verify the working hour is producing available slots, call:
get_available_slots(provider_id=..., start_date=...)

Slots should appear immediately. If no slots are returned:
- Check that the working hour is marked active
- Check that the date range overlaps with the working hour schedule
- Check that the operatory_id matches the one on the working hour
- Check that the provider is not already fully booked in that window

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| 422 — overlapping schedule | Another working hour already covers this time in the same operatory | Overlapping hours across different operatories are fine |
| 422 — invalid days value | Day name not recognised | Must be full name e.g. "Monday" not "Mon" |
| 422 — operatory not found | operatory_id not valid at this location | Call list_operatories() and pick a valid one |
| Validation error — missing recurrence fields | custom_recurrence requires all three fields | Ensure num, unit, and ref are all provided |
| No slots returned after creation | Working hour exists but window is fully booked | The window is open but all slots are taken — this is expected behavior |
