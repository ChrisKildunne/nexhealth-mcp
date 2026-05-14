"""Timezone conversion helpers for the NexHealth MCP server."""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from nexhealth.config import CITY_TIMEZONE_OVERRIDES, SPLIT_TIMEZONE_STATES, STATE_TIMEZONES


def _tz_for_location(city: Optional[str], state: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve the best available IANA timezone for a location, and return a
    warning string if the state is split-timezone and the city wasn't recognised.

    Returns (iana_tz, warning_or_None).
    """
    city_key = (city or "").strip().lower()
    state_key = (state or "").strip().upper()

    # 1. City-level override — most specific, handles split-timezone states
    if city_key and city_key in CITY_TIMEZONE_OVERRIDES:
        return CITY_TIMEZONE_OVERRIDES[city_key], None

    # 2. State default
    state_tz = STATE_TIMEZONES.get(state_key)

    # 3. Warn when the state is split-timezone and the city wasn't in our map
    warning = None
    if state_key in SPLIT_TIMEZONE_STATES and city_key not in CITY_TIMEZONE_OVERRIDES:
        warning = (
            f"'{city or state}' is in a split-timezone state. "
            f"{SPLIT_TIMEZONE_STATES[state_key]}"
        )

    return state_tz, warning


def _tz_for_state(state: str) -> Optional[str]:
    """Return the IANA timezone string for a US state abbreviation, or None if unknown."""
    if not state:
        return None
    return STATE_TIMEZONES.get(state.strip().upper())


def _local_to_utc(local_dt_str: str, iana_tz: str) -> str:
    """
    Convert a naive local datetime string (YYYY-MM-DDTHH:MM:SS) to a UTC offset
    string suitable for the NexHealth API (e.g. 2026-06-01T16:00:00+00:00).
    """
    try:
        tz       = ZoneInfo(iana_tz)
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
    Falls back to the raw input string on any parse error.
    """
    try:
        tz      = ZoneInfo(iana_tz)
        utc_str = utc_dt_str.replace("Z", "+00:00")
        # Append offset if the string has no timezone info after position 10
        if "+" not in utc_str[10:] and utc_str[-6] != "-":
            utc_str += "+00:00"
        utc_dt   = datetime.fromisoformat(utc_str)
        local_dt = utc_dt.astimezone(tz)
        return local_dt.strftime("%-I:%M %p %Z")
    except Exception:
        return utc_dt_str
