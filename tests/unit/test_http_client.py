"""Unit tests for nexhealth.http_client error handling — no API calls needed."""
import pytest
from nexhealth.http_client import _structured_error, _HTTP_EXPLANATIONS


class TestStructuredError:
    def test_returns_error_true(self):
        result = _structured_error(404, "not found", "/patients")
        assert result["error"] is True

    def test_includes_code(self):
        result = _structured_error(422, "validation failed")
        assert result["code"] == 422

    def test_includes_path(self):
        result = _structured_error(400, "bad request", "/appointments")
        assert result["path"] == "/appointments"

    def test_empty_path_default(self):
        result = _structured_error(400, "bad request")
        assert result["path"] == ""

    def test_dict_detail_extracts_description(self):
        result = _structured_error(422, {"description": "Email is invalid"})
        assert result["message"] == "Email is invalid"

    def test_dict_detail_falls_back_to_message_key(self):
        result = _structured_error(400, {"message": "Missing required field"})
        assert result["message"] == "Missing required field"

    def test_dict_detail_falls_back_to_error_key(self):
        result = _structured_error(403, {"error": "Forbidden"})
        assert result["message"] == "Forbidden"

    def test_string_detail_used_as_message(self):
        result = _structured_error(500, "Internal server error")
        assert result["message"] == "Internal server error"

    def test_detail_preserved_in_full(self):
        detail = {"description": "short", "extra": "data"}
        result = _structured_error(422, detail)
        assert result["detail"] == detail

    def test_known_codes_have_explanations(self):
        for code in [400, 401, 403, 404, 422, 429, 500]:
            result = _structured_error(code, "x")
            assert result["explanation"] != f"Unexpected HTTP {code} from NexHealth API.", \
                f"HTTP {code} has no explanation in _HTTP_EXPLANATIONS"

    def test_unknown_code_has_fallback_explanation(self):
        result = _structured_error(418, "I'm a teapot")
        assert "418" in result["explanation"]

    def test_explanation_is_human_readable(self):
        result = _structured_error(429, "rate limited")
        assert len(result["explanation"]) > 20
        assert result["explanation"][0].isupper()  # starts with capital letter


class TestHttpExplanations:
    def test_all_common_codes_covered(self):
        for code in [400, 401, 403, 404, 422, 429, 500]:
            assert code in _HTTP_EXPLANATIONS, f"HTTP {code} missing from _HTTP_EXPLANATIONS"

    def test_explanations_are_non_empty_strings(self):
        for code, msg in _HTTP_EXPLANATIONS.items():
            assert isinstance(msg, str) and len(msg) > 10, \
                f"Explanation for {code} is too short: {msg!r}"
