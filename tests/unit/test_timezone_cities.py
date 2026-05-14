"""
Validates the CITY_TIMEZONE_OVERRIDES and SPLIT_TIMEZONE_STATES data in config.py.
Every entry must be a real IANA timezone and every city must resolve correctly.
"""
import pytest
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from nexhealth.config import CITY_TIMEZONE_OVERRIDES, SPLIT_TIMEZONE_STATES, STATE_TIMEZONES


class TestCityTimezoneOverrides:
    def test_all_timezones_are_valid_iana(self):
        """Every timezone value must be recognisable by zoneinfo."""
        bad = []
        for city, tz in CITY_TIMEZONE_OVERRIDES.items():
            try:
                ZoneInfo(tz)
            except ZoneInfoNotFoundError:
                bad.append(f"{city!r}: {tz!r}")
        assert not bad, f"Invalid IANA timezones in CITY_TIMEZONE_OVERRIDES:\n" + "\n".join(bad)

    def test_all_keys_are_lowercase(self):
        """Keys must be lowercase for case-insensitive matching to work."""
        bad = [k for k in CITY_TIMEZONE_OVERRIDES if k != k.lower()]
        assert not bad, f"Non-lowercase keys in CITY_TIMEZONE_OVERRIDES: {bad}"

    def test_eastern_tn_cities_are_new_york(self):
        eastern_tn = ["knoxville", "chattanooga", "oak ridge", "kingsport",
                      "bristol", "johnson city", "morristown", "maryville"]
        for city in eastern_tn:
            assert CITY_TIMEZONE_OVERRIDES.get(city) == "America/New_York", \
                f"{city!r} should map to America/New_York"

    def test_northern_id_cities_are_pacific(self):
        pacific_id = ["coeur d'alene", "moscow", "sandpoint", "lewiston",
                      "post falls", "hayden"]
        for city in pacific_id:
            assert CITY_TIMEZONE_OVERRIDES.get(city) == "America/Los_Angeles", \
                f"{city!r} should map to America/Los_Angeles"


class TestSplitTimezoneStates:
    def test_split_states_are_subset_of_state_timezones(self):
        """Every split-timezone state must also have an entry in STATE_TIMEZONES."""
        for state in SPLIT_TIMEZONE_STATES:
            assert state in STATE_TIMEZONES, \
                f"{state!r} is in SPLIT_TIMEZONE_STATES but not STATE_TIMEZONES"

    def test_warnings_are_non_empty_strings(self):
        for state, msg in SPLIT_TIMEZONE_STATES.items():
            assert isinstance(msg, str) and len(msg) > 10, \
                f"Warning for {state!r} is too short or not a string"

    def test_tn_and_id_are_split_states(self):
        assert "TN" in SPLIT_TIMEZONE_STATES
        assert "ID" in SPLIT_TIMEZONE_STATES


class TestStateTimezones:
    def test_all_state_timezones_are_valid_iana(self):
        bad = []
        for state, tz in STATE_TIMEZONES.items():
            try:
                ZoneInfo(tz)
            except ZoneInfoNotFoundError:
                bad.append(f"{state}: {tz!r}")
        assert not bad, f"Invalid IANA timezones in STATE_TIMEZONES:\n" + "\n".join(bad)

    def test_all_50_states_plus_territories_present(self):
        required = {
            "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL",
            "IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT",
            "NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
            "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
        }
        missing = required - set(STATE_TIMEZONES.keys())
        assert not missing, f"Missing states in STATE_TIMEZONES: {sorted(missing)}"
