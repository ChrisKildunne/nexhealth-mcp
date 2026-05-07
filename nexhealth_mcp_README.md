# NexHealth MCP Server

Exposes the NexHealth API as MCP tools so Claude can book appointments, search patients, check availability, and more — conversationally.

---

## Prerequisites

```bash
pip install "mcp[cli]"
```

Python 3.10+ recommended.

---

## Environment Variables

Set these before running the server:

| Variable | Description |
|---|---|
| `NEXHEALTH_API_KEY` | Your NexHealth API key (from the NexHealth dashboard) |
| `NEXHEALTH_SUBDOMAIN` | Your institution subdomain (e.g. `nexhealthsmiles`) |

```bash
export NEXHEALTH_API_KEY="your_api_key_here"
export NEXHEALTH_SUBDOMAIN="yoursubdomain"
```

---

## Running the Server

### Option A — stdio (Claude Desktop / local MCP clients)

```bash
python nexhealth_mcp_server.py
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nexhealth": {
      "command": "python",
      "args": ["/absolute/path/to/nexhealth_mcp_server.py"],
      "env": {
        "NEXHEALTH_API_KEY": "your_api_key_here",
        "NEXHEALTH_SUBDOMAIN": "yoursubdomain"
      }
    }
  }
}
```

### Option B — SSE/HTTP (hosted, Claude.ai MCP connector)

```bash
python nexhealth_mcp_server.py --sse --port 8080
```

Then register `http://yourserver:8080/sse` as the MCP server URL in Claude.ai settings.

---

## Available Tools

| Tool | What it does |
|---|---|
| `list_locations` | List all practice locations for your institution |
| `search_patients` | Search patients by name within a location |
| `get_patient` | Fetch a single patient by ID |
| `list_providers` | List all active providers at a location |
| `list_appointment_types` | List appointment types (cleaning, exam, etc.) |
| `get_available_slots` | Find open appointment slots for a provider |
| `book_appointment` | Create (POST) a new appointment |
| `get_appointment` | Fetch a single appointment by ID |
| `list_appointments` | List appointments in a date range |
| `cancel_appointment` | Cancel an existing appointment |
| `list_operatories` | List rooms/chairs at a location |

---

## Typical Booking Flow (what Claude does automatically)

```
1. list_locations          → pick a location_id
2. search_patients         → find patient_id
3. list_providers          → pick provider_id
4. list_appointment_types  → pick appointment_type_id (optional)
5. get_available_slots     → pick a slot (gives time + operatory_id)
6. book_appointment        → POST the appointment
```

---

## Authentication Notes

- The server calls `POST /authenticates` once on startup using your API key, caches the bearer token for the session, and automatically attaches it to every subsequent request.
- If the token expires (NexHealth tokens are short-lived), restart the server to re-authenticate.
- The `subdomain` query parameter is injected automatically into every request — you never need to pass it to the tools.
