"""Unit tests for nexhealth.time_utils — no API calls, no credentials needed."""
import pytest
from nexhealth.time_utils import _local_to_utc, _utc_to_local, _tz_for_location, _tz_for_state


class TestLocalToUtc:
    def test_mountain_time_conversion(self):
        result = _local_to_utc("2026-06-01T09:00:00", "America/Denver")
        assert result == "2026-06-01T15:00:00+00:00"  # MDT is UTC-6

    def test_eastern_time_conversion(self):
        result = _local_to_utc("2026-06-01T09:00:00", "America/New_York")
        assert result == "2026-06-01T13:00:00+00:00"  # EDT is UTC-4

    def test_pacific_time_conversion(self):
        result = _local_to_utc("2026-06-01T09:00:00", "America/Los_Angeles")
        assert result == "2026-06-01T16:00:00+00:00"  # PDT is UTC-7

    def test_output_always_has_utc_offset(self):
        result = _local_to_utc("2026-01-15T10:30:00", "America/Chicago")
        assert result.endswith("+00:00")

    def test_invalid_timezone_raises(self):
        with pytest.raises(RuntimeError, match="Could not convert"):
            _local_to_utc("2026-06-01T09:00:00", "Not/A/Timezone")

    def test_invalid_datetime_raises(self):
        with pytest.raises(RuntimeError):
            _local_to_utc("not-a-date", "America/Denver")

    def test_dst_boundary_winter(self):
        # January — MST (UTC-7), not MDT
        result = _local_to_utc("2026-01-15T09:00:00", "America/Denver")
        assert result == "2026-01-15T16:00:00+00:00"

    def test_dst_boundary_summer(self):
        # July — MDT (UTC-6)
        result = _local_to_utc("2026-07-15T09:00:00", "America/Denver")
        assert result == "2026-07-15T15:00:00+00:00"


class TestUtcToLocal:
    def test_z_suffix(self):
        result = _utc_to_local("2026-06-01T15:00:00Z", "America/Denver")
        assert "9:00 AM" in result or "AM" in result

    def test_plus_zero_suffix(self):
        result = _utc_to_local("2026-06-01T15:00:00+00:00", "America/Denver")
        assert "AM" in result or "PM" in result

    def test_naive_string_appends_utc(self):
        # Naive strings (no offset) should be treated as UTC
        result = _utc_to_local("2026-06-01T15:00:00", "America/Denver")
        assert "AM" in result or "PM" in result

    def test_invalid_string_returns_original(self):
        # Fallback: bad input returns the original string
        result = _utc_to_local("not-a-date", "America/Denver")
        assert result == "not-a-date"

    def test_invalid_timezone_returns_original(self):
        result = _utc_to_local("2026-06-01T15:00:00Z", "Not/A/Timezone")
        assert result == "2026-06-01T15:00:00Z"

    def test_timezone_abbreviation_in_output(self):
        result = _utc_to_local("2026-06-01T15:00:00Z", "America/Denver")
        assert "MDT" in result  # summer = Mountain Daylight Time


class TestTzForState:
    def test_known_states(self):
        assert _tz_for_state("NY") == "America/New_York"
        assert _tz_for_state("CA") == "America/Los_Angeles"
        assert _tz_for_state("TX") == "America/Chicago"
        assert _tz_for_state("CO") == "America/Denver"
        assert _tz_for_state("AZ") == "America/Phoenix"

    def test_case_insensitive(self):
        assert _tz_for_state("ny") == "America/New_York"
        assert _tz_for_state("Ny") == "America/New_York"

    def test_unknown_state_returns_none(self):
        assert _tz_for_state("XX") is None

    def test_empty_string_returns_none(self):
        assert _tz_for_state("") is None

    def test_none_returns_none(self):
        assert _tz_for_state(None) is None


class TestTzForLocation:
    # ── City-level overrides ───────────────────────────────────────────────────

    def test_knoxville_tn_is_eastern(self):
        tz, warning = _tz_for_location("Knoxville", "TN")
        assert tz == "America/New_York"
        assert warning is None  # city was recognised — no warning needed

    def test_chattanooga_tn_is_eastern(self):
        tz, warning = _tz_for_location("Chattanooga", "TN")
        assert tz == "America/New_York"
        assert warning is None

    def test_coeur_dalene_id_is_pacific(self):
        tz, warning = _tz_for_location("Coeur d'Alene", "ID")
        assert tz == "America/Los_Angeles"
        assert warning is None

    def test_moscow_id_is_pacific(self):
        tz, warning = _tz_for_location("Moscow", "ID")
        assert tz == "America/Los_Angeles"
        assert warning is None

    def test_city_lookup_is_case_insensitive(self):
        tz, _ = _tz_for_location("KNOXVILLE", "TN")
        assert tz == "America/New_York"
        tz, _ = _tz_for_location("knoxville", "TN")
        assert tz == "America/New_York"

    # ── State fallback ─────────────────────────────────────────────────────────

    def test_nashville_tn_falls_back_to_central_with_warning(self):
        tz, warning = _tz_for_location("Nashville", "TN")
        assert tz == "America/Chicago"
        assert warning is not None
        assert "Tennessee" in warning or "TN" in warning

    def test_boise_id_falls_back_to_mountain_with_warning(self):
        tz, warning = _tz_for_location("Boise", "ID")
        assert tz == "America/Boise"
        assert warning is not None

    def test_non_split_state_no_warning(self):
        tz, warning = _tz_for_location("Denver", "CO")
        assert tz == "America/Denver"
        assert warning is None

    def test_new_york_city_no_warning(self):
        tz, warning = _tz_for_location("New York", "NY")
        assert tz == "America/New_York"
        assert warning is None

    # ── Edge cases ─────────────────────────────────────────────────────────────

    def test_empty_city_falls_back_to_state(self):
        tz, warning = _tz_for_location("", "CO")
        assert tz == "America/Denver"

    def test_none_city_falls_back_to_state(self):
        tz, warning = _tz_for_location(None, "CO")
        assert tz == "America/Denver"

    def test_unknown_state_returns_none(self):
        tz, warning = _tz_for_location("Somewhere", "XX")
        assert tz is None

    def test_both_none_returns_none(self):
        tz, warning = _tz_for_location(None, None)
        assert tz is None
