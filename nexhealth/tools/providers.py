import json

from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.session import _ensure_location
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def list_providers(location_id: int) -> str:
    """
    List all active providers at a given location.

    Args:
        location_id: The location to list providers for.

    Returns a list with each provider's id, first_name, last_name, and title.
    """
    data = _request("GET", "/providers", params={"location_id": location_id, "active": "true"})

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("providers", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":         p.get("id"),
            "first_name": p.get("first_name"),
            "last_name":  p.get("last_name"),
            "title":      p.get("title"),
        }
        for p in raw
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def list_appointment_types(location_id: int) -> str:
    """
    List all appointment types configured at a location.

    Args:
        location_id: The location to list appointment types for.

    Returns id, name, duration (minutes), and whether it is active.
    Use the returned id as appointment_type_id in get_available_slots.
    """
    data = _request("GET", "/appointment_types", params={"location_id": location_id})

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("appointment_types", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":       t.get("id"),
            "name":     t.get("name"),
            "duration": t.get("minutes") or t.get("duration"),
            "active":   t.get("active"),
        }
        for t in raw
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def create_appointment_type(
    name: str,
    minutes: int,
    bookable_online: bool = False,
    parent_type: str = "Institution",
    location_id: int = None,
    parent_id: int = None,
    emr_appt_descriptor_ids: list = None,
) -> str:
    """
    Create a new appointment type.

    Appointment types are a NexHealth construct — they are NOT read from or
    written to the connected PMS/EHR. They define what kinds of appointments
    providers offer and are used to control what patients can book and when.

    By default appointment types are created at the Institution level, meaning
    they are accessible across all locations. To scope to a specific location,
    set parent_type="Location" and provide both location_id and parent_id.

    IMPORTANT: minutes must be in increments of 5 (e.g. 15, 30, 45, 60).

    Args:
        name:                    Appointment type name — must be unique (required).
        minutes:                 Duration in minutes, increments of 5 (required).
        bookable_online:         Whether this type appears on the NexHealth online
                                 booking page (default False).
        parent_type:             "Institution" (default) — accessible across all
                                 locations, or "Location" — scoped to one location.
        location_id:             Required when parent_type is "Location".
        parent_id:               ID of the parent model. Required when parent_type
                                 is "Location" — use the location_id value here.
        emr_appt_descriptor_ids: Optional list of EMR appointment descriptor IDs
                                 to associate. Any descriptors linked here will be
                                 automatically written to the PMS/EHR when an
                                 appointment is booked with this appointment_type_id.
                                 Use list_appointment_descriptors() to find valid IDs.

    Returns the full API response including the new appointment type ID.
    """
    if minutes % 5 != 0:
        raise RuntimeError(
            f"minutes must be in increments of 5 (e.g. 15, 30, 45, 60). Got: {minutes}"
        )

    if parent_type == "Location":
        if not location_id:
            raise RuntimeError(
                "location_id is required when parent_type is 'Location'."
            )
        if not parent_id:
            raise RuntimeError(
                "parent_id is required when parent_type is 'Location'. "
                "Use the location_id value for parent_id."
            )

    appt_type: dict = {
        "name":            name,
        "minutes":         minutes,
        "bookable_online": bookable_online,
        "parent_type":     parent_type,
    }
    if parent_type == "Location":
        appt_type["parent_id"] = parent_id
    if emr_appt_descriptor_ids:
        appt_type["emr_appt_descriptor_ids"] = emr_appt_descriptor_ids

    params = {}
    if location_id:
        params["location_id"] = location_id

    data = _request(
        "POST",
        "/appointment_types",
        params=params if params else None,
        body={"appointment_type": appt_type},
    )
    return json.dumps(data, indent=2)


@mcp.tool()
@_tool
def patch_appointment_type(
    appointment_type_id: int,
    emr_appt_descriptor_ids: list = None,
    name: str = None,
    minutes: int = None,
    bookable_online: bool = None,
) -> str:
    """
    Update an existing appointment type.

    Most commonly used to associate EMR appointment descriptors (procedure codes
    or EHR-specific appointment types) with an existing appointment type. Once
    associated, those descriptors are automatically written to the PMS/EHR
    whenever an appointment is booked with this appointment_type_id.

    IMPORTANT: emr_appt_descriptor_ids REPLACES the existing list entirely.
    Always include all IDs you want associated — not just the new ones.

    Args:
        appointment_type_id:     The ID of the appointment type to update (required).
                                 Use list_appointment_types() to find valid IDs.
        emr_appt_descriptor_ids: List of descriptor IDs to associate. Use
                                 list_appointment_descriptors() to find valid IDs.
                                 This REPLACES the existing list — include all IDs
                                 you want associated, not just the new ones.
        name:                    (Optional) Update the appointment type name.
        minutes:                 (Optional) Update the duration. Must be a multiple of 5.
        bookable_online:         (Optional) Update whether bookable online.

    Returns the full API response for the updated appointment type.
    """
    if minutes is not None and minutes % 5 != 0:
        raise RuntimeError(
            f"minutes must be in increments of 5 (e.g. 15, 30, 45, 60). Got: {minutes}"
        )

    appt_type: dict = {}
    if emr_appt_descriptor_ids is not None:
        appt_type["emr_appt_descriptor_ids"] = emr_appt_descriptor_ids
    if name is not None:
        appt_type["name"] = name
    if minutes is not None:
        appt_type["minutes"] = minutes
    if bookable_online is not None:
        appt_type["bookable_online"] = bookable_online

    if not appt_type:
        raise RuntimeError(
            "No fields to update. Provide at least one of: emr_appt_descriptor_ids, "
            "name, minutes, bookable_online."
        )

    data = _request(
        "PATCH",
        f"/appointment_types/{appointment_type_id}",
        body={"appointment_type": appt_type},
    )
    return json.dumps(data, indent=2)


@mcp.tool()
@_tool
def list_appointment_descriptors(
    descriptor_type: str = None,
) -> str:
    """
    List all appointment descriptors (procedure codes and EHR-specific appointment
    types) available at the session location.

    Appointment descriptors are synced FROM the connected PMS/EHR — they cannot
    be created via the API. They represent:
      - Procedure Codes: CDT codes (dental) or CPT codes (medical)
        e.g. "Composite-2 Surf, Posterior" / code "T5833"
      - EHR-specific Appointment Types: appointment categories in systems like
        athenahealth e.g. "NEW PRIMARY CARE VISIT" / code "NPR"

    Use the returned descriptor IDs as emr_appt_descriptor_ids when calling
    create_appointment_type() or patch_appointment_type(). When an appointment
    is booked with an appointment_type_id, all associated descriptors are
    automatically written to the PMS/EHR at the moment the appointment is created
    — not on a sync cycle.

    Supported PMS systems for Procedure Codes:
      Cloud9, Denticon, Dentrix, Dentrix Ascend, Dentrix Enterprise,
      Eaglesoft, Open Dental, Orthotrac

    Supported PMS systems for EHR-specific Appointment Types:
      athenahealth, Cloud9, Dentrix, Dentrix Enterprise, Eaglesoft,
      eClinicalWorks, Open Dental, NextGen, Modmed, Orthotrac

    Args:
        descriptor_type: (Optional) Filter by type. Pass "Procedure Codes" to
                         see only procedure codes, or "Appointment Type" to see
                         only EHR-specific appointment types. Leave blank for all.

    Returns a list of descriptors with id, name, code, and descriptor_type.
    """
    location_id = _ensure_location()

    params = {}
    if descriptor_type:
        params["descriptor_type"] = descriptor_type

    data = _request(
        "GET",
        f"/locations/{location_id}/appointment_descriptors",
        params=params if params else None,
    )

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("appointment_descriptors", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":              d.get("id"),
            "name":            d.get("name"),
            "code":            d.get("code"),
            "descriptor_type": d.get("descriptor_type"),
            "active":          d.get("active"),
            "foreign_id_type": d.get("foreign_id_type"),
        }
        for d in raw
        if d.get("active", True)
    ]
    return json.dumps(result, indent=2)
