"""
Pytest wrapper for the integration smoke test.

The actual test logic lives in test_server.py (custom runner).
This file lets pytest discover, gate, and report it as a single test.
"""
import os
import subprocess
import sys
import pytest


@pytest.mark.integration
def test_smoke_suite():
    """Run the full end-to-end smoke test against the live sandbox API."""
    api_key = os.environ.get("NEXHEALTH_API_KEY", "")
    if not api_key:
        pytest.skip("NEXHEALTH_API_KEY not set")

    result = subprocess.run(
        [sys.executable, str(os.path.join(os.path.dirname(__file__), "test_server.py"))],
        env={**os.environ, "NEXHEALTH_API_KEY": api_key},
        capture_output=False,
    )
    assert result.returncode == 0, "Smoke test reported failures — see output above"
