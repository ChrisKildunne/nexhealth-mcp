"""
Low-level HTTP helpers for the NexHealth API.

_raw_request  — bare HTTP call, no subdomain injection, used by institution tools
_request      — authenticated + subdomain-scoped call used by all other tools
"""
import json
import urllib.request
import urllib.parse
import urllib.error

import nexhealth.session as _session
from nexhealth.config import BASE_URL, API_VERSION, USER_AGENT
from nexhealth.auth import _get_token, _refresh_token

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
    Build a structured error dict. Tools return this as a JSON string so Claude
    can read, interpret, and explain the error to the developer in plain English.
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
        "explanation": _HTTP_EXPLANATIONS.get(code, f"Unexpected HTTP {code} from NexHealth API."),
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
    """
    Low-level HTTP call. Does NOT auto-inject subdomain — callers must pass it
    explicitly. Used by institution tools that run before a subdomain is selected.
    Never raises; returns a structured error dict on failure.
    """
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

    def _do(tok: str) -> dict:
        hdrs = dict(headers)
        hdrs["Authorization"] = f"Bearer {tok}"
        r = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        with urllib.request.urlopen(r) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    try:
        return _do(token)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # Refresh token and retry exactly once
            try:
                return _do(_refresh_token())
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
    Authenticated, subdomain-scoped API call.
    Raises ValueError (with JSON string payload) on API errors so the @_tool
    decorator can catch it and return it as a string to Claude.
    """
    token     = _get_token()
    subdomain = _session._ensure_subdomain()
    result    = _raw_request(method, path, token, params=params, body=body, subdomain=subdomain)
    if isinstance(result, dict) and result.get("error") is True:
        raise ValueError(json.dumps(result, indent=2))
    return result
