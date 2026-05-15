import os
import json

import nexhealth.session as _session
from nexhealth.app import mcp
from nexhealth.auth import _get_token
from nexhealth.http_client import _raw_request
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def list_institutions() -> str:
    """
    ALWAYS CALL THIS FIRST (unless NEXHEALTH_SUBDOMAIN env var is set).

    Fetches all institutions accessible with this API key and returns each
    institution name, id, and subdomain so the user can choose which one
    to work with.

    After the user selects an institution, call select_institution(subdomain=...)
    to activate it for the rest of the session.
    """
    token = _get_token()
    data  = _raw_request("GET", "/institutions", token)

    # Surface auth/network errors instead of silently returning "no institutions"
    if isinstance(data, dict) and data.get("error"):
        return json.dumps(data, indent=2)

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("institutions", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":        inst.get("id"),
            "name":      inst.get("name"),
            "subdomain": inst.get("subdomain"),
            "locations": [
                {
                    "id":    loc.get("id"),
                    "name":  loc.get("name"),
                    "city":  loc.get("city"),
                    "state": loc.get("state"),
                }
                for loc in inst.get("locations", [])
            ],
        }
        for inst in raw
    ]

    if not result:
        return json.dumps({
            "message": (
                "No institutions found for this API key. "
                "Check that NEXHEALTH_API_KEY is correct."
            )
        })

    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def select_institution(subdomain: str) -> str:
    """
    Set the active institution subdomain for this session.
    Call this after list_institutions() once the user has chosen an institution.
    All subsequent tool calls will automatically use this subdomain — no need
    to pass it again.

    Args:
        subdomain: The institution subdomain chosen by the user
                   (from the subdomain field in list_institutions results).

    Returns a confirmation and the list of locations under that institution.
    """
    _session._subdomain  = subdomain.strip()
    _session._location_id = None   # reset location when institution changes

    token = _get_token()
    try:
        data = _raw_request("GET", "/locations", token, subdomain=_session._subdomain)
        locations = []
        for inst in data.get("data", []):
            locations.extend(inst.get("locations", []))
        loc_list = [
            {"id": loc.get("id"), "name": loc.get("name"),
             "city": loc.get("city"), "state": loc.get("state")}
            for loc in locations
        ]
        return json.dumps({
            "message":   f"Institution '{_session._subdomain}' selected and active for this session.",
            "locations": loc_list,
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "message": (
                f"Institution '{_session._subdomain}' selected. "
                f"(Could not pre-fetch locations: {e})"
            ),
        }, indent=2)


@mcp.tool()
@_tool
def current_session() -> str:
    """
    Show the current session state: which institution/subdomain and location
    are active, and whether authentication is established.
    Useful for confirming setup before making other calls.
    """
    from nexhealth import config_loader as _cfg
    cfg_sub = _cfg.SUBDOMAIN
    return json.dumps({
        "authenticated":      _session._bearer_token is not None,
        "active_subdomain":   (
            _session._subdomain or cfg_sub or "(not set — call list_institutions first)"
        ),
        "subdomain_source":   (
            "config/env" if (not _session._subdomain and cfg_sub)
            else ("select_institution()" if _session._subdomain else "none")
        ),
        "active_location_id": (
            _session._location_id or "(not set — call select_location after listing locations)"
        ),
        "active_timezone":    _session._location_tz or "(not set — select a location first)",
        "active_state":       _session._location_state or "(not set)",
    }, indent=2)
