# Workflow: Create an Appointment Type

## What is an Appointment Type?

Appointment types are a **NexHealth construct** — they are not read from or written
to the connected PMS/EHR. They define what kinds of appointments providers offer
and are used to control what patients can book and when.

They are most useful when manually configuring provider schedules (working hours).
By associating appointment types with working hours you can:
- Control what kinds of appointments a provider offers
- Control when specific appointment types are available
  (e.g. "New Patient" only available 9am-12pm on Mondays)

### Scope — Institution vs Location

By default, appointment types are created at the **Institution level** — meaning
they are accessible across all locations. If you need to scope an appointment type
to a single location, set parent_type="Location".

### Relationship to Working Hours

After creating an appointment type, associate it with a working hour by passing
the appointment_type_id when calling create_working_hour(). This controls when
that appointment type is available for booking.

### Relationship to Appointments

When booking an appointment with an appointment_type_id, any EMR descriptors
associated with that type are automatically added to the appointment when it
is created in the health record system.

---

## Required Session State
Confirm with current_session() that active_subdomain is set.
Location is not required for institution-level appointment types.

---

## Step-by-Step Flow

### 1. Collect Required Information
You must have both of the following:

| Field | Notes |
|---|---|
| name | Unique string identifier for this appointment type (required) |
| minutes | Duration in minutes — must be in increments of 5 (required) |

If the user provides a minutes value that is not a multiple of 5, round to the
nearest 5 and confirm with them before proceeding.

### 2. Collect Optional Information

| Field | Notes |
|---|---|
| bookable_online | Whether patients can book this type online (default False) |
| parent_type | "Institution" (default) or "Location" |
| location_id | Required only if parent_type is "Location" |
| parent_id | Required only if parent_type is "Location" — use the location_id value |
| emr_appt_descriptor_ids | List of EMR descriptor IDs to auto-attach to appointments |

### 3. Confirm Before Creating
Summarise and ask the user to confirm:

  Name:            [name]
  Duration:        [minutes] minutes
  Scope:           [Institution / Location]
  Bookable online: [Yes / No]

### 4. Create the Appointment Type
Call create_appointment_type() with all collected fields.

On success, present the returned appointment type ID. Remind the user that
to make this type available for booking they should associate it with a
working hour using create_working_hour(appointment_type_ids=[id]).

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| Validation error — minutes | Not a multiple of 5 | Round to nearest 5 and confirm with user |
| 422 — name already exists | An appointment type with this name exists | Choose a different name or list existing types with list_appointment_types() |
| Validation error — location fields | parent_type is Location but location_id or parent_id missing | Provide both location_id and parent_id |
