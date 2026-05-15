"""Error-handling decorator applied to every MCP tool function."""
import json
import functools


def _tool(fn):
    """
    Wrap an MCP tool to catch errors and return them as JSON strings.
    Tools must never raise to the MCP framework — they always return a string.

    ValueError  → structured API error from _request; returned as-is for Claude to explain.
    RuntimeError → session/validation errors (no subdomain, no location, etc.).
    Exception   → unexpected server-side errors.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except RuntimeError as e:
            return json.dumps({"error": True, "code": None, "message": str(e)}, indent=2)
        except Exception as e:
            return json.dumps({
                "error":       True,
                "code":        None,
                "message":     str(e),
                "explanation": "An unexpected error occurred in the MCP server.",
            }, indent=2)
    return wrapper
