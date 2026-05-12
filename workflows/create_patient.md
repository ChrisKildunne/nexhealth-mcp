# Workflow: Create a Patient

## Overview
Creating a patient registers them at the active session location. Always search for the patient first — never create a duplicate.

---

## Required Session State
Confirm with current_session() that both are set:
- active_subdomain
- active_location_id

---

## Step-by-Step Flow

### 1. Search First — Never Skip This
Call search_patients(name="...") before creating anyone.

- If a matching patient is found, present them to the user and ask: "I found an existing patient — is this the person you meant?"
- Only proceed to create if the user confirms no match exists.
- Creating duplicates causes data integrity issues in the EHR.

### 2. Collect Required Information
You must have ALL of the following before calling create_patient:

| Field | Notes |
|---|---|
| first_name | Required |
| last_name | Required |
| email | Required |
| date_of_birth | Required — YYYY-MM-DD format |
| phone_number | Required — primary contact number |
| provider_id | Required — the intake provider. Call list_providers() if unknown |

If any required field is missing, ask the user for it before proceeding. Do not call create_patient with missing required fields.

### 3. Collect Optional Information
Gather these if the user has them — they improve the patient record but are not required:

- gender (Male, Female, or Other)
- cell_phone_number
- home_phone_number
- address_line_1, address_line_2, city, state, zip_code

### 4. Confirm Before Creating
Summarise the patient details and ask the user to confirm before creating:

  Name:     [first_name] [last_name]
  DOB:      [date_of_birth]
  Email:    [email]
  Phone:    [phone_number]
  Provider: [provider name]

### 5. Create the Patient
Call create_patient() with all collected fields.

On success, present the new patient's ID and confirm they have been created at the session location.

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| 422 — email already exists | A patient with this email exists at this location | Surface the existing patient to the user |
| 422 — invalid date format | date_of_birth not in YYYY-MM-DD format | Reformat and retry |
| 422 — provider not found | provider_id is not valid at this location | Call list_providers() and pick a valid one |
