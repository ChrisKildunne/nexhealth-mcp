"""Token management: fetch, cache, and auto-refresh the NexHealth bearer token."""
import os
import json
import urllib.request
import urllib.error

import nexhealth.session as _session
from nexhealth.config import BASE_URL, USER_AGENT

# These match what the macOS `security` CLI uses:
#   security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "..."
#   security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w
#
# Using the same service/username means `keyring` and the `security` CLI
# read from and write to the exact same keychain entry.
_KEYCHAIN_SERVICE  = "NEXHEALTH_API_KEY"
_KEYCHAIN_USERNAME = os.environ.get("USER", "")


def _get_api_key() -> str:
    """
    Resolve the NexHealth API key using the following priority:
      1. NEXHEALTH_API_KEY environment variable  — wins always; use this for
         CI, Docker, or to inject a key from a network secrets provider
         (HashiCorp Vault, AWS Secrets Manager, etc.).
      2. System keychain  — macOS Keychain, Windows Credential Manager
         (DPAPI/TPM-backed), or Linux Secret Service / GNOME Keyring.

    To store the key in the system keychain, run:
        nexhealth-mcp setup
    Or via the macOS security CLI directly:
        security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_key"
    """
    # 1. Environment variable (highest priority)
    env_key = os.environ.get("NEXHEALTH_API_KEY", "").strip()
    if env_key:
        return env_key

    # 2. System keychain via keyring
    try:
        import keyring
        stored = keyring.get_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USERNAME)
        if stored:
            return stored.strip()
    except Exception:
        pass  # keyring unavailable or backend error — fall through to clear error

    raise RuntimeError(
        "NexHealth API key not found.\n\n"
        "Store it in your system keychain (recommended):\n"
        "    nexhealth-mcp setup\n\n"
        "Or via the macOS security CLI:\n"
        "    security add-generic-password -a \"$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_key\"\n\n"
        "Or set the environment variable:\n"
        "    export NEXHEALTH_API_KEY=your_key_here\n"
    )


def _fetch_token() -> str:
    """Exchange the API key for a fresh bearer token from NexHealth."""
    api_key = _get_api_key()
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
