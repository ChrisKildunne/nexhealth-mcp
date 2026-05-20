#!/usr/bin/env python3
"""
NexHealth MCP Server
====================
Exposes NexHealth API capabilities as MCP tools so Claude (or any MCP client)
can book appointments, search patients, list providers, and more.

Setup:
    pip install "mcp[cli]"

Environment variables:
    NEXHEALTH_API_KEY   – Your NexHealth API key (required)
    NEXHEALTH_SUBDOMAIN – (Optional) Skip institution selection and use this subdomain directly

Session flow (automatic, on first tool call):
    1. Exchange API key for bearer token
    2. If NEXHEALTH_SUBDOMAIN is set → use it immediately
       Otherwise → call GET /institutions, return list to Claude so the
       user can pick one via select_institution(), then cache the choice.

Run (stdio transport – for use with Claude Desktop / local MCP clients):
    python nexhealth_mcp_server.py

Run (SSE transport – for hosted/remote use, e.g. Claude.ai MCP connector):
    python nexhealth_mcp_server.py --sse --port 8080
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ─── Config ───────────────────────────────────────────────────────────────────

BASE_URL    = "https://nexhealth.info"
API_VERSION = "v20240412"
USER_AGENT  = (
    "NexHealth-MCP-Server/1.0 "
    "Mozilla/5.0 (compatible; MCP; Python)"
)

# ─── Session state (populated automatically on first tool call) ───────────────

_bearer_token:   Optional[str] = None
_subdomain:      Optional[str] = None   # set by select_institution() or env var
_location_id:    Optional[int] = None   # set by select_location(); enforced on all patient + booking calls
_location_tz:    Optional[str] = None   # IANA timezone string for the active location, e.g. "America/Denver"
_location_state: Optional[str] = None   # US state abbreviation for the active location

# ─── State → IANA timezone lookup ─────────────────────────────────────────────
# Maps US state abbreviations to their primary IANA timezone identifier.
# Covers the standard timezone for each state; edge cases (e.g. parts of Indiana,
# Navajo Nation) are not differentiated.

_STATE_TIMEZONES = {
    "AL": "America/Chicago",
    "AK": "America/Anchorage",
    "AZ": "America/Phoenix",
    "AR": "America/Chicago",
    "CA": "America/Los_Angeles",
    "CO": "America/Denver",
    "CT": "America/New_York",
    "DE": "America/New_York",
    "FL": "America/New_York",
    "GA": "America/New_York",
    "HI": "Pacific/Honolulu",
    "ID": "America/Boise",
    "IL": "America/Chicago",
    "IN": "America/Indiana/Indianapolis",
    "IA": "America/Chicago",
    "KS": "America/Chicago",
    "KY": "America/Kentucky/Louisville",
    "LA": "America/Chicago",
    "ME": "America/New_York",
    "MD": "America/New_York",
    "MA": "America/New_York",
    "MI": "America/Detroit",
    "MN": "America/Chicago",
    "MS": "America/Chicago",
    "MO": "America/Chicago",
    "MT": "America/Denver",
    "NE": "America/Chicago",
    "NV": "America/Los_Angeles",
    "NH": "America/New_York",
    "NJ": "America/New_York",
    "NM": "America/Denver",
    "NY": "America/New_York",
    "NC": "America/New_York",
    "ND": "America/Chicago",
    "OH": "America/New_York",
    "OK": "America/Chicago",
    "OR": "America/Los_Angeles",
    "PA": "America/New_York",
    "RI": "America/New_York",
    "SC": "America/New_York",
    "SD": "America/Chicago",
    "TN": "America/Chicago",
    "TX": "America/Chicago",
    "UT": "America/Denver",
    "VT": "America/New_York",
    "VA": "America/New_York",
    "WA": "America/Los_Angeles",
    "WV": "America/New_York",
    "WI": "America/Chicago",
    "WY": "America/Denver",
    "DC": "America/New_York",
    "PR": "America/Puerto_Rico",
    "VI": "America/St_Thomas",
    "GU": "Pacific/Guam",
    "AS": "Pacific/Pago_Pago",
    "MP": "Pacific/Saipan",
}


def _tz_for_state(state: str) -> Optional[str]:
    """Return the IANA timezone string for a US state abbreviation, or None if unknown."""
    if not state:
        return None
    return _STATE_TIMEZONES.get(state.strip().upper())


def _local_to_utc(local_dt_str: str, iana_tz: str) -> str:
    """
    Convert a naive local datetime string (YYYY-MM-DDTHH:MM:SS) to a UTC
    offset string suitable for the NexHealth API (e.g. 2026-06-01T16:00:00+00:00).
    """
    try:
        tz   = ZoneInfo(iana_tz)
        local_dt = datetime.fromisoformat(local_dt_str).replace(tzinfo=tz)
        utc_dt   = local_dt.astimezone(ZoneInfo("UTC"))
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except Exception as e:
        raise RuntimeError(
            f"Could not convert '{local_dt_str}' to UTC using timezone '{iana_tz}': {e}"
        )


def _utc_to_local(utc_dt_str: str, iana_tz: str) -> str:
    """
    Convert a UTC datetime string from the API to a local time display string.
    Returns a human-readable string like '1:00 PM MDT'.
    """
    try:
        tz = ZoneInfo(iana_tz)
        # Handle ISO strings with or without offset
        utc_str = utc_dt_str.replace("Z", "+00:00")
        if "+" not in utc_str[10:] and utc_str[-6] != "-":
            utc_str += "+00:00"
        utc_dt   = datetime.fromisoformat(utc_str)
        local_dt = utc_dt.astimezone(tz)
        return local_dt.strftime("%-I:%M %p %Z")
    except Exception:
        return utc_dt_str  # fall back to raw string if conversion fails


def _fetch_token() -> str:
    """Exchange the API key for a fresh bearer token from NexHealth."""
    api_key = os.environ.get("NEXHEALTH_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "NEXHEALTH_API_KEY environment variable is not set. "
            "Please set it before starting the MCP server."
        )
    url = f"{BASE_URL}/authenticates"
    headers = {
        "accept":      "application/vnd.Nexhealth+json;version=2",
        "Authorization": api_key,
        "User-Agent":  USER_AGENT,
    }
    req = urllib.request.Request(url, data=None, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"NexHealth authentication failed (HTTP {e.code}): {e.read().decode()}"
        )
    token = (
        data.get("data", {}).get("token")
        or data.get("token")
        or data.get("access_token")
    )
    if not token:
        raise RuntimeError(f"Could not find token in auth response: {data}")
    return token


def _get_token() -> str:
    """Return the cached bearer token, fetching a new one if not yet set."""
    global _bearer_token
    if not _bearer_token:
        _bearer_token = _fetch_token()
    return _bearer_token


def _refresh_token() -> str:
    """Force a new token fetch, clearing the cache first. Called on 401 responses."""
    global _bearer_token
    _bearer_token = None
    _bearer_token = _fetch_token()
    return _bearer_token


def _ensure_subdomain() -> str:
    """
    Return the cached subdomain, or raise a structured error telling Claude
    to call list_institutions() so the user can pick one.
    """
    global _subdomain

    # Fast path: already set this session
    if _subdomain:
        return _subdomain

    # Fast path: env var shortcut (single-subdomain deployments)
    env_sub = os.environ.get("NEXHEALTH_SUBDOMAIN", "").strip()
    if env_sub:
        _subdomain = env_sub
        return _subdomain

    # No subdomain yet — tell Claude what to do
    raise RuntimeError(
        "No institution selected for this session. "
        "Please call list_institutions() first so the user can choose one, "
        "then call select_institution(subdomain=...) with their choice."
    )


# ─── Structured API error helper ─────────────────────────────────────────────

_HTTP_EXPLANATIONS = {
    400: "The request was malformed. Check that all required fields are present and correctly formatted.",
    401: "Authentication failed. Your API key may be invalid or expired.",
    403: "You do not have permission to perform this action with your current API key.",
    404: "The requested resource was not found. Check that the ID is correct.",
    422: "The request was valid but could not be processed — check the 'detail' field for specifics.",
    429: "Too many requests. The NexHealth API rate limit has been hit — wait a moment and try again.",
    500: "NexHealth server error. This is on their side — try again in a moment.",
}


def _structured_error(code: int, detail, path: str = "") -> dict:
    """
    Return a structured error dict instead of raising. Tools return this as a
    JSON string so Claude can read it, explain it in plain English, and suggest
    what the developer should do next.
    """
    if isinstance(detail, dict):
        message = (
            detail.get("description")
            or detail.get("message")
            or detail.get("error")
            or str(detail)
        )
    else:
        message = str(detail)

    return {
        "error":       True,
        "code":        code,
        "path":        path,
        "message":     message,
        "explanation": _HTTP_EXPLANATIONS.get(
            code, f"Unexpected HTTP {code} from NexHealth API."
        ),
        "detail":      detail,
    }


def _raw_request(
    method: str,
    path: str,
    token: str,
    params: dict = None,
    body: dict = None,
    subdomain: str = None,
) -> dict:
    """Low-level HTTP request — does NOT auto-inject subdomain (used by institution tools)."""
    p = {}
    if subdomain:
        p["subdomain"] = subdomain
    if params:
        p.update(params)

    url = f"{BASE_URL}{path}"
    if p:
        url += "?" + urllib.parse.urlencode(p, doseq=True)

    headers = {
        "Authorization":   f"Bearer {token}",
        "Content-Type":    "application/json",
        "Accept":          "application/vnd.Nexhealth+json;version=2",
        "Nex-Api-Version": API_VERSION,
        "User-Agent":      USER_AGENT,
    }

    data = json.dumps(body).encode("utf-8") if body else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)

    def _do_request(tok: str) -> dict:
        hdrs = dict(headers)
        hdrs["Authorization"] = f"Bearer {tok}"
        r = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        with urllib.request.urlopen(r) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    try:
        return _do_request(token)
    except urllib.error.HTTPError as e:
        # On 401, refresh the token and retry exactly once
        if e.code == 401:
            try:
                new_tok = _refresh_token()
                return _do_request(new_tok)
            except urllib.error.HTTPError as retry_e:
                err = retry_e.read().decode("utf-8")
                try:
                    detail = json.loads(err)
                except Exception:
                    detail = err
                return _structured_error(retry_e.code, detail, path)
        err = e.read().decode("utf-8")
        try:
            detail = json.loads(err)
        except Exception:
            detail = err
        return _structured_error(e.code, detail, path)
    except urllib.error.URLError as e:
        return _structured_error(0, str(e.reason), path)


def _request(method: str, path: str, params: dict = None, body: dict = None) -> dict:
    """
    Make an authenticated, subdomain-scoped request to the NexHealth API.
    If the response is a structured error dict, raises ValueError so the calling
    tool can catch it and return the error as a JSON string to Claude.
    """
    token     = _get_token()
    subdomain = _ensure_subdomain()
    result    = _raw_request(method, path, token, params=params, body=body, subdomain=subdomain)
    if isinstance(result, dict) and result.get("error") is True:
        raise ValueError(json.dumps(result, indent=2))
    return result


# ─── MCP Server ───────────────────────────────────────────────────────────────

# Load system prompt from environment variable if set (populated by start script)
_system_prompt = os.environ.get("NEXHEALTH_SYSTEM_PROMPT", "").strip()
mcp = FastMCP("NexHealth", instructions=_system_prompt if _system_prompt else None)


def _tool(fn):
    """
    Decorator applied to all MCP tools. Catches ValueError (structured API error
    JSON raised by _request) and returns it as a string so Claude can read,
    interpret, and explain the error to the developer in plain English.
    Also catches unexpected exceptions and surfaces them as structured errors.
    """
    import functools
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            # Structured API error from _request — return as-is for Claude to explain
            return str(e)
        except RuntimeError as e:
            # Session/validation errors (no subdomain, no location, etc)
            return json.dumps({"error": True, "code": None, "message": str(e)}, indent=2)
        except Exception as e:
            return json.dumps({
                "error":       True,
                "code":        None,
                "message":     str(e),
                "explanation": "An unexpected error occurred in the MCP server.",
            }, indent=2)
    return wrapper



# ──────────────────────────────────────────────────────────────────────────────
# INSTITUTION / SESSION SETUP  (always call these first)
# ──────────────────────────────────────────────────────────────────────────────

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
    global _subdomain, _location_id
    _subdomain = subdomain.strip()
    _location_id = None  # reset location when institution changes

    token = _get_token()
    try:
        data = _raw_request("GET", "/locations", token, subdomain=_subdomain)
        institutions = data.get("data", [])
        locations = []
        for inst in institutions:
            locations.extend(inst.get("locations", []))

        loc_list = [
            {
                "id":    loc.get("id"),
                "name":  loc.get("name"),
                "city":  loc.get("city"),
                "state": loc.get("state"),
            }
            for loc in locations
        ]
        return json.dumps({
            "message":   f"Institution '{_subdomain}' selected and active for this session.",
            "locations": loc_list,
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "message": f"Institution '{_subdomain}' selected. (Could not pre-fetch locations: {e})",
        }, indent=2)


@mcp.tool()
@_tool
def current_session() -> str:
    """
    Show the current session state: which institution/subdomain and location
    are active, and whether authentication is established.
    Useful for confirming setup before making other calls.
    """
    env_sub = os.environ.get("NEXHEALTH_SUBDOMAIN", "").strip()
    return json.dumps({
        "authenticated":      _bearer_token is not None,
        "active_subdomain":   _subdomain or env_sub or "(not set — call list_institutions first)",
        "subdomain_source":   (
            "environment variable" if (not _subdomain and env_sub)
            else ("select_institution()" if _subdomain else "none")
        ),
        "active_location_id": _location_id or "(not set — call select_location after listing locations)",
        "active_timezone":    _location_tz or "(not set — select a location first)",
        "active_state":       _location_state or "(not set)",
    }, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# LOCATIONS
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_location() -> int:
    """Return the cached location_id or raise a clear error telling Claude to call select_location()."""
    if _location_id:
        return _location_id
    raise RuntimeError(
        "No location selected for this session. "
        "Call list_locations() and then select_location(location_id=...) before searching patients or booking."
    )


@mcp.tool()
@_tool
def list_locations() -> str:
    """
    List all locations (practice/clinic/office) for this institution.
    Returns a list with each location's id, name, city, and state.
    Most other tools require a location_id — call this first to discover them.
    """
    data = _request("GET", "/locations")
    institutions = data.get("data", [])
    locations = []
    for inst in institutions:
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

    Returns a confirmation of the selected location.
    """
    global _location_id, _location_tz, _location_state
    # Verify the location actually exists under the current subdomain
    data = _request("GET", "/locations")
    institutions = data.get("data", [])
    all_locations = []
    for inst in institutions:
        all_locations.extend(inst.get("locations", []))

    match = next((loc for loc in all_locations if loc.get("id") == location_id), None)
    if not match:
        valid_ids = [loc.get("id") for loc in all_locations]
        raise RuntimeError(
            f"Location ID {location_id} not found in this institution. "
            f"Valid location IDs are: {valid_ids}. Call list_locations() to see options."
        )

    _location_id    = location_id
    _location_state = match.get("state", "").strip().upper() if match.get("state") else None
    _location_tz    = _tz_for_state(_location_state) if _location_state else None

    return json.dumps({
        "message":   "Location locked for this session.",
        "location_id": _location_id,
        "name":      match.get("name"),
        "city":      match.get("city"),
        "state":     _location_state,
        "timezone":  _location_tz or "Unknown (timezone could not be determined from state)",
    }, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# PATIENTS
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
@_tool
def search_patients(
    name: str,
    per_page: int = 10,
) -> str:
    """
    Search for patients by name, locked to the session location set by select_location().

    Every patient returned is guaranteed to belong to the active session location.
    The location_id is embedded in each result so it can be passed directly and
    safely to book_appointment without risk of location mismatch.

    Args:
        name:     First or last name fragment to search for.
        per_page: Max results to return (default 10, max 300).

    Returns a list of matching patients. Each record includes location_id (always
    the session location) to be used as-is when booking.
    """
    location_id = _ensure_location()

    data = _request("GET", "/patients", params={
        "location_id": location_id,
        "name":        name,
        "per_page":    per_page,
        "non_patient": "false",
        "inactive":    "false",
    })

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("patients", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":            p.get("id"),
            "first_name":    p.get("first_name"),
            "last_name":     p.get("last_name"),
            "date_of_birth": p.get("date_of_birth"),
            "email":         p.get("email"),
            "phone":         p.get("phone_number") or p.get("cell_phone_number"),
            "location_id":   location_id,   # always the session-locked location
        }
        for p in raw
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def get_patient(patient_id: int) -> str:
    """
    Retrieve a single patient by their NexHealth patient ID.

    Args:
        patient_id: The NexHealth patient ID.
    """
    location_id = _ensure_location()
    data = _request("GET", f"/patients/{patient_id}", params={"location_id": location_id})
    return json.dumps(data.get("data", data), indent=2)



# ──────────────────────────────────────────────────────────────────────────────
# CREATE PATIENT
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
@_tool
def create_patient(
    first_name: str,
    last_name: str,
    email: str,
    date_of_birth: str,
    phone_number: str,
    provider_id: int,
    gender: str = None,
    cell_phone_number: str = None,
    home_phone_number: str = None,
    address_line_1: str = None,
    address_line_2: str = None,
    city: str = None,
    state: str = None,
    zip_code: str = None,
) -> str:
    """
    Create a new patient at the session location.

    The patient is always created at the active session location (set by
    select_location). Required fields are first_name, last_name, email,
    date_of_birth, phone_number, and provider_id (the intake provider).

    Args:
        first_name:        Patient first name (required).
        last_name:         Patient last name (required).
        email:             Patient email address (required).
        date_of_birth:     Date of birth in YYYY-MM-DD format (required).
        phone_number:      Primary phone number (required).
        provider_id:       ID of the provider to intake this patient under (required).
                           Use list_providers() to find valid provider IDs.
        gender:            "Male", "Female", or "Other" (defaults to Female if omitted).
        cell_phone_number: Cell phone number (optional).
        home_phone_number: Home phone number (optional).
        address_line_1:    Street address line 1 (optional).
        address_line_2:    Street address line 2 (optional).
        city:              City (optional).
        state:             State (optional).
        zip_code:          Zip code (optional).

    Returns the full API response for the newly created patient including their new patient ID.
    """
    location_id = _ensure_location()

    bio: dict = {
        "date_of_birth": date_of_birth,
        "phone_number":  phone_number,
    }
    if gender:
        bio["gender"] = gender
    if cell_phone_number:
        bio["cell_phone_number"] = cell_phone_number
    if home_phone_number:
        bio["home_phone_number"] = home_phone_number
    if address_line_1:
        bio["address_line_1"] = address_line_1
    if address_line_2:
        bio["address_line_2"] = address_line_2
    if city:
        bio["city"] = city
    if state:
        bio["state"] = state
    if zip_code:
        bio["zip_code"] = zip_code

    body = {
        "provider": {"provider_id": provider_id},
        "patient": {
            "first_name": first_name,
            "last_name":  last_name,
            "email":      email,
            "bio":        bio,
        },
    }

    data = _request(
        "POST",
        "/patients",
        params={"location_id": location_id},
        body=body,
    )
    return json.dumps(data, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# PROVIDERS
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
@_tool
def list_providers(location_id: int) -> str:
    """
    List all active providers at a given location.

    Args:
        location_id: The location to list providers for.

    Returns a list with each provider's id, first_name, last_name, and title.
    """
    data = _request("GET", "/providers", params={
        "location_id": location_id,
        "active":      "true",
    })

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


# ──────────────────────────────────────────────────────────────────────────────
# APPOINTMENT TYPES
# ──────────────────────────────────────────────────────────────────────────────

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
    data = _request("GET", "/appointment_types", params={
        "location_id": location_id,
    })

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
    automatically written to the PMS/EHR.

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

    data = _check(_request(
        "GET",
        f"/locations/{location_id}/appointment_descriptors",
        params=params if params else None,
    ))

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

    data = _check(_request(
        "PATCH",
        f"/appointment_types/{appointment_type_id}",
        body={"appointment_type": appt_type},
    ))
    return json.dumps(data, indent=2)

# ──────────────────────────────────────────────────────────────────────────────
# AVAILABLE SLOTS
# ──────────────────────────────────────────────────────────────────────────────

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
                                     Defaults to today.
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
        start_date = datetime.now().strftime("%Y-%m-%d")

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

    grouped = {}
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

            if date not in grouped:
                grouped[date] = []
            raw_time     = slot.get("time", "")
            raw_end_time = slot.get("end_time", "")
            local_disp   = _utc_to_local(raw_time, _location_tz) if _location_tz and raw_time else disp
            local_end    = _utc_to_local(raw_end_time, _location_tz) if _location_tz and raw_end_time else raw_end_time

            grouped[date].append({
                "time":              raw_time,          # UTC — pass this directly to book_appointment
                "end_time":          raw_end_time,      # UTC
                "display_time":      local_disp,        # local time for display
                "display_end_time":  local_end,         # local time for display
                "timezone":          _location_tz or "UTC",
                "operatory_id":      slot.get("operatory_id"),
                "location_id":       entry.get("lid"),
                "provider_id":       entry.get("pid"),
            })

    return json.dumps(grouped, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# BOOK APPOINTMENT
# ──────────────────────────────────────────────────────────────────────────────

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
    The session location (set by select_location) is always used and enforced.

    Args:
        patient_id:          The NexHealth patient ID (must belong to the session location).
        provider_id:         The NexHealth provider ID.
        start_time:          ISO 8601 start datetime (e.g. "2025-06-01T09:00:00").
                             Get this from the 'time' field in get_available_slots.
        operatory_id:        The operatory/room ID (required). Get this from the
                             'operatory_id' field returned by get_available_slots.
        location_id:         Optional — if provided, must match the session location or the
                             booking is rejected. Useful as an explicit double-check.
        appointment_type_id: (Optional) ID of the appointment type.
        note:                (Optional) A note to attach to the appointment.
        notify_patient:      Whether to send a NexHealth confirmation notification (default False).

    Returns the full NexHealth API response including the new appointment ID.
    """
    # ── Location guard ────────────────────────────────────────────────────────
    # Always use the session-locked location, regardless of what was passed in.
    # If a location_id argument was supplied but differs from the session location,
    # reject immediately — never silently override.
    session_location = _ensure_location()
    if location_id != session_location:
        raise RuntimeError(
            f"Location mismatch: you passed location_id={location_id} but the active "
            f"session location is {session_location}. All bookings must use the session "
            f"location. Call select_location() to change it explicitly."
        )

    # ── Timezone: convert local time to UTC if needed ────────────────────────
    # If start_time looks like a naive local datetime (no offset) and we have
    # a session timezone, convert it to UTC before sending to the API.
    # If start_time already contains a UTC offset (e.g. from get_available_slots),
    # pass it through unchanged.
    if _location_tz and "+" not in start_time and start_time[-1] != "Z":
        start_time = _local_to_utc(start_time, _location_tz)

    # ── Create the appointment ─────────────────────────────────────────────────
    appt_body: dict = {
        "patient_id":  patient_id,
        "provider_id": provider_id,
        "start_time":  start_time,
        "location_id": session_location,
    }
    if operatory_id:
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


# ──────────────────────────────────────────────────────────────────────────────
# VIEW / MANAGE APPOINTMENTS
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
@_tool
def get_appointment(appointment_id: int) -> str:
    """
    Retrieve a single appointment by its NexHealth appointment ID.

    Args:
        appointment_id: The NexHealth appointment ID to look up.
    """
    data = _request(
        "GET",
        f"/appointments/{appointment_id}",
        params={"include[]": ["patient", "operatory", "appointment_type"]},
    )
    return json.dumps(data.get("data", data), indent=2)


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
        next_page:   Cursor to fetch the NEXT page. Pass the value of
                     navigation.end_cursor from the previous response.
                     Use when the user asks for "next page" or "more results".
        prev_page:   Cursor to fetch the PREVIOUS page. Pass the value of
                     navigation.start_cursor from the previous response.
                     Use when the user asks to "go back" or "previous page".

    Returns appointments plus a navigation block. Always show the user:
      - How many results were returned
      - Whether there are more pages (has_next_page / has_previous_page)
      - A prompt like "Want me to fetch the next page?" when has_next_page is true.
    Do NOT call this tool again until the user explicitly asks to paginate.
    """
    location_id = _ensure_location()

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

    # Cursor-based pagination — only one direction at a time
    if next_page and prev_page:
        raise RuntimeError("Pass either next_page or prev_page, not both.")
    if next_page:
        params["end_cursor"]   = next_page
    elif prev_page:
        params["start_cursor"] = prev_page

    data      = _request("GET", "/appointments", params=params)
    appts     = data.get("data", [])
    page_info = data.get("page_info", {})

    # Build a navigation block Claude can use to drive the next call
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
        # Convert local checkin time to UTC if no offset present
        if _location_tz and "+" not in checkin_at and checkin_at[-1] != "Z":
            checkin_at = _local_to_utc(checkin_at, _location_tz)
        appt["checkin_at"] = checkin_at

    if not appt:
        raise RuntimeError(
            "No fields to patch. Provide at least one of: confirmed, cancelled, checkin_at."
        )

    data = _request(
        "PATCH",
        f"/appointments/{appointment_id}",
        body={"appt": appt},
    )
    return json.dumps(data, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# OPERATORIES
# ──────────────────────────────────────────────────────────────────────────────

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



# ──────────────────────────────────────────────────────────────────────────────
# WORKING HOURS
# ──────────────────────────────────────────────────────────────────────────────

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

    # ── Validate exactly one scheduling mode is provided ──────────────────────
    using_days       = bool(days)
    using_date       = bool(specific_date)
    using_recurrence = any([custom_recurrence_num, custom_recurrence_unit, custom_recurrence_ref])

    modes_set = sum([using_days, using_date, using_recurrence])
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

    # ── Validate days if provided ─────────────────────────────────────────────
    if using_days:
        valid_days = {"Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"}
        invalid = [d for d in days if d not in valid_days]
        if invalid:
            raise RuntimeError(
                f"Invalid day(s): {invalid}. "
                f"Must be one of: {sorted(valid_days)}"
            )

    # ── Validate custom_recurrence fields are all present together ────────────
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

    # ── Build payload ─────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────────
# DEVELOPER ONBOARDING
# ──────────────────────────────────────────────────────────────────────────────

# ─── Onboarding content — loaded from markdown files at startup ──────────────
# To update any section, edit the corresponding .md file in the onboarding/
# directory. No Python code changes required.

def _load_onboarding(directory: str) -> dict:
    """Load all .md files in directory as onboarding sections keyed by filename stem."""
    sections = {}
    if not os.path.isdir(directory):
        return sections
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".md"):
            key = filename[:-3]  # strip .md
            try:
                with open(os.path.join(directory, filename), encoding="utf-8") as f:
                    sections[key] = f.read().strip()
            except Exception as e:
                sections[key] = f"[Could not load {filename}: {e}]"
    return sections


# Resolve onboarding directory relative to this file so it works regardless
# of the working directory the server is launched from.
_ONBOARDING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onboarding")
_ONBOARDING_SECTIONS = _load_onboarding(_ONBOARDING_DIR)

_SANDBOX_SECTIONS    = ["sandbox_overview", "dev_portal", "api_key", "sandbox_first_call"]
_PRODUCTION_SECTIONS = ["production_overview", "production_institution",
                        "production_datasource", "production_api_key", "production_first_call"]

def _build_guide(section_keys: list) -> str:
    parts = []
    for key in section_keys:
        parts.append(_ONBOARDING_SECTIONS.get(key, f"[Section '{key}' not found — check onboarding/ directory]"))
    return "\n\n---\n\n".join(parts)

_SANDBOX_GUIDE    = "## NexHealth Sandbox Setup — Full Guide\n\n"    + _build_guide(_SANDBOX_SECTIONS)
_PRODUCTION_GUIDE = "## NexHealth Production Setup — Full Guide\n\n" + _build_guide(_PRODUCTION_SECTIONS)


@mcp.tool()
@_tool
def get_started(section: str = None, mode: str = None) -> str:
    """
    Developer onboarding guide for the NexHealth MCP server.

    Supports both sandbox and production setup flows. Always ask the developer
    which mode they want before calling this tool.

    Call with no arguments to get a full guide for both modes.
    Call with mode="sandbox" or mode="production" for the full guide for that mode.
    Call with a specific section name to get guidance on that step only.

    Args:
        mode:    (Optional) "sandbox" or "production". Returns the full guide
                 for that mode when no section is specified.
        section: (Optional) A specific section to return. Sandbox sections:
                   "sandbox_overview"      — High-level summary of sandbox steps
                   "dev_portal"            — Create developer account and sandbox API key
                   "vm_setup"              — Mac users: install Parallels Windows VM
                   "open_dental"           — Install Open Dental demo EHR
                   "synchronizer"          — Install the NexHealth synchronizer
                   "api_key"               — Store API key securely in Mac keychain
                   "sandbox_first_call"    — Make first sandbox API call end-to-end
                 Production sections:
                   "production_overview"      — High-level summary of production steps
                   "production_institution"   — Create a production institution
                   "production_datasource"    — Connect Open Dental as a datasource
                   "production_api_key"       — Generate and store production API key
                   "production_first_call"    — Make first production API call

    If neither argument is provided, returns an overview of both modes and asks
    the developer which they want to proceed with.
    """
    if section:
        section = section.strip().lower()
        if section not in _ONBOARDING_SECTIONS:
            valid = ", ".join(f'"{s}"' for s in _ONBOARDING_SECTIONS)
            return (
                f"Section '{section}' not found. "
                f"Available sections: {valid}."
            )
        return _ONBOARDING_SECTIONS[section]

    if mode:
        mode = mode.strip().lower()
        if mode == "sandbox":
            return _SANDBOX_GUIDE
        if mode == "production":
            return _PRODUCTION_GUIDE
        return (
            f"Mode '{mode}' not recognised. "
            f"Use mode='sandbox' or mode='production'."
        )

    # No arguments — return a prompt asking the developer which they want
    return """
## NexHealth Developer Setup

Welcome! Before we get started, are you setting up a sandbox (test) environment
or a production environment?

  - Sandbox    — Uses test data pre-populated by NexHealth. Recommended for
                 first-time setup and integration testing. No real patient data.

  - Production — Connects to a live Open Dental instance and real practice data.
                 Requires a production institution to be configured first.

Please tell me which you'd like to set up and I'll walk you through it step by step.
"""

# ──────────────────────────────────────────────────────────────────────────────
# WORKFLOW GUIDANCE
# ──────────────────────────────────────────────────────────────────────────────

# Workflow files live in a workflows/ directory next to the server file.
# Each file is a markdown guide telling Claude how to execute a specific task
# correctly — what order to call tools, what to confirm with the user,
# and how to handle errors. Add new .md files to extend coverage.

_WORKFLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")
_WORKFLOWS    = _load_onboarding(_WORKFLOW_DIR)  # reuse same loader as onboarding

# Map of natural-language aliases → workflow file keys
# Lets Claude match "book appointment", "booking", "schedule" etc to the right file
_WORKFLOW_ALIASES = {
    # book appointment
    "book":               "book_appointment",
    "booking":            "book_appointment",
    "schedule":           "book_appointment",
    "book appointment":   "book_appointment",
    "book_appointment":   "book_appointment",
    # create patient
    "create patient":     "create_patient",
    "create_patient":     "create_patient",
    "new patient":        "create_patient",
    "add patient":        "create_patient",
    # working hours
    "working hour":       "create_working_hour",
    "working hours":      "create_working_hour",
    "create_working_hour":"create_working_hour",
    "availability":       "create_working_hour",
    # patch / update appointment
    "patch":              "patch_appointment",
    "patch appointment":  "patch_appointment",
    "patch_appointment":  "patch_appointment",
    "confirm":            "patch_appointment",
    "cancel":             "patch_appointment",
    "reschedule":         "patch_appointment",
    "check in":           "patch_appointment",
    "checkin":            "patch_appointment",
    # session setup
    "session":            "session_setup",
    "session setup":      "session_setup",
    "session_setup":      "session_setup",
    "setup":              "session_setup",
    "get started":        "session_setup",
    # troubleshooting
    "troubleshoot":       "troubleshoot",
    "error":              "troubleshoot",
    "debug":              "troubleshoot",
    "help":               "troubleshoot",
}


@mcp.tool()
@_tool
def get_workflow(task: str = None) -> str:
    """
    Return step-by-step workflow guidance for a specific task.
    Claude should call this proactively before executing any multi-step operation
    to ensure tools are called in the correct order with the right validations.

    Call with no arguments to see all available workflows.
    Call with a task name or natural-language description to get that workflow.

    Args:
        task: The task or workflow to retrieve. Accepts natural language or exact names.
              Examples: "book appointment", "create patient", "working hours",
              "patch", "cancel", "reschedule", "check in", "session setup",
              "troubleshoot", "error"

    Available workflows:
        "book_appointment"    — Full booking flow: patient → provider → slots → confirm → book
        "create_patient"      — Create a new patient with duplicate checking
        "create_working_hour" — Set up provider availability (recurring, one-off, or custom)
        "patch_appointment"   — Confirm, cancel, check in, or reschedule an appointment
        "session_setup"       — Establish institution and location at session start
        "troubleshoot"        — Error code reference and debugging steps

    When to call this tool:
        - At the start of any booking, creation, or update operation
        - When an error is returned and you need to diagnose it
        - When the user asks "how do I..." for any supported task
        - When you are unsure of the correct tool sequence for a task
    """
    if not _WORKFLOWS:
        return json.dumps({
            "error":   True,
            "message": f"Workflow directory not found at {_WORKFLOW_DIR}. "
                       f"Ensure the workflows/ folder exists next to the server file."
        }, indent=2)

    if not task:
        available = sorted(_WORKFLOWS.keys())
        return json.dumps({
            "message":            "Available workflows — call get_workflow(task='...') for any of these:",
            "available_workflows": available,
            "tip":                "You can also use natural language e.g. get_workflow('book appointment') or get_workflow('troubleshoot')",
        }, indent=2)

    # Resolve alias or direct key
    key = _WORKFLOW_ALIASES.get(task.strip().lower()) or task.strip().lower()

    if key not in _WORKFLOWS:
        # Fuzzy fallback — check if task is a substring of any key
        matches = [k for k in _WORKFLOWS if task.lower() in k or k in task.lower()]
        if len(matches) == 1:
            key = matches[0]
        elif len(matches) > 1:
            return json.dumps({
                "message":  f"Multiple workflows match '{task}'. Please be more specific:",
                "matches":  matches,
            }, indent=2)
        else:
            return json.dumps({
                "error":     True,
                "message":   f"No workflow found for '{task}'.",
                "available": sorted(_WORKFLOWS.keys()),
            }, indent=2)

    return _WORKFLOWS[key]


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexHealth MCP Server")
    parser.add_argument(
        "--sse", action="store_true",
        help="Run with SSE (HTTP) transport instead of stdio"
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Port for SSE transport (default: 8080)"
    )
    args = parser.parse_args()

    if args.sse:
        print(f"Starting NexHealth MCP server on http://0.0.0.0:{args.port}/sse", flush=True)
        mcp.run(transport="sse")
    else:
        # stdio — standard for Claude Desktop and local MCP clients
        mcp.run(transport="stdio")
