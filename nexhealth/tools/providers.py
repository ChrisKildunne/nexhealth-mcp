import json

from nexhealth.app import mcp
from nexhealth.http_client import _request
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
