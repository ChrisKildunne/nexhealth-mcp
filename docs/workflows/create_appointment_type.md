# Workflow: Create and Configure Appointment Types

## What is an Appointment Type?

Appointment types are a **NexHealth construct** — they are not read from or written
to the connected PMS/EHR directly. They define what kinds of appointments providers
offer and are used to control what patients can book and when.

Think of a NexHealth appointment type as a **logical bundle** — it groups together:
- A name and duration (e.g. "Cleaning", 60 minutes)
- One or more EMR appointment descriptors (procedure codes or EHR-specific types)
- Association with specific working hours (controls when it's bookable)

When an appointment is booked with an `appointment_type_id`, any descriptors
linked to that type are **automatically written to the PMS/EHR**, ensuring the
practice has the correct procedure codes and billing information.

---

## What are Appointment Descriptors?

Appointment descriptors are synced FROM the PMS/EHR — they cannot be created
via the API. There are two types:

**Procedure Codes** — CDT codes (dental) or CPT codes (medical)
Example: "Composite-2 Surf, Posterior" / code "T5833"
Supported PMS: Cloud9, Denticon, Dentrix, Dentrix Ascend, Dentrix Enterprise,
Eaglesoft, Open Dental, Orthotrac

**EHR-specific Appointment Types** — appointment categories in specific systems
Example: "NEW PRIMARY CARE VISIT" / code "NPR"
Supported PMS: athenahealth, Cloud9, Dentrix, Dentrix Enterprise, Eaglesoft,
eClinicalWorks, Open Dental, NextGen, Modmed, Orthotrac

Use list_appointment_descriptors() to see all descriptors available at the
session location. Pass their IDs as emr_appt_descriptor_ids when creating or
updating an appointment type.

---

## Scope — Institution vs Location

By default, appointment types are created at the **Institution level** — accessible
across all locations. To scope to a single location, set parent_type="Location"
and provide both location_id and parent_id.

---

## Full End-to-End Flow

### Step 1 — List Available Descriptors (optional but recommended)
Call list_appointment_descriptors() to see what procedure codes and EHR-specific
types are available at the location. Show these to the developer so they can
decide which to associate.

Filter by type if needed:
- list_appointment_descriptors(descriptor_type="Procedure Codes")
- list_appointment_descriptors(descriptor_type="Appointment Type")

### Step 2 — Collect Required Information

| Field | Notes |
|---|---|
| name | Unique string identifier (required) |
| minutes | Duration in minutes, must be multiple of 5 (required) |

If the user provides minutes that is not a multiple of 5, round to the nearest
5 and confirm before proceeding.

### Step 3 — Collect Optional Information

| Field | Notes |
|---|---|
| bookable_online | Whether patients can book online (default False) |
| parent_type | "Institution" (default) or "Location" |
| location_id | Required only if parent_type is "Location" |
| parent_id | Required only if parent_type is "Location" — use location_id value |
| emr_appt_descriptor_ids | List of descriptor IDs from list_appointment_descriptors() |

### Step 4 — Confirm Before Creating
Summarise and ask the user to confirm:

  Name:            [name]
  Duration:        [minutes] minutes
  Scope:           [Institution / Location]
  Bookable online: [Yes / No]
  Descriptors:     [list of descriptor names, or "None"]

### Step 5 — Create the Appointment Type
Call create_appointment_type() with all collected fields.

### Step 6 — Associate with Working Hours
Remind the developer: to make this appointment type available for booking,
associate it with a working hour by passing appointment_type_ids=[id] when
calling create_working_hour(). This controls when the type is available.

---

## Updating an Existing Appointment Type

To add or update descriptors on an existing appointment type, call
patch_appointment_type(appointment_type_id=..., emr_appt_descriptor_ids=[...]).

IMPORTANT: emr_appt_descriptor_ids REPLACES the existing list entirely.
Always include all IDs you want associated — not just the new ones.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| Validation — minutes not multiple of 5 | e.g. 17 minutes passed | Round to nearest 5 and confirm |
| 422 — name already exists | Duplicate name at this scope | Choose a different name or list existing types |
| Validation — location fields missing | parent_type is Location but location_id or parent_id missing | Provide both |
| No descriptors returned | PMS may not support descriptors, or none synced yet | Check supported PMS list above |

---

## Important: When Are Descriptors Written to the PMS?

Descriptor writes are **synchronous** — they happen at the exact moment the
appointment is created, not on a sync cycle.

This means:
- When POST /appointments is called with an appointment_type_id, the associated
  descriptors are written to the PMS immediately as part of that same operation
- The developer does not need to wait for a sync cycle to verify descriptors
- If you call get_appointment() immediately after booking, the descriptors
  should already be present on the appointment in the PMS
