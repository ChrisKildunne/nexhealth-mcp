# Workflow: Book an Appointment

## Overview
Booking an appointment requires a patient, provider, operatory, and available time slot — all scoped to the same session location. Follow these steps in order without skipping any.

---

## Required Session State
Before starting, confirm with current_session() that both of the following are set:
- active_subdomain — if missing, call list_institutions() then select_institution()
- active_location_id — if missing, call list_locations() then select_location()

If either is missing, complete session setup before proceeding.

---

## Step-by-Step Flow

### 1. Find the Patient
Call search_patients(name="...") with the patient's name.

- Results are automatically scoped to the session location — do not pass a location_id.
- If multiple results are returned, present them to the user and ask which one to use. Show first name, last name, and date of birth so they can confirm.
- If no results are found, ask the user if they would like to create the patient (see create_patient workflow).
- Never proceed with a patient the user has not explicitly confirmed.

### 2. Find a Provider
Call list_providers() to get available providers at the session location.

- Present the list to the user and ask which provider to use.
- Remember the provider_id for the next step.

### 3. Check Available Slots
Call get_available_slots(provider_id=...) with the confirmed provider.

- Default search is 5 days from today. If the user has a preferred date, pass it as start_date.
- Slots are returned grouped by date with display_time in the location's local timezone — present these to the user, not the raw UTC times.
- Ask the user to pick a date and time.
- Remember the time (raw UTC value) and operatory_id from the chosen slot — both are required for booking.

### 4. Confirm Before Booking
Before calling book_appointment, always summarise the appointment details and ask the user to confirm:

  Patient:    [first name] [last name]
  Provider:   [provider name]
  Date/Time:  [display_time in local timezone]
  Location:   [location name]

Do not book until the user explicitly confirms.

### 5. Book the Appointment
Call book_appointment() with:
- patient_id (from Step 1)
- provider_id (from Step 2)
- start_time (raw UTC time from the slot — do NOT convert, it is already correct)
- operatory_id (from the slot — REQUIRED, booking will fail without it)
- appointment_type_id (optional — ask the user if relevant)

### 6. Confirm Success
After booking, present the returned appointment ID and tell the user the appointment was created successfully. Offer to book another or help with anything else.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| 422 — operatory not available | Slot was taken between search and booking | Re-run get_available_slots and pick a new slot |
| 422 — patient not found | Patient ID does not exist at this location | Re-run search_patients and confirm the patient |
| 401 | Token expired | Server will auto-refresh — retry the call |
| No slots returned | Provider has no availability in the search window | Extend the days parameter or try a different start_date |
