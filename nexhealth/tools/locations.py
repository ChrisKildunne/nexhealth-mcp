import json

import nexhealth.session as _session
from nexhealth import config_loader as _cfg
from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.time_utils import _tz_for_location
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def list_locations() -> str:
    """
    List all locations (practice/clinic/office) for this institution.
    Returns a list with each location's id, name, city, state, and phone.
    Most other tools require a location_id — call this first to discover them.
    """
    data = _request("GET", "/locations")
    locations = []
    for inst in data.get("data", []):
        locations.extend(inst.get("locations", []))

    result = [
        {
            "id":    loc.get("id"),
            "name":  loc.get("name"),
            "city":  loc.get("city"),
            "state": loc.get("state"),
            "phone": loc.get("phone"),
        }
        for loc in locations
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def select_location(location_id: int) -> str:
    """
    Set the active location for this session.
    MUST be called after list_locations() before searching patients or booking appointments.
    All patient lookups and bookings are locked to this location for the entire session,
    preventing patients from one location being booked at another.

    Args:
        location_id: The location ID chosen by the user (from list_locations results).

    Returns a confirmation of the selected location including its timezone.
    """
    data = _request("GET", "/locations")
    all_locations = []
    for inst in data.get("data", []):
        all_locations.extend(inst.get("locations", []))

    match = next((loc for loc in all_locations if loc.get("id") == location_id), None)
    if not match:
        valid_ids = [loc.get("id") for loc in all_locations]
        raise RuntimeError(
            f"Location ID {location_id} not found in this institution. "
            f"Valid location IDs are: {valid_ids}. Call list_locations() to see options."
        )

    _session._location_id    = location_id
    _session._location_state = match.get("state", "").strip().upper() if match.get("state") else None
    city                     = match.get("city", "")

    # Config override wins; otherwise resolve by city then state.
    tz_override = _cfg.TIMEZONE_OVERRIDE
    if tz_override:
        _session._location_tz = tz_override
        tz_source = "config override"
        tz_warning = None
    else:
        _session._location_tz, tz_warning = _tz_for_location(city, _session._location_state)
        tz_source = "city lookup" if (city and _session._location_tz) else "state lookup"

    response = {
        "message":        "Location locked for this session.",
        "location_id":    _session._location_id,
        "name":           match.get("name"),
        "city":           city,
        "state":          _session._location_state,
        "timezone":       _session._location_tz or "Unknown — set timezone_override in config.yaml",
        "timezone_source": tz_source,
    }
    if tz_warning:
        response["timezone_warning"] = (
            tz_warning + " If this is wrong, set timezone_override in config.yaml."
        )
    return json.dumps(response, indent=2)
