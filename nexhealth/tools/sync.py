import json

from nexhealth.app import mcp
from nexhealth.auth import _get_token
from nexhealth.http_client import _raw_request
from nexhealth.session import _ensure_subdomain
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def get_sync_status(
    location_ids: list = None,
    read_status: str = None,
    write_status: str = None,
) -> str:
    """
    Get the sync status (read/write) for all data sources connected to the
    active session institution. Works for both sandbox and production environments.

    Use this any time a developer asks about sync status, why data isn't
    appearing in the EHR, or whether their integration is healthy. Always
    call this before walking a developer through sync troubleshooting steps —
    it immediately shows which data sources are healthy (green) vs
    disconnected (red).

    Status values:
      green — the connection is active and syncing correctly
      red   — the connection has been severed; NexHealth cannot read or write

    If read_status and write_status are both red for an on-premises EHR
    (type="onprem", e.g. Open Dental, Dentrix, Eaglesoft), the most likely
    causes are:
      1. The server hosting the EHR is offline
      2. The EHR database is not running
      3. The NexHealth Synchronizer service has stopped
         (check Windows Services → NexHealth Synchronizer)

    For cloud EHRs (Denticon, athenahealth, eClinicalWorks) a red status
    is typically a credential or configuration issue — not a local service.

    Args:
        location_ids:  (Optional) List of location IDs to filter results.
                       If omitted, returns sync status for all locations
                       in the active institution.
        read_status:   (Optional) Filter by read status. "green" or "red".
        write_status:  (Optional) Filter by write status. "green" or "red".

    Returns each data source with its name, connected EHR, read/write status,
    last status timestamps, associated locations, and a plain-English summary.
    """
    subdomain = _ensure_subdomain()

    if read_status and read_status not in ("green", "red"):
        raise RuntimeError(
            f"read_status must be 'green' or 'red'. Got: '{read_status}'"
        )
    if write_status and write_status not in ("green", "red"):
        raise RuntimeError(
            f"write_status must be 'green' or 'red'. Got: '{write_status}'"
        )

    params: dict = {"subdomain": subdomain}
    if location_ids:
        params["location_ids[]"] = location_ids
    if read_status:
        params["read_status"] = read_status
    if write_status:
        params["write_status"] = write_status

    token = _get_token()
    data  = _raw_request("GET", "/sync_status", token, params=params)

    raw = data.get("data", [])
    if not isinstance(raw, list):
        raw = []

    result = []
    for source in raw:
        emr     = source.get("emr", {})
        read_s  = source.get("read_status",  "unknown")
        write_s = source.get("write_status", "unknown")
        is_onprem = emr.get("type") == "onprem"

        entry = {
            "sync_source_name": source.get("sync_source_name"),
            "emr":              emr.get("display_name"),
            "emr_type":         emr.get("type"),
            "read_status":      read_s,
            "read_status_at":   source.get("read_status_at"),
            "write_status":     write_s,
            "write_status_at":  source.get("write_status_at"),
            "locations": [
                {
                    "id":    loc.get("id"),
                    "name":  loc.get("name"),
                    "city":  loc.get("city"),
                    "state": loc.get("state"),
                }
                for loc in source.get("locations", [])
            ],
        }

        # Plain-English status summary for Claude to surface to the developer
        if read_s == "green" and write_s == "green":
            entry["_status_summary"] = "Healthy — reads and writes are both active."
        elif read_s == "red" and write_s == "red":
            msg = "Disconnected — both reads and writes are down."
            if is_onprem:
                msg += (
                    " For on-premises EHRs, check: (1) Is the server online? "
                    "(2) Is the database running? "
                    "(3) Is the NexHealth Synchronizer service running? "
                    "(Windows: Services → NexHealth Synchronizer)"
                )
            else:
                msg += (
                    " For cloud EHRs this is typically a credential or "
                    "configuration issue. Contact developers@nexhealth.com "
                    "with the sync_source_name from this response."
                )
            entry["_status_summary"] = msg
        elif read_s == "red":
            entry["_status_summary"] = (
                "Reads are down — NexHealth cannot read from the EHR. "
                "Check the synchronizer service and database connection."
            )
        elif write_s == "red":
            entry["_status_summary"] = (
                "Writes are down — NexHealth can read but cannot write to the EHR. "
                "Check the synchronizer service and database permissions."
            )

        result.append(entry)

    return json.dumps({
        "sync_sources": result,
        "count":        len(result),
    }, indent=2)
