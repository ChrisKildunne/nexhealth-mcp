"""Token management: fetch, cache, and auto-refresh the NexHealth bearer token."""
import os
import json
import urllib.request
import urllib.error

import nexhealth.session as _session
from nexhealth.config import BASE_URL, USER_AGENT


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
        "accept":        "application/vnd.Nexhealth+json;version=2",
        "Authorization": api_key,
        "User-Agent":    USER_AGENT,
    }
    req = urllib.request.Request(url, data=None, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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
    if not _session._bearer_token:
        _session._bearer_token = _fetch_token()
    return _session._bearer_token


def _refresh_token() -> str:
    """Force a new token fetch. Called automatically on 401 responses."""
    _session._bearer_token = None
    _session._bearer_token = _fetch_token()
    return _session._bearer_token
