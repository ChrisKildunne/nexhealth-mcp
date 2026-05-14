# Changelog

## Refactor + Bug Fixes — 2026-05-14

### What changed

The original single-file server (`nexhealth_mcp_server.py`, 1618 lines) was split into a proper Python package with focused modules. The new entry point is `server.py`. The old file is kept for reference but is no longer used.

**New structure:**
```
nexhealth/
├── config.py           — constants and state→timezone lookup table
├── session.py          — 5 session globals + session guard helpers
├── auth.py             — token fetch, cache, and auto-refresh
├── http_client.py      — _raw_request, _request, error formatting
├── time_utils.py       — UTC/local timezone conversion helpers
├── content_loader.py   — markdown file loader (onboarding + workflows)
├── app.py              — FastMCP instance (6 lines)
└── tools/
    ├── _decorator.py       — @_tool error-handling wrapper
    ├── institutions.py     — list_institutions, select_institution, current_session
    ├── locations.py        — list_locations, select_location
    ├── patients.py         — search_patients, get_patient, create_patient
    ├── providers.py        — list_providers, list_appointment_types
    ├── slots.py            — get_available_slots
    ├── appointments.py     — book_appointment, get_appointment, list_appointments,
    │                         cancel_appointment, patch_appointment
    ├── operatories.py      — list_operatories
    ├── working_hours.py    — create_working_hour
    └── content.py          — get_started, get_workflow
server.py               — entry point (37 lines)
```

No tool behavior changed. All 20 tools are still registered and behave identically from Claude's perspective.

---

### Bug fixes

**1. `book_appointment` location guard always rejected valid calls (critical)**

`location_id` has a default of `None`. The guard compared `None != session_location_id`, which is always `True`, causing every booking to raise a RuntimeError unless the caller explicitly passed the session location ID.

Fixed in `nexhealth/tools/appointments.py`:
```python
# Before
if location_id != session_location:

# After
if location_id is not None and location_id != session_location:
```

**2. SSE port argument was silently ignored (high)**

`--port` was parsed but never applied. The SSE server always bound to the FastMCP default (`127.0.0.1:8000`) regardless of what was passed, while the startup print statement claimed `0.0.0.0:8080`.

Fixed in `server.py` — `mcp.settings.host` and `mcp.settings.port` are now set from parsed args before calling `mcp.run()`.

**3. `list_institutions` swallowed authentication errors (high)**

A 401 from the API produced a structured error dict. The function's data extraction logic (`data.get("data", data)` then `.get("institutions", [])`) consumed that dict silently and returned an empty list, causing Claude to report "No institutions found — check your API key" instead of showing the actual error.

Fixed in `nexhealth/tools/institutions.py` — error dicts are detected and returned immediately before any data extraction.

**4. Merge conflict in `workflows/create_working_hour.md` (high)**

The file contained six unresolved git conflict marker sets (`<<<<<<< HEAD`, `=======`, `>>>>>>>`). Calling `get_workflow("working hours")` returned the raw conflicted text.

Fixed by resolving in favor of the HEAD version, which includes the "What is a Working Hour?" conceptual section, the "After Creating — Verifying Slots" section, and the richer error table.

**5. `get_available_slots` used server timezone for "today" (low)**

When `start_date` was omitted, `datetime.now()` used the server machine's local timezone. If the server runs in UTC and the practice is in Pacific time, "today" could be off by one calendar day late at night.

Fixed in `nexhealth/tools/slots.py` — `datetime.now(tz=ZoneInfo(location_tz))` is used when the session timezone is known.

**6. `functools` imported inside the decorator on every function application (low)**

`import functools` was inside the `_tool` wrapper closure, re-importing the module once per decorated function at load time.

Fixed in `nexhealth/tools/_decorator.py` — import moved to module level.

**7. Duplicate docstring line in `book_appointment` (trivial)**

"The session location (set by select_location) is always used and enforced." appeared twice consecutively. Removed.

---

### Other improvements

- **`requirements.txt` added** — `mcp[cli]>=1.27.1` is now machine-readable for `pip install -r`.
- **Start script updated** — `nexhealth-mcp-start.sh` now points to `server.py`.
- **`create_patient` optional fields** — the long series of `if field: bio[field] = field` blocks replaced with a single loop over a list of `(key, value)` pairs.
- **Unused imports removed** — `sys`, `timedelta`, `timezone`, `tzinfo`, `ZoneInfoNotFoundError` were all imported but never used.
- **`docs/` directory added** — see `docs/setup.md`, `docs/usage.md`, `docs/architecture.md`.
