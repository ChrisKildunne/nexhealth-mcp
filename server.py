#!/usr/bin/env python3
"""
NexHealth MCP Server — entry point.

Setup:
    cp config.yaml.example config.yaml   # edit as needed
    python -m nexhealth setup            # store API key in system keychain
    python server.py

Run (stdio — for Claude Desktop / local MCP clients):
    python server.py

Run (SSE — for hosted/remote use, e.g. Claude.ai MCP connector):
    python server.py --sse
"""
import argparse

from nexhealth import config_loader as _cfg
from nexhealth.app import mcp
import nexhealth.tools  # noqa: F401

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexHealth MCP Server")
    parser.add_argument("--sse",  action="store_true", help="Run with SSE transport instead of stdio")
    parser.add_argument("--host", default=None, help=f"SSE bind address (default: {_cfg.SSE_HOST})")
    parser.add_argument("--port", type=int, default=None, help=f"SSE port (default: {_cfg.SSE_PORT})")
    args = parser.parse_args()

    if args.sse:
        host = args.host or _cfg.SSE_HOST
        port = args.port or _cfg.SSE_PORT
        mcp.settings.host = host
        mcp.settings.port = port
        print(f"Starting NexHealth MCP server on http://{host}:{port}/sse", flush=True)
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
