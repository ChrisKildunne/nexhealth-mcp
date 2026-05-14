"""
Entry point for `python -m nexhealth` and the `nexhealth-mcp` console script.

Commands:
    nexhealth-mcp           Start the MCP server (stdio, for Claude Desktop)
    nexhealth-mcp setup     Store your API key in the system keychain
"""
import sys


def setup() -> None:
    """Interactively store the NexHealth API key in the system keychain."""
    try:
        import keyring
    except ImportError:
        print("Error: keyring is not installed. Run: pip install keyring")
        sys.exit(1)

    from nexhealth.auth import _KEYCHAIN_SERVICE, _KEYCHAIN_USERNAME

    print("NexHealth MCP — API key setup")
    print(f"Platform keychain: {keyring.get_keyring().__class__.__name__}")
    print()

    existing = keyring.get_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USERNAME)
    if existing:
        print("An API key is already stored.")
        overwrite = input("Overwrite it? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Aborted — existing key kept.")
            return

    import getpass
    api_key = getpass.getpass("Paste your NexHealth API key (input is hidden): ").strip()
    if not api_key:
        print("Error: no key entered.")
        sys.exit(1)

    keyring.set_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USERNAME, api_key)
    print()
    print("API key stored successfully in your system keychain.")
    print("You can now start the server with: nexhealth-mcp")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
        return

    from nexhealth.app import mcp
    import nexhealth.tools  # noqa: F401
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
