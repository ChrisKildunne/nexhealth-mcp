#!/usr/bin/env python3
"""
End-to-end smoke test for the NexHealth MCP server.

Walks the full session setup → patient search → provider + slot lookup chain
against the real API. Does NOT book, create, or modify anything.

Usage:
    NEXHEALTH_API_KEY=<key> python3 test_server.py
    python3 test_server.py                          # reads key from env
"""
import os
import sys
import json
import textwrap

# ── helpers ────────────────────────────────────────────────────────────────────

_PASS  = "  PASS"
_FAIL  = "  FAIL"
_SKIP  = "  SKIP"
_total = 0
_passed = 0
_failed = 0

def check(label: str, value, *, expect=None, contains=None, truthy=True):
    global _total, _passed, _failed
    _total += 1
    ok = True
    reason = ""
    if expect is not None and value != expect:
        ok = False
        reason = f"expected {expect!r}, got {value!r}"
    if contains is not None and contains not in str(value):
        ok = False
        reason = f"{contains!r} not found in result"
    if truthy and not value:
        ok = False
        reason = f"expected truthy, got {value!r}"
    if ok:
        _passed += 1
        print(f"{_PASS}  {label}")
    else:
        _failed += 1
        print(f"{_FAIL}  {label}  ← {reason}")
    return ok

def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

def dump(label: str, data, max_items: int = 3):
    """Print a short preview of a result."""
    if isinstance(data, list):
        preview = data[:max_items]
        suffix  = f"  ... and {len(data) - max_items} more" if len(data) > max_items else ""
    else:
        preview = data
        suffix  = ""
    print(f"  {label}:")
    for line in json.dumps(preview, indent=2).splitlines():
        print(f"    {line}")
    if suffix:
        print(f"    {suffix}")


# ── setup ──────────────────────────────────────────────────────────────────────

api_key = os.environ.get("NEXHEALTH_API_KEY", "").strip()
if not api_key:
    print("ERROR: NEXHEALTH_API_KEY not set.")
    sys.exit(1)

os.environ["NEXHEALTH_API_KEY"] = api_key

# Import the package (this also registers all tools)
from nexhealth.app import mcp
import nexhealth.tools          # noqa: F401 — registers @mcp.tool() decorators
import nexhealth.session as S

# Import tools directly so we can call them as plain Python functions
from nexhealth.tools.institutions  import list_institutions, select_institution, current_session
from nexhealth.tools.locations     import list_locations, select_location
from nexhealth.tools.patients      import search_patients
from nexhealth.tools.providers     import list_providers, list_appointment_types
from nexhealth.tools.slots         import get_available_slots
from nexhealth.tools.appointments  import list_appointments
from nexhealth.tools.operatories   import list_operatories
from nexhealth.tools.content       import get_workflow, get_started

print("\nNexHealth MCP Server — smoke test")
print("=" * 60)

# ── 1. tool registration ───────────────────────────────────────────────────────

section("1. Tool registration")
tools = [t.name for t in mcp._tool_manager.list_tools()]
check("20 tools registered", len(tools), expect=20)

# ── 2. authentication ──────────────────────────────────────────────────────────

section("2. Authentication")
from nexhealth.auth import _get_token
try:
    token = _get_token()
    check("Bearer token fetched", token, contains=".")
    check("Token cached in session", S._bearer_token, truthy=True)
except Exception as e:
    print(f"{_FAIL}  Token fetch raised: {e}")
    _failed += 1
    _total  += 1
    print("\nCannot continue without a valid token.")
    sys.exit(1)

# ── 3. current_session (before institution) ────────────────────────────────────

section("3. current_session — pre-setup state")
raw = json.loads(current_session())
check("authenticated=true",  raw.get("authenticated"), expect=True)
check("no subdomain yet",    raw.get("active_subdomain"), contains="not set")
check("no location yet",     raw.get("active_location_id"), contains="not set")

# ── 4. list_institutions ───────────────────────────────────────────────────────

section("4. list_institutions")
raw = json.loads(list_institutions())
check("returned a list",       isinstance(raw, list), truthy=True)
check("at least one institution", len(raw) >= 1, truthy=True)
check("each has subdomain",    all("subdomain" in i for i in raw), truthy=True)
dump("institutions", raw)

institution  = raw[0]
subdomain    = institution["subdomain"]
print(f"\n  → using institution: {institution.get('name')!r}  subdomain={subdomain!r}")

# ── 5. select_institution ──────────────────────────────────────────────────────

section("5. select_institution")
raw = json.loads(select_institution(subdomain))
check("message contains subdomain", raw.get("message", ""), contains=subdomain)
check("locations list returned",    isinstance(raw.get("locations"), list), truthy=True)
check("subdomain in session",       S._subdomain, expect=subdomain)
dump("locations preview", raw.get("locations", []))

# ── 6. list_locations ──────────────────────────────────────────────────────────

section("6. list_locations")
raw = json.loads(list_locations())
check("returned a list",          isinstance(raw, list), truthy=True)
check("at least one location",    len(raw) >= 1, truthy=True)
check("each has id and name",     all("id" in l and "name" in l for l in raw), truthy=True)
dump("locations", raw)

location    = raw[0]
location_id = location["id"]
print(f"\n  → using location: {location.get('name')!r}  id={location_id}")

# ── 7. select_location ─────────────────────────────────────────────────────────

section("7. select_location")
raw = json.loads(select_location(location_id))
check("message = Location locked", raw.get("message"), expect="Location locked for this session.")
check("location_id in response",   raw.get("location_id"), expect=location_id)
check("timezone set",              raw.get("timezone"), truthy=True)
check("session location_id set",   S._location_id, expect=location_id)
check("session timezone set",      S._location_tz, truthy=True)
print(f"  timezone: {raw.get('timezone')}")

# ── 8. current_session (after setup) ──────────────────────────────────────────

section("8. current_session — post-setup state")
raw = json.loads(current_session())
check("authenticated=true",        raw.get("authenticated"), expect=True)
check("subdomain set",             raw.get("active_subdomain"), expect=subdomain)
check("location_id set",           raw.get("active_location_id"), expect=location_id)
check("timezone set",              raw.get("active_timezone"), truthy=True)

# ── 9. search_patients ─────────────────────────────────────────────────────────

section("9. search_patients")
raw = json.loads(search_patients("a", per_page=5))
check("returned a list",         isinstance(raw, list), truthy=True)
check("location_id embedded",    all(p.get("location_id") == location_id for p in raw) if raw else True, truthy=True)
check("has first_name field",    all("first_name" in p for p in raw) if raw else True, truthy=True)
if raw:
    dump("patients (first 2)", raw[:2])
else:
    print(f"  (no patients matching 'a' at this location)")

# ── 10. list_providers ─────────────────────────────────────────────────────────

section("10. list_providers")
raw = json.loads(list_providers(location_id))
check("returned a list",         isinstance(raw, list), truthy=True)
check("has id field",            all("id" in p for p in raw) if raw else True, truthy=True)
dump("providers", raw)

provider_id = raw[0]["id"] if raw else None
print(f"  → using provider_id={provider_id}")

# ── 11. list_appointment_types ─────────────────────────────────────────────────

section("11. list_appointment_types")
raw = json.loads(list_appointment_types(location_id))
check("returned a list",  isinstance(raw, list), truthy=True)
check("has name field",   all("name" in t for t in raw) if raw else True, truthy=True)
dump("appointment types", raw)

# ── 12. list_operatories ───────────────────────────────────────────────────────

section("12. list_operatories")
raw = json.loads(list_operatories(location_id))
check("returned a list", isinstance(raw, list), truthy=True)
dump("operatories", raw)

# ── 13. get_available_slots ────────────────────────────────────────────────────

section("13. get_available_slots")
if provider_id:
    raw = json.loads(get_available_slots(provider_id=provider_id, days=7))
    check("returned a dict (grouped by date)", isinstance(raw, dict), truthy=True)
    total_slots = sum(len(v) for v in raw.values())
    print(f"  slot dates: {sorted(raw.keys())}")
    print(f"  total slots across {len(raw)} date(s): {total_slots}")
    if raw:
        first_date  = sorted(raw.keys())[0]
        first_slot  = raw[first_date][0]
        check("slot has 'time' field",         "time" in first_slot, truthy=True)
        check("slot has 'operatory_id' field", "operatory_id" in first_slot, truthy=True)
        check("slot has 'display_time' field", "display_time" in first_slot, truthy=True)
        print(f"  sample slot: {json.dumps(first_slot, indent=4)}")
    else:
        print(f"  (no slots available in the next 7 days for provider {provider_id})")
        _total += 3   # count the slot field checks as skipped
else:
    print(f"{_SKIP}  no provider found — skipping slot check")

# ── 14. list_appointments ──────────────────────────────────────────────────────

section("14. list_appointments")
raw = json.loads(list_appointments(
    start="2026-01-01T00:00:00+0000",
    end="2026-12-31T23:59:59+0000",
    per_page=5,
))
check("has 'appointments' key",  "appointments" in raw, truthy=True)
check("has 'navigation' key",    "navigation" in raw,    truthy=True)
check("has 'count' key",         "count" in raw,          truthy=True)
nav = raw.get("navigation", {})
check("navigation has has_next_page", "has_next_page" in nav, truthy=True)
print(f"  count={raw.get('count')}  has_next_page={nav.get('has_next_page')}")

# ── 15. get_workflow ───────────────────────────────────────────────────────────

section("15. get_workflow")
raw = json.loads(get_workflow())
check("lists available workflows",    "available_workflows" in raw, truthy=True)
workflows = raw.get("available_workflows", [])
for expected in ["book_appointment", "session_setup", "troubleshoot"]:
    check(f"workflow '{expected}' present", expected in workflows, truthy=True)

raw2 = get_workflow("book appointment")
check("book_appointment content returned", "book" in raw2.lower(), truthy=True)

# ── 16. error handling ─────────────────────────────────────────────────────────

section("16. Error handling — session guard")

# Temporarily clear the location to test the guard
saved_loc = S._location_id
S._location_id = None
raw = json.loads(search_patients("test"))
check("guard error is structured JSON", raw.get("error"), expect=True)
check("guard message is helpful",       raw.get("message", ""), contains="select_location")
S._location_id = saved_loc  # restore

# location_id mismatch in book_appointment
from nexhealth.tools.appointments import book_appointment
raw = json.loads(book_appointment(
    patient_id=1, provider_id=2, start_time="2026-06-01T09:00:00",
    operatory_id=3, location_id=99999
))
check("location mismatch rejected",     raw.get("error"), expect=True)
check("mismatch message is helpful",    raw.get("message", ""), contains="session location")

# ── summary ────────────────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print(f"  Results: {_passed}/{_total} passed", end="")
if _failed:
    print(f"   ({_failed} FAILED)")
else:
    print("   — all clear")
print(f"{'=' * 60}\n")

sys.exit(0 if _failed == 0 else 1)
