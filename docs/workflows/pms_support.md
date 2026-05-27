# NexHealth EHR/PMS Integration Parity

Use this guide when a developer asks which PMS systems are supported, or whether
a specific feature works with their EHR. The full interactive parity table is at:
https://docs.nexhealth.com/docs/integration-parity

---

## Supported PMS Systems

### Popular Dental EHR
| PMS | Type | Min Version |
|---|---|---|
| Curve | Cloud | — |
| Denticon | Cloud | — |
| Dentrix | On-premises | G6.2+ |
| Dentrix Ascend | Cloud | — |
| Dentrix Enterprise | On-premises | v8.0.7+ |
| Eaglesoft | On-premises | v18+ |
| Open Dental | On-premises | — |
| Practiceworks | On-premises | All |

### Popular Ortho EHR
| PMS | Type | Min Version |
|---|---|---|
| Cloud9 | Cloud | — |
| Dolphin | On-premises | All |
| Orthotrac Local | On-premises | All |

### Enterprise EHR
| PMS | Type |
|---|---|
| QDW - QSI Dental Web | Cloud |

### Medical EHR
| PMS | Type | Min Version |
|---|---|---|
| Athena | Cloud | — |
| DrChrono | Cloud | — |
| eClinicalWorks | Cloud | v11.53+ |
| ModMed | Cloud | — |

### Not Supported at This Time
- Open Dental Cloud
- eClinicalWorks on-premises (server-based)
- Curve on-premises (server-based)

---

## Feature Parity by PMS

Legend: Yes / No / Planned / N/A

### Baseline (Read Appointments, Patients, Providers, Operatories)
All supported PMS systems support baseline reads. QDW does not read event blocks.

### Patient Features

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Read Operatories | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | N/A | N/A |
| Update Deleted Patients → Inactive | No | No | Yes | No | Yes | Yes | Yes | No | Yes | Yes | Yes | No | Yes | No | Yes | Yes |
| Read Patient Address | No | No | Yes | No | Yes | Yes | Yes | No | No | No | Yes | No | No | No | Yes | Yes |
| Read Guarantor / Head of Household | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes |
| Write to Patient Docs (PDFs) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | No | No | Yes | No | No | No | Yes | Yes |

### Appointment Features (Basic)

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Interpret Multiple Statuses as Confirmed | No | Yes | Yes | No | Yes | No | Yes | No | No | No | No | No | No | No | No | No |
| Interpret Multiple Statuses as Cancelled | No | No | No | No | Yes | No | No | No | No | No | No | No | No | No | Yes | No |
| Populate Appt Checkout Boolean | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | No | No | No | No | Yes | Yes | Yes |
| Populate Sooner If Possible Boolean | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | No | No | Yes | No | No | Yes |
| Read Appointment Notes | No | No | Yes | No | Yes | Yes | Yes | No | Yes | No | No | No | Yes | No | No | Yes |
| Read Patient Recalls | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes | No | No | No | No | No | Yes |

### Appointment Features (Advanced)

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Read Native EHR Appt Types (descriptors) | No | No | Yes | No | Yes | Yes | Yes | No | Yes | No | Yes | No | Yes | No | Yes | Yes |
| Read Service Codes (procedure codes) | No | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | No | Yes | No | No | No | No | No |
| Read Clinical Notes | No | No | Planned | No | No | Planned | Planned | No | No | No | No | No | No | No | No | No |

### Patient & Appointment Writes

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Create Patient in EHR without Appt | No | No | No | No | No | No | No | No | No | No | No | No | No | No | No | No |
| Create Appointment in EHR | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Appointment Insertion Webhook | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

**Note:** Creating a patient via the API creates them in NexHealth only. The patient
is NOT written to the PMS until their first appointment is booked. No PMS currently
supports creating a patient without an appointment.

**Note:** When creating an appointment, a successful API response (200) confirms the
appointment was created in NexHealth — it does NOT confirm insertion into the PMS.
Subscribe to the Appointment Insertion Webhook to track EHR insertion status.

### Online Booking / Slot Availability

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Read Closed Column as Unavailable | No | No | No | No | Yes | Yes | No | No | Yes | Yes | Yes | No | Yes | No | N/A | N/A |
| Read Lunch Blocks as Unavailable | No | No | Yes | No | N/A | Yes | Yes | No | Yes | N/A | No | No | Yes | No | No | Yes |
| Read Holidays as Unavailable | No | Yes | Yes | No | Yes | Yes | Yes | No | Yes | Yes | No | No | Yes | No | No | N/A |
| Read Provider Working Hours from EHR | No | No | No | No | Yes | Yes | Yes | No | No | No | Yes | Yes | Yes | No | Yes | Yes |

**Note:** For integrations that do not read closed columns or lunch blocks as
unavailable, the recommended workaround is to manually configure NexHealth working
hours to reflect the correct schedule.

### Editing Existing Appointments

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Update Cancel Status in EHR | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Update Confirmation Status in EHR | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes | Yes |
| Reschedule Appointment in EHR | No | No | No | No | No | No | No | No | No | No | No | No | No | No | No | No |

**Note:** Rescheduling is not supported for any PMS. To reschedule, cancel the
original appointment and create a new one at the desired time.

### Special Features (Available Upon Request)

| Feature | Curve | Denticon | Dentrix | Dentrix Ascend | Dentrix Ent. | Eaglesoft | Open Dental | Practiceworks | Cloud9 | Dolphin | Orthotrac | QDW | Athena | DrChrono | eCW | ModMed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Integrated Forms | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes | No | Yes | No | No | No | No | Yes |
| Patient Procedures (fees) | No | No | Yes | No | Yes | Yes | Yes | No | No | No | No | No | No | No | No | No |
| Read Patient Insurance Coverages | No | No | Yes | No | Yes | Yes | Yes | No | No | No | No | No | No | No | No | No |
| Patient Financials (Charges/Payments/Adjustments) | No | No | Yes | Yes | Yes | Yes | Yes | No | No | No | No | No | No | No | No | No |
| Read Provider TIN | No | No | Yes | No | Yes | Yes | Yes | No | No | No | No | No | No | No | No | No |
| Read Provider NPI | No | No | Yes | Yes | Yes | No | No | No | No | No | No | No | Yes | No | Yes | No |

---

## Quick Reference — Most Common Questions

**Which PMS systems support appointment creation (writes)?**
All supported PMS systems support creating appointments via the API.

**Which PMS systems support appointment cancellation writes?**
All except Practiceworks, Dolphin, and QDW.

**Which PMS systems support confirmation status writes?**
All except QDW.

**Does any PMS support rescheduling via the API?**
No — rescheduling is not supported for any PMS. Cancel and recreate.

**Which PMS systems support reading provider working hours?**
Dentrix Enterprise, Eaglesoft, Open Dental, QDW, Athena, eClinicalWorks, ModMed.
All others require manually configured NexHealth working hours.

**Which PMS systems support service codes (procedure codes)?**
Denticon, Dentrix, Dentrix Ascend, Dentrix Enterprise, Eaglesoft, Open Dental,
Cloud9, Orthotrac.

**Which PMS systems support reading clinical notes?**
None currently. Planned for Dentrix, Eaglesoft, and Open Dental.

**Can I create a patient in the EHR without booking an appointment?**
No — no PMS supports this. Patients are written to the EHR on first appointment booking.

**Which PMS systems support integrated forms?**
Curve, Denticon, Dentrix, Dentrix Ascend, Dentrix Enterprise, Eaglesoft,
Open Dental, Cloud9, Orthotrac, ModMed. Contact developers@nexhealth.com to get started.

---

## Important Notes for Developers

- **Appointment insertion is asynchronous** — a 200 response means the appointment
  was created in NexHealth, not that it reached the EHR. Use the Appointment
  Insertion Webhook to track EHR insertion.

- **Patient creation is NexHealth-only** until the first appointment is booked.
  Do not build workflows that assume the patient exists in the EHR before booking.

- **Working hours** — if the PMS does not support syncing provider working hours,
  you must manually configure them in NexHealth via the working_hours endpoint.

- **Special features** (forms, procedures, insurance, financials, TIN, NPI) are
  available upon request. Contact developers@nexhealth.com.
