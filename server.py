#!/usr/bin/env python3
"""
NexHealth MCP Server — entry point.

Setup:
    pip install -r requirements.txt

Environment variables:
    NEXHEALTH_API_KEY   – Your NexHealth API key (required)
    NEXHEALTH_SUBDOMAIN – (Optional) Skip institution selection; use this subdomain directly

Run (stdio — for Claude Desktop / local MCP clients):
    python server.py

Run (SSE — for hosted/remote use, e.g. Claude.ai MCP connector):
    python server.py --sse --port 8080
"""
import argparse

# app.py creates the FastMCP instance; importing tools registers all @mcp.tool() decorators.
from nexhealth.app import mcp
import nexhealth.tools  # noqa: F401

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexHealth MCP Server")
    parser.add_argument("--sse",  action="store_true", help="Run with SSE transport instead of stdio")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE transport (default: 8080)")
    args = parser.parse_args()

    if args.sse:
        # Set host/port on the already-instantiated mcp object before run()
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = args.port
        print(f"Starting NexHealth MCP server on http://0.0.0.0:{args.port}/sse", flush=True)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
