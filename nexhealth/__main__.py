"""
Entry point for `python -m nexhealth` and the `nexhealth-mcp` console script.

Commands:
    nexhealth-mcp           Start the MCP server (stdio, for Claude Desktop)
    nexhealth-mcp init      First-time setup wizard — generates config.yaml and stores API key
    nexhealth-mcp setup     Store (or update) your API key in the system keychain
"""
import os
import sys


def _hr(char: str = "─", width: int = 52) -> str:
    return char * width


def _section(title: str) -> None:
    print()
    print(_hr())
    print(f"  {title}")
    print(_hr())


def _ask(prompt: str, default: str = "") -> str:
    """Prompt the user, returning default on empty input."""
    suffix = f" [{default}]" if default else ""
    return input(f"{prompt}{suffix}: ").strip() or default


def _ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {hint}: ").strip().lower()
    if not answer:
        return default
    return answer.startswith("y")


def setup(quiet: bool = False) -> bool:
    """
    Store (or update) the NexHealth API key in the macOS keychain via the
    security CLI. This ensures full compatibility with the start script which
    reads the key using the same CLI tool.
    Returns True if the key was stored, False if the user skipped/aborted.
    """
    import subprocess
    import getpass

    SERVICE  = "NEXHEALTH_API_KEY"
    USERNAME = os.environ.get("USER", "")

    if not quiet:
        # Check if a key already exists
        result = subprocess.run(
            ["security", "find-generic-password", "-a", USERNAME, "-s", SERVICE, "-w"],
            capture_output=True, text=True
        )
        existing = result.returncode == 0 and result.stdout.strip()
        if existing:
            print("  An API key is already stored in the keychain.")
            if not _ask_yes_no("  Overwrite it?", default=False):
                print("  Keeping existing key.")
                return False

    api_key = getpass.getpass("  Paste your NexHealth API key (input hidden): ").strip()
    if not api_key:
        print("  No key entered — skipping.")
        return False

    # Delete existing entry first (ignore error if it doesn't exist)
    subprocess.run(
        ["security", "delete-generic-password", "-a", USERNAME, "-s", SERVICE],
        capture_output=True
    )

    # Store the new key via the security CLI
    result = subprocess.run(
        ["security", "add-generic-password", "-a", USERNAME, "-s", SERVICE, "-w", api_key],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"  Error storing key: {result.stderr.strip()}")
        return False

    print("  API key stored. ✓")
    return True


def init() -> None:
    """First-time setup wizard. Generates config.yaml and stores the API key."""
    from pathlib import Path
    import yaml  # pyyaml is a required dep

    config_path  = Path(__file__).parent.parent / "config.yaml"
    example_path = Path(__file__).parent.parent / "config.yaml.example"

    # When installed as a uv tool, config lives next to the start script
    # in ~/nexhealth/ rather than in the package directory.
    home_config = Path.home() / "nexhealth" / "config.yaml"
    home_example = Path.home() / "nexhealth" / "config.yaml.example"
    if home_example.exists():
        config_path  = home_config
        example_path = home_example

    print()
    print(_hr("═"))
    print("  NexHealth MCP Server — Setup Wizard")
    print(_hr("═"))
    print()
    print("  This wizard will store your API key securely and")
    print("  generate a config.yaml file for your installation.")

    if config_path.exists():
        print()
        print("  config.yaml already exists.")
        if not _ask_yes_no("  Overwrite it?", default=False):
            print("  Keeping existing config.yaml.")
            print("  Run `nexhealth-mcp setup` to update your API key only.")
            return

    # ── Step 1: API key ───────────────────────────────────────────────────────
    _section("Step 1 of 3 — API Key")
    print()
    print("  Your API key is stored securely in your system keychain.")
    print("  Get it from: https://developers.nexhealth.com → API Key")
    print()
    if _ask_yes_no("  Store API key now?", default=True):
        setup(quiet=True)
    else:
        print()
        print("  Skipped. Run `nexhealth-mcp setup` later, or set")
        print("  NEXHEALTH_API_KEY as an environment variable.")

    # ── Step 2: Subdomain ─────────────────────────────────────────────────────
    _section("Step 2 of 3 — Institution (optional)")
    print()
    print("  If you know your NexHealth subdomain, pre-setting it skips")
    print("  the institution selection step at the start of every session.")
    print("  Leave blank to select interactively each time.")
    print()
    subdomain = _ask("  Subdomain")

    # ── Step 3: Timezone ──────────────────────────────────────────────────────
    _section("Step 3 of 3 — Timezone (optional)")
    print()
    print("  Some states have split timezones. The server derives timezone")
    print("  from your location's state, but may be wrong for:")
    print()
    print("    Tennessee  — Eastern TN (Knoxville, Chattanooga) → America/New_York")
    print("    Idaho      — Northern ID (Coeur d'Alene, Moscow) → America/Los_Angeles")
    print()
    print("  Leave blank unless your practice is in one of these areas.")
    print()
    timezone_override = _ask("  Timezone override (IANA, e.g. America/New_York)")

    # Validate the timezone if provided
    if timezone_override:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(timezone_override)
            print(f"  Timezone '{timezone_override}' recognised. ✓")
        except Exception:
            print(f"  Warning: '{timezone_override}' is not a recognised IANA timezone.")
            print("  Check https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
            if not _ask_yes_no("  Keep it anyway?", default=False):
                timezone_override = ""

    # ── Write config.yaml ─────────────────────────────────────────────────────
    print()
    print(_hr())

    if example_path.exists():
        with open(example_path, encoding="utf-8") as f:
            raw_example = f.read()

        def _set_value(text: str, key: str, value: str) -> str:
            import re
            return re.sub(
                rf'^(\s*{re.escape(key)}:\s*).*$',
                rf'\g<1>"{value}"' if value else rf'\g<1>""',
                text,
                flags=re.MULTILINE,
            )

        output = raw_example
        if subdomain:
            output = _set_value(output, "subdomain", subdomain)
        if timezone_override:
            output = _set_value(output, "timezone_override", timezone_override)

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        config = {
            "nexhealth": {"subdomain": subdomain},
            "server": {
                "timezone_override": timezone_override,
                "sse_host": "127.0.0.1",
                "sse_port": 8080,
            },
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print()
    print("  config.yaml written. ✓")
    print()
    print(_hr("═"))
    print("  Setup complete.")
    print()
    print("  Next steps:")
    print("  1. Add the start script to your Claude Desktop config")
    print("     (see README for the exact path and JSON)")
    print("  2. Fully quit Claude Desktop (Cmd+Q)")
    print("  3. Relaunch Claude Desktop")
    print('  4. Ask Claude: "Can you list my NexHealth institutions?"')
    print()
    print("  Update API key:  nexhealth-mcp setup")
    print("  Re-run wizard:   nexhealth-mcp init")
    print(_hr("═"))
    print()


def main() -> None:
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init()
            return
        if cmd == "setup":
            print()
            print("NexHealth MCP — API Key Setup")
            print(_hr())
            setup(quiet=False)
            print()
            return

    from nexhealth.app import mcp
    import nexhealth.tools  # noqa: F401
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
