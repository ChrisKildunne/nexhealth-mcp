"""
Entry point for `python -m nexhealth` and the `nexhealth-mcp` console script.

Install and run with uv (no manual pip/venv needed):
    uv tool install .
    nexhealth-mcp

Or run directly without installing:
    uv run nexhealth-mcp
"""
from nexhealth.app import mcp
import nexhealth.tools  # noqa: F401


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
