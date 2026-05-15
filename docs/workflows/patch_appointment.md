# Workflow: Patch an Appointment (Confirm, Cancel, Check In)

## Overview
Patching updates the status of an existing appointment. Only three fields can be patched — confirmed, cancelled, and checkin_at. All other fields are managed by the EHR sync and cannot be changed through the API.

---

## What Can and Cannot Be Patched

| Action | Field | Constraint |
|---|---|---|
| Confirm | confirmed=True | One-way only — cannot be set back to False once confirmed |
| Cancel | cancelled=True | One-way — cancellation cannot be undone via API |
| Check in | checkin_at="YYYY-MM-DDTHH:MM:SS" | One-way — cannot be cleared once set |
| Reschedule | Not supported | Cancel the original and create a new appointment instead |

Never attempt to patch start_time, end_time, provider_id, patient_id, or operatory_id — these will be silently overwritten by the next EHR sync.

---

## Step-by-Step Flow

### 1. Identify the Appointment
If the appointment_id is not already known, call list_appointments() or get_appointment() to find it.

Always confirm the appointment details with the user before patching — show patient name, date, time, and current status.

### 2. Confirm the Action
Ask the user explicitly what they want to do:
- "Confirm this appointment" → set confirmed=True
- "Cancel this appointment" → set cancelled=True
- "Check in this patient" → set checkin_at to current local time

For cancellations, warn the user that this cannot be undone via the API.

### 3. Patch the Appointment
Call patch_appointment() with only the fields that need to change.
Do not pass fields that are not being updated.

For checkin_at, pass the current local datetime in YYYY-MM-DDTHH:MM:SS format — the server will convert it to UTC automatically using the session timezone.

### 4. Confirm Success
Present the returned appointment status and confirm the update was applied.

---

## Rescheduling Flow
To reschedule an appointment:
1. Call patch_appointment(appointment_id=..., cancelled=True) to cancel the original.
2. Follow the book_appointment workflow to create the new appointment at the desired time.
3. Let the user know both steps are required and confirm before executing either.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| 422 — already confirmed | Trying to confirm an already-confirmed appointment | No action needed — inform the user it is already confirmed |
| 422 — already cancelled | Trying to cancel an already-cancelled appointment | No action needed — inform the user it is already cancelled |
| 404 — appointment not found | appointment_id does not exist | Verify the ID with get_appointment() or list_appointments() |
