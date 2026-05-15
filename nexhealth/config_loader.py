"""
Loads config.yaml from the project root at import time.

Priority for each setting (highest → lowest):
  1. Environment variable  — always wins, good for CI and secrets providers
  2. config.yaml value     — the user-friendly layer for local installs
  3. Hardcoded default     — safe fallback, works out of the box

The API key is never read from config.yaml — use the system keychain
(or set NEXHEALTH_API_KEY as an env var from your secrets provider).
"""
import os
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_PATH  = _PROJECT_ROOT / "config.yaml"

_raw: dict = {}

if _CONFIG_PATH.exists():
    try:
        import yaml
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _raw = yaml.safe_load(f) or {}
    except Exception as e:
        import warnings
        warnings.warn(f"Could not load config.yaml: {e}. Using defaults.")


def _get(section: str, key: str, default: Any = "") -> Any:
    """Return env var if set, else config.yaml value, else default."""
    env_key = f"NEXHEALTH_{key.upper()}"
    env_val = os.environ.get(env_key, "").strip()
    if env_val:
        return env_val
    return (_raw.get(section) or {}).get(key, default) or default


# ── Resolved config values ────────────────────────────────────────────────────

# NexHealth API subdomain (skips list_institutions selection when set)
SUBDOMAIN: str = _get("nexhealth", "subdomain", "")

# IANA timezone override for split-timezone states (e.g. "America/New_York")
TIMEZONE_OVERRIDE: str = _get("server", "timezone_override", "")

# SSE mode bind address — 127.0.0.1 restricts to local connections only
SSE_HOST: str = _get("server", "sse_host", "127.0.0.1")

# SSE mode port
SSE_PORT: int = int(_get("server", "sse_port", 8080))
