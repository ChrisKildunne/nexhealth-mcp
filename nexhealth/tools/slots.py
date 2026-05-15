import json
from datetime import datetime
from zoneinfo import ZoneInfo

import nexhealth.session as _session
from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.session import _ensure_location
from nexhealth.time_utils import _utc_to_local
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def get_available_slots(
    provider_id: int,
    start_date: str = None,
    days: int = 5,
    appointments_per_timeslot: int = 1,
    overlapping_operatory_slots: bool = False,
    appointment_type_id: int = None,
) -> str:
    """
    Fetch available appointment slots for a provider at the session location.
    Hits GET /available_slots using the v20240412 API.

    Args:
        provider_id:                 The provider whose schedule to check (required).
                                     Use list_providers() to find valid IDs.
        start_date:                  Date to start searching from (YYYY-MM-DD).
                                     Defaults to today in the location's local timezone.
        days:                        Number of days to search from start_date (default 5).
        appointments_per_timeslot:   Max appointments to return per time slot (default 1).
        overlapping_operatory_slots: Return all operatory slots at a given time rather
                                     than just the first found (default False).
        appointment_type_id:         (Optional) Filter slots by appointment type.
                                     Use list_appointment_types() to find valid IDs.

    Returns slots grouped by date. Each slot includes time, end_time, display_time,
    and operatory_id. Pass operatory_id directly into book_appointment.
    """
    location_id = _ensure_location()

    if not start_date:
        # Use the location's timezone for "today" to avoid date boundary errors
        # when the server runs in a different timezone than the practice.
        tz = ZoneInfo(_session._location_tz) if _session._location_tz else None
        start_date = datetime.now(tz=tz).strftime("%Y-%m-%d")

    params = {
        "lids[]":                      location_id,
        "pids[]":                      provider_id,
        "start_date":                  start_date,
        "days":                        days,
        "appointments_per_timeslot":   appointments_per_timeslot,
        "overlapping_operatory_slots": str(overlapping_operatory_slots).lower(),
    }
    if appointment_type_id:
        params["appointment_type_id"] = appointment_type_id

    data = _request("GET", "/available_slots", params=params)

    grouped: dict = {}
    for entry in data.get("data", []):
        for slot in entry.get("slots", []):
            time_str = slot.get("time", "")
            try:
                dt   = datetime.fromisoformat(time_str)
                date = dt.strftime("%Y-%m-%d")
                disp = dt.strftime("%I:%M %p").lstrip("0")
            except Exception:
                date = time_str[:10]
                disp = time_str[11:16]

            raw_time     = slot.get("time", "")
            raw_end_time = slot.get("end_time", "")
            local_disp   = _utc_to_local(raw_time, _session._location_tz) if _session._location_tz and raw_time else disp
            local_end    = _utc_to_local(raw_end_time, _session._location_tz) if _session._location_tz and raw_end_time else raw_end_time

            grouped.setdefault(date, []).append({
                "time":             raw_time,        # UTC — pass directly to book_appointment
                "end_time":         raw_end_time,    # UTC
                "display_time":     local_disp,      # local time for display
                "display_end_time": local_end,       # local time for display
                "timezone":         _session._location_tz or "UTC",
                "operatory_id":     slot.get("operatory_id"),
                "location_id":      entry.get("lid"),
                "provider_id":      entry.get("pid"),
            })

    return json.dumps(grouped, indent=2)
