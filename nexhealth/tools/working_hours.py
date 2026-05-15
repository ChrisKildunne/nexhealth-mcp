import json

from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.session import _ensure_location
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def create_working_hour(
    provider_id: int,
    begin_time: str,
    end_time: str,
    operatory_id: int,
    days: list = None,
    specific_date: str = None,
    custom_recurrence_num: int = None,
    custom_recurrence_unit: str = None,
    custom_recurrence_ref: str = None,
    appointment_type_ids: list = None,
    active: bool = True,
) -> str:
    """
    Create a working hour (provider availability) at the session location.
    Posts to POST /working_hours using the v20240412 API.

    IMPORTANT: Configure exactly ONE scheduling mode:
      - days:               Recurring weekly (e.g. ["Monday", "Wednesday"])
      - specific_date:      One-off date (e.g. "2026-06-15")
      - custom_recurrence:  Every N days/weeks/months from a reference date.
                            Requires custom_recurrence_num, custom_recurrence_unit,
                            and custom_recurrence_ref all to be provided together.

    Args:
        provider_id:             ID of the provider (required). Use list_providers().
        begin_time:              Start time in HH:MM format, e.g. "09:00" (required).
        end_time:                End time in HH:MM format, e.g. "17:00" (required).
        operatory_id:            ID of the operatory/room (required). Use list_operatories().
        days:                    List of weekday names for a recurring weekly schedule.
                                 Valid values: "Sunday", "Monday", "Tuesday", "Wednesday",
                                 "Thursday", "Friday", "Saturday".
        specific_date:           A single date in YYYY-MM-DD format for a one-off working hour.
        custom_recurrence_num:   Recurrence interval count (e.g. 1 for every 1 day).
        custom_recurrence_unit:  Recurrence unit: "day", "week", or "month".
        custom_recurrence_ref:   Recurrence start date in YYYY-MM-DD format.
        appointment_type_ids:    List of appointment type IDs to associate (optional).
                                 Use list_appointment_types().
        active:                  Whether this working hour is active immediately (default True).

    Returns the full API response for the created working hour including its new ID.
    """
    location_id = _ensure_location()

    using_days       = bool(days)
    using_date       = bool(specific_date)
    using_recurrence = any([custom_recurrence_num, custom_recurrence_unit, custom_recurrence_ref])
    modes_set        = sum([using_days, using_date, using_recurrence])

    if modes_set == 0:
        raise RuntimeError(
            "You must configure exactly one scheduling mode: "
            "'days' for weekly recurrence, 'specific_date' for a one-off date, "
            "or custom_recurrence_num + custom_recurrence_unit + custom_recurrence_ref "
            "for a custom recurrence."
        )
    if modes_set > 1:
        raise RuntimeError(
            "Only one scheduling mode may be configured at a time. "
            "Choose one of: days, specific_date, or custom_recurrence."
        )

    if using_days:
        valid_days = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}
        invalid = [d for d in days if d not in valid_days]
        if invalid:
            raise RuntimeError(
                f"Invalid day(s): {invalid}. Must be one of: {sorted(valid_days)}"
            )

    if using_recurrence:
        missing = [
            name for name, val in [
                ("custom_recurrence_num",  custom_recurrence_num),
                ("custom_recurrence_unit", custom_recurrence_unit),
                ("custom_recurrence_ref",  custom_recurrence_ref),
            ] if not val
        ]
        if missing:
            raise RuntimeError(
                f"custom_recurrence requires all three fields. Missing: {missing}"
            )
        valid_units = {"day", "week", "month"}
        if custom_recurrence_unit not in valid_units:
            raise RuntimeError(
                f"custom_recurrence_unit must be one of: {sorted(valid_units)}. "
                f"Got: '{custom_recurrence_unit}'"
            )

    working_hour: dict = {
        "provider_id":  provider_id,
        "begin_time":   begin_time,
        "end_time":     end_time,
        "operatory_id": operatory_id,
        "active":       active,
    }
    if using_days:
        working_hour["days"] = days
    if using_date:
        working_hour["specific_date"] = specific_date
    if using_recurrence:
        working_hour["custom_recurrence"] = {
            "num":  custom_recurrence_num,
            "unit": custom_recurrence_unit,
            "ref":  custom_recurrence_ref,
        }
    if appointment_type_ids:
        working_hour["appointment_type_ids"] = appointment_type_ids

    data = _request(
        "POST",
        "/working_hours",
        params={"location_id": location_id},
        body={"working_hour": working_hour},
    )
    return json.dumps(data, indent=2)
