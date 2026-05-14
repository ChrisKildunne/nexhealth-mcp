"""
Unit tests for nexhealth.content_loader.

These tests exist specifically to catch path bugs that cause get_started()
and get_workflow() to silently return empty results. If any of these fail,
the content_loader directory paths are wrong.
"""
import pytest
from nexhealth.content_loader import (
    ONBOARDING,
    WORKFLOWS,
    SANDBOX_GUIDE,
    PRODUCTION_GUIDE,
    ONBOARDING_DIR,
    WORKFLOW_DIR,
)


class TestDirectoriesExist:
    def test_onboarding_dir_exists(self):
        import os
        assert os.path.isdir(ONBOARDING_DIR), \
            f"ONBOARDING_DIR does not exist: {ONBOARDING_DIR!r}\n" \
            "Check content_loader.py — the path is probably missing 'docs/'"

    def test_workflow_dir_exists(self):
        import os
        assert os.path.isdir(WORKFLOW_DIR), \
            f"WORKFLOW_DIR does not exist: {WORKFLOW_DIR!r}\n" \
            "Check content_loader.py — the path is probably missing 'docs/'"


class TestOnboardingContent:
    def test_onboarding_is_not_empty(self):
        assert len(ONBOARDING) > 0, \
            "ONBOARDING dict is empty — content_loader failed to read any .md files"

    def test_sandbox_sections_present(self):
        required = ["sandbox_overview", "dev_portal", "api_key", "sandbox_first_call"]
        missing = [k for k in required if k not in ONBOARDING]
        assert not missing, f"Missing sandbox onboarding sections: {missing}"

    def test_production_sections_present(self):
        required = [
            "production_overview", "production_institution",
            "production_datasource", "production_api_key", "production_first_call",
        ]
        missing = [k for k in required if k not in ONBOARDING]
        assert not missing, f"Missing production onboarding sections: {missing}"

    def test_no_placeholder_text_remains(self):
        for key, content in ONBOARDING.items():
            assert "PLACEHOLDER" not in content, \
                f"Section {key!r} still contains placeholder text — fill it in"

    def test_no_load_errors(self):
        for key, content in ONBOARDING.items():
            assert not content.startswith("[Could not load"), \
                f"Section {key!r} failed to load: {content}"


class TestWorkflowContent:
    def test_workflows_is_not_empty(self):
        assert len(WORKFLOWS) > 0, \
            "WORKFLOWS dict is empty — content_loader failed to read any .md files"

    def test_core_workflows_present(self):
        required = ["book_appointment", "create_patient", "session_setup", "troubleshoot"]
        missing = [k for k in required if k not in WORKFLOWS]
        assert not missing, f"Missing workflow sections: {missing}"

    def test_no_load_errors(self):
        for key, content in WORKFLOWS.items():
            assert not content.startswith("[Could not load"), \
                f"Workflow {key!r} failed to load: {content}"


class TestBuiltGuides:
    def test_sandbox_guide_has_no_missing_sections(self):
        assert "[Section" not in SANDBOX_GUIDE, \
            "SANDBOX_GUIDE contains '[Section ... not found]' — a required key is missing from ONBOARDING"

    def test_production_guide_has_no_missing_sections(self):
        assert "[Section" not in PRODUCTION_GUIDE, \
            "PRODUCTION_GUIDE contains '[Section ... not found]' — a required key is missing from ONBOARDING"

    def test_sandbox_guide_is_substantial(self):
        assert len(SANDBOX_GUIDE) > 200, "SANDBOX_GUIDE is suspiciously short"

    def test_production_guide_is_substantial(self):
        assert len(PRODUCTION_GUIDE) > 200, "PRODUCTION_GUIDE is suspiciously short"
