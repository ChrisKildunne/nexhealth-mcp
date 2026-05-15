import json

from nexhealth.app import mcp
from nexhealth.http_client import _request
from nexhealth.session import _ensure_location
from nexhealth.tools._decorator import _tool


@mcp.tool()
@_tool
def search_patients(name: str, per_page: int = 10) -> str:
    """
    Search for patients by name, locked to the session location set by select_location().

    Every patient returned is guaranteed to belong to the active session location.
    The location_id is embedded in each result so it can be passed directly and
    safely to book_appointment without risk of location mismatch.

    Args:
        name:     First or last name fragment to search for.
        per_page: Max results to return (default 10, max 300).

    Returns a list of matching patients. Each record includes location_id (always
    the session location) to be used as-is when booking.
    """
    location_id = _ensure_location()

    data = _request("GET", "/patients", params={
        "location_id": location_id,
        "name":        name,
        "per_page":    per_page,
        "non_patient": "false",
        "inactive":    "false",
    })

    raw = data.get("data", data)
    if isinstance(raw, dict):
        raw = raw.get("patients", [])
    if not isinstance(raw, list):
        raw = []

    result = [
        {
            "id":            p.get("id"),
            "first_name":    p.get("first_name"),
            "last_name":     p.get("last_name"),
            "date_of_birth": p.get("date_of_birth"),
            "email":         p.get("email"),
            "phone":         p.get("phone_number") or p.get("cell_phone_number"),
            "location_id":   location_id,   # always the session-locked location
        }
        for p in raw
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
@_tool
def get_patient(patient_id: int) -> str:
    """
    Retrieve a single patient by their NexHealth patient ID.

    Args:
        patient_id: The NexHealth patient ID.
    """
    location_id = _ensure_location()
    data = _request("GET", f"/patients/{patient_id}", params={"location_id": location_id})
    return json.dumps(data.get("data", data), indent=2)


@mcp.tool()
@_tool
def create_patient(
    first_name: str,
    last_name: str,
    email: str,
    date_of_birth: str,
    phone_number: str,
    provider_id: int,
    gender: str = None,
    cell_phone_number: str = None,
    home_phone_number: str = None,
    address_line_1: str = None,
    address_line_2: str = None,
    city: str = None,
    state: str = None,
    zip_code: str = None,
) -> str:
    """
    Create a new patient at the session location.

    The patient is always created at the active session location (set by
    select_location). Required fields are first_name, last_name, email,
    date_of_birth, phone_number, and provider_id (the intake provider).

    Args:
        first_name:        Patient first name (required).
        last_name:         Patient last name (required).
        email:             Patient email address (required).
        date_of_birth:     Date of birth in YYYY-MM-DD format (required).
        phone_number:      Primary phone number (required).
        provider_id:       ID of the provider to intake this patient under (required).
                           Use list_providers() to find valid provider IDs.
        gender:            "Male", "Female", or "Other" (defaults to Female if omitted).
        cell_phone_number: Cell phone number (optional).
        home_phone_number: Home phone number (optional).
        address_line_1:    Street address line 1 (optional).
        address_line_2:    Street address line 2 (optional).
        city:              City (optional).
        state:             State abbreviation (optional).
        zip_code:          Zip code (optional).

    Returns the full API response for the newly created patient including their new patient ID.
    """
    location_id = _ensure_location()

    bio: dict = {
        "date_of_birth": date_of_birth,
        "phone_number":  phone_number,
    }
    for key, val in [
        ("gender",            gender),
        ("cell_phone_number", cell_phone_number),
        ("home_phone_number", home_phone_number),
        ("address_line_1",    address_line_1),
        ("address_line_2",    address_line_2),
        ("city",              city),
        ("state",             state),
        ("zip_code",          zip_code),
    ]:
        if val is not None:
            bio[key] = val

    data = _request(
        "POST",
        "/patients",
        params={"location_id": location_id},
        body={
            "provider": {"provider_id": provider_id},
            "patient":  {"first_name": first_name, "last_name": last_name, "email": email, "bio": bio},
        },
    )
    return json.dumps(data, indent=2)
