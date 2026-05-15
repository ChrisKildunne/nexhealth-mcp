import json

from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def list_operatories(location_id: int) -> str:
    """
    List all operatories (chairs/rooms) at a location.

    Args:
        location_id: The location to list operatories for.
    """
    data = _request("GET", "/operatories", params={"location_id": location_id})
    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("operatories", [])
    if not isinstance(raw, list):
        raw = []
    return json.dumps(raw, indent=2)
