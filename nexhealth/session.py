"""
Session-level state for the running MCP server process.

Each variable here is set during the institution/location setup flow and
then read (never written) by most tool modules. Writes go through the
tool functions in institutions.py and locations.py which reference this
module directly (import nexhealth.session as _session).
"""
from typing import Optional
from nexhealth import config_loader as _cfg

_bearer_token:   Optional[str] = None
_subdomain:      Optional[str] = None   # set by select_institution, config.yaml, or env var
_location_id:    Optional[int] = None   # set by select_location; enforced on patient + booking calls
_location_tz:    Optional[str] = None   # IANA timezone string, e.g. "America/Denver"
_location_state: Optional[str] = None   # US state abbreviation, e.g. "CO"


def _ensure_subdomain() -> str:
    """Return the active subdomain or raise, telling Claude to call list_institutions first."""
    global _subdomain
    if _subdomain:
        return _subdomain
    if _cfg.SUBDOMAIN:
        _subdomain = _cfg.SUBDOMAIN
        return _subdomain
    raise RuntimeError(
        "No institution selected for this session. "
        "Please call list_institutions() first so the user can choose one, "
        "then call select_institution(subdomain=...) with their choice."
    )


def _ensure_location() -> int:
    """Return the active location_id or raise, telling Claude to call select_location first."""
    if _location_id is not None:
        return _location_id
    raise RuntimeError(
        "No location selected for this session. "
        "Call list_locations() and then select_location(location_id=...) "
        "before searching patients or booking appointments."
    )
