import json

import nexhealth.session as _session
from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.session import _ensure_location
from nexhealth.time_utils import _local_to_utc
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def book_appointment(
    patient_id: int,
    provider_id: int,
    start_time: str,
    operatory_id: int,
    location_id: int = None,
    appointment_type_id: int = None,
    note: str = None,
    notify_patient: bool = False,
) -> str:
    """
    Create (book) an appointment in NexHealth.

    The session location (set by select_location) is always used and enforced.

    Args:
        patient_id:          The NexHealth patient ID (must belong to the session location).
        provider_id:         The NexHealth provider ID.
        start_time:          ISO 8601 start datetime (e.g. "2025-06-01T09:00:00").
                             Get this from the 'time' field in get_available_slots.
        operatory_id:        The operatory/room ID (required). Get this from the
                             'operatory_id' field returned by get_available_slots.
        location_id:         Optional explicit double-check. If provided, must match the
                             session location or the booking is rejected.
        appointment_type_id: (Optional) ID of the appointment type.
        note:                (Optional) A note to attach to the appointment.
        notify_patient:      Whether to send a NexHealth confirmation notification (default False).

    Returns the full NexHealth API response including the new appointment ID.
    """
    session_location = _ensure_location()

    # If the caller passed a location_id, verify it matches — never silently override.
    if location_id is not None and location_id != session_location:
        raise RuntimeError(
            f"Location mismatch: you passed location_id={location_id} but the active "
            f"session location is {session_location}. All bookings must use the session "
            f"location. Call select_location() to change it explicitly."
        )

    # Convert naive local datetime to UTC if no offset is present in start_time.
    # Times from get_available_slots already carry a UTC offset and pass through unchanged.
    if _session._location_tz and "+" not in start_time and start_time[-1] != "Z":
        start_time = _local_to_utc(start_time, _session._location_tz)

    appt_body: dict = {
        "patient_id":  patient_id,
        "provider_id": provider_id,
        "start_time":  start_time,
        "location_id": session_location,
    }
    if operatory_id is not None:
        appt_body["operatory_id"] = operatory_id
    if appointment_type_id:
        appt_body["appointment_type_id"] = appointment_type_id
    if note:
        appt_body["note"] = note

    data = _request(
        "POST",
        "/appointments",
        params={
            "location_id":    session_location,
            "notify_patient": str(notify_patient).lower(),
        },
        body={"appt": appt_body},
    )
    return json.dumps(data, indent=2)


@mcp.tool()
@_tool
def get_appointment(appointment_id: int) -> str:
    """
    Retrieve a single appointment by its NexHealth appointment ID.
    Also interprets and surfaces two important status fields:

    1. PMS sync status — derived from foreign_id_type:
       - If foreign_id_type starts with "Nex", the appointment has NOT yet
         synced to the PMS/EHR. Surface this clearly to the developer.
       - If foreign_id_type contains a PMS name (e.g. "dentrix", "eaglesoft"),
         the appointment has synced. Tell the developer which PMS it synced to.

    2. Unavailable block — if unavailable=true and patient_id is missing,
       this is a blocked time slot, not a real appointment. Label it clearly.

    Args:
        appointment_id: The NexHealth appointment ID to look up.
    """
    data = _request(
        "GET",
        f"/appointments/{appointment_id}",
        params={"include[]": ["patient", "operatory", "appointment_type"]},
    )
    appt = data.get("data", data)

    foreign_id_type = appt.get("foreign_id_type", "") or ""
    if foreign_id_type.startswith("Nex"):
        appt["_pms_sync_status"] = "Not yet synced to PMS — foreign_id_type starts with Nex"
    elif foreign_id_type:
        appt["_pms_sync_status"] = f"Synced to PMS: {foreign_id_type}"
    else:
        appt["_pms_sync_status"] = "Unknown — no foreign_id_type present"

    if appt.get("unavailable") is True and not appt.get("patient_id"):
        appt["_record_type"] = "UNAVAILABLE BLOCK — this is a blocked time slot, not a patient appointment"
    else:
        appt["_record_type"] = "appointment"

    return json.dumps(appt, indent=2)


@mcp.tool()
@_tool
def list_appointments(
    start: str,
    end: str,
    patient_id: int = None,
    provider_id: int = None,
    cancelled: bool = None,
    per_page: int = 100,
    next_page: str = None,
    prev_page: str = None,
) -> str:
    """
    List appointments within a date range at the session location.
    Supports cursor-based pagination (v20240412) — pass next_page or prev_page
    to navigate through large result sets.

    Args:
        start:       ISO 8601 start datetime (e.g. "2026-06-01T00:00:00+0000").
        end:         ISO 8601 end datetime   (e.g. "2026-06-30T23:59:59+0000").
        patient_id:  (Optional) Filter to a specific patient.
        provider_id: (Optional) Filter to a specific provider.
        cancelled:   (Optional) True to show only cancelled; False to exclude cancelled.
        per_page:    Number of results per page (default 100, max 1000).
        next_page:   Cursor to fetch the NEXT page (end_cursor from the previous response).
        prev_page:   Cursor to fetch the PREVIOUS page (start_cursor from the previous response).

    Returns appointments plus a navigation block. Always show the user:
      - How many results were returned
      - Whether there are more pages (has_next_page / has_previous_page)
      - A prompt like "Want me to fetch the next page?" when has_next_page is true.
    Do NOT call this tool again until the user explicitly asks to paginate.

    IMPORTANT — reading results:
      - Records with unavailable=true and no patient_id are UNAVAILABLE BLOCKS
        (blocked time slots). Label these clearly as "[Unavailable Block]" when
        presenting to the user — do not treat them as patient appointments.
    """
    location_id = _ensure_location()

    if next_page and prev_page:
        raise RuntimeError("Pass either next_page or prev_page, not both.")

    params: dict = {
        "location_id": location_id,
        "start":       start,
        "end":         end,
        "per_page":    per_page,
        "include[]":   ["patient", "appointment_type"],
    }
    if patient_id:
        params["patient_id"]     = patient_id
    if provider_id:
        params["provider_ids[]"] = provider_id
    if cancelled is not None:
        params["cancelled"]      = str(cancelled).lower()
    if next_page:
        params["end_cursor"]   = next_page
    elif prev_page:
        params["start_cursor"] = prev_page

    data      = _request("GET", "/appointments", params=params)
    appts     = data.get("data", [])
    page_info = data.get("page_info", {})

    navigation = {
        "has_next_page":     page_info.get("has_next_page", False),
        "has_previous_page": page_info.get("has_previous_page", False),
        "end_cursor":        page_info.get("end_cursor"),    # pass as next_page to go forward
        "start_cursor":      page_info.get("start_cursor"),  # pass as prev_page to go back
    }

    return json.dumps({
        "appointments": appts,
        "count":        len(appts) if isinstance(appts, list) else None,
        "navigation":   navigation,
    }, indent=2)


@mcp.tool()
@_tool
def cancel_appointment(appointment_id: int) -> str:
    """
    Cancel an existing appointment by marking it as cancelled.

    Args:
        appointment_id: The NexHealth appointment ID to cancel.
    """
    data = _request(
        "PATCH",
        f"/appointments/{appointment_id}",
        body={"appt": {"cancelled": True}},
    )
    return json.dumps(data, indent=2)


@mcp.tool()
@_tool
def patch_appointment(
    appointment_id: int,
    confirmed: bool = None,
    cancelled: bool = None,
    checkin_at: str = None,
) -> str:
    """
    Patch (update) an existing appointment. Supports confirming, cancelling,
    and checking in a patient.

    IMPORTANT constraints from the NexHealth API:
      - Only confirmed, cancelled, and checkin_at fields can be patched.
        All other fields are overwritten when NexHealth syncs from the EHR.
      - confirmed can only be changed from false → true (not reversed).
      - checkin_at can only be changed from null → a datetime (not cleared).
      - To reschedule, cancel the original and create a new appointment —
        start/end times cannot be patched directly.

    Args:
        appointment_id: The NexHealth appointment ID to patch (required).
        confirmed:      Set to True to confirm the appointment.
                        Cannot be set back to False once confirmed.
        cancelled:      Set to True to cancel the appointment.
        checkin_at:     Local datetime string for patient check-in
                        (e.g. "2026-06-01T09:05:00"). Will be converted to
                        UTC automatically using the session location timezone.
                        Can only be set once — cannot be cleared after set.

    Returns the full NexHealth API response for the patched appointment.
    """
    appt: dict = {}

    if confirmed is not None:
        appt["confirmed"] = confirmed
    if cancelled is not None:
        appt["cancelled"] = cancelled
    if checkin_at is not None:
        if _session._location_tz and "+" not in checkin_at and checkin_at[-1] != "Z":
            checkin_at = _local_to_utc(checkin_at, _session._location_tz)
        appt["checkin_at"] = checkin_at

    if not appt:
        raise RuntimeError(
            "No fields to patch. Provide at least one of: confirmed, cancelled, checkin_at."
        )

    data = _request("PATCH", f"/appointments/{appointment_id}", body={"appt": appt})
    return json.dumps(data, indent=2)
