"""
Shared pytest fixtures and configuration.

Unit tests (tests/unit/) require no credentials and always run.
Integration tests (tests/integration/) require NEXHEALTH_API_KEY and are
skipped automatically when it isn't set.
"""
import os
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip integration tests when NEXHEALTH_API_KEY is not set."""
    skip_integration = pytest.mark.skip(reason="NEXHEALTH_API_KEY not set — skipping integration tests")
    for item in items:
        if "integration" in str(item.fspath):
            if not os.environ.get("NEXHEALTH_API_KEY"):
                item.add_marker(skip_integration)
