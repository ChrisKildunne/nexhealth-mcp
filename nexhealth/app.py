"""Creates the shared FastMCP instance. Import `mcp` from here everywhere."""
import os
from mcp.server.fastmcp import FastMCP

_system_prompt = os.environ.get("NEXHEALTH_SYSTEM_PROMPT", "").strip()
mcp = FastMCP("NexHealth", instructions=_system_prompt or None)
