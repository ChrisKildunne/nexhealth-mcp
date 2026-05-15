"""Unit tests for nexhealth.config_loader priority resolution."""
import os
import pytest


class TestEnvVarPriority:
    """Env vars must win over config.yaml values."""

    def test_subdomain_from_env(self, monkeypatch):
        monkeypatch.setenv("NEXHEALTH_SUBDOMAIN", "env-subdomain")
        import nexhealth.config_loader as cl
        import importlib
        importlib.reload(cl)
        assert cl.SUBDOMAIN == "env-subdomain"
        monkeypatch.delenv("NEXHEALTH_SUBDOMAIN", raising=False)
        importlib.reload(cl)

    def test_timezone_override_from_env(self, monkeypatch):
        monkeypatch.setenv("NEXHEALTH_TIMEZONE_OVERRIDE", "America/New_York")
        import nexhealth.config_loader as cl
        import importlib
        importlib.reload(cl)
        assert cl.TIMEZONE_OVERRIDE == "America/New_York"
        monkeypatch.delenv("NEXHEALTH_TIMEZONE_OVERRIDE", raising=False)
        importlib.reload(cl)

    def test_sse_host_from_env(self, monkeypatch):
        monkeypatch.setenv("NEXHEALTH_SSE_HOST", "0.0.0.0")
        import nexhealth.config_loader as cl
        import importlib
        importlib.reload(cl)
        assert cl.SSE_HOST == "0.0.0.0"
        monkeypatch.delenv("NEXHEALTH_SSE_HOST", raising=False)
        importlib.reload(cl)

    def test_sse_port_from_env(self, monkeypatch):
        monkeypatch.setenv("NEXHEALTH_SSE_PORT", "9090")
        import nexhealth.config_loader as cl
        import importlib
        importlib.reload(cl)
        assert cl.SSE_PORT == 9090
        monkeypatch.delenv("NEXHEALTH_SSE_PORT", raising=False)
        importlib.reload(cl)


class TestGetFunction:
    """Tests the _get() resolution logic directly."""

    def test_env_var_wins_over_dict(self, monkeypatch):
        import nexhealth.config_loader as cl
        monkeypatch.setenv("NEXHEALTH_MYKEY", "from-env")
        monkeypatch.setattr(cl, "_raw", {"mysection": {"mykey": "from-yaml"}})
        assert cl._get("mysection", "mykey", "default") == "from-env"

    def test_yaml_value_used_when_no_env(self, monkeypatch):
        import nexhealth.config_loader as cl
        monkeypatch.delenv("NEXHEALTH_MYKEY", raising=False)
        monkeypatch.setattr(cl, "_raw", {"mysection": {"mykey": "from-yaml"}})
        assert cl._get("mysection", "mykey", "default") == "from-yaml"

    def test_default_used_when_neither(self, monkeypatch):
        import nexhealth.config_loader as cl
        monkeypatch.delenv("NEXHEALTH_MYKEY", raising=False)
        monkeypatch.setattr(cl, "_raw", {})
        assert cl._get("mysection", "mykey", "the-default") == "the-default"

    def test_empty_string_env_var_falls_through(self, monkeypatch):
        import nexhealth.config_loader as cl
        monkeypatch.setenv("NEXHEALTH_MYKEY", "  ")  # whitespace-only
        monkeypatch.setattr(cl, "_raw", {"mysection": {"mykey": "from-yaml"}})
        assert cl._get("mysection", "mykey", "default") == "from-yaml"


class TestDefaults:
    """Verify safe out-of-the-box defaults when no config is present."""

    def test_sse_host_default_is_localhost(self):
        import nexhealth.config_loader as cl
        # If no env var and no config sets it, should default to 127.0.0.1
        if not os.environ.get("NEXHEALTH_SSE_HOST") and not cl._raw.get("server", {}).get("sse_host"):
            assert cl.SSE_HOST == "127.0.0.1"

    def test_sse_port_default_is_8080(self):
        import nexhealth.config_loader as cl
        if not os.environ.get("NEXHEALTH_SSE_PORT") and not cl._raw.get("server", {}).get("sse_port"):
            assert cl.SSE_PORT == 8080
