# NexHealth MCP Server

Exposes the NexHealth API as MCP tools so Claude (or any MCP-compatible agent) can book appointments, manage patients, check availability, and guide developers through setup — conversationally, without writing any API code.

---

## Quickstart (recommended — no manual venv needed)

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Store your API key in the macOS Keychain
security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_api_key_here"

# 3. Point Claude Desktop at the start script (see below)
# 4. Restart Claude Desktop — done
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nexhealth": {
      "command": "/Users/YOUR_USERNAME/Nexhealth/nexhealth-mcp-start.sh",
      "args": []
    }
  }
}
```

Full setup walkthrough: **[docs/setup.md](docs/setup.md)**

---

## Alternative install (uv tool)

```bash
# Install from this repo as a local uv tool
uv tool install .

# Run directly
nexhealth-mcp

# Or without installing
uv run nexhealth-mcp
```

---

## Manual install (pip)

```bash
pip install -r requirements.txt
python server.py
```

---

## Tools (20 total)

**Onboarding guidance** — `get_started`, `get_workflow`

**Session setup** — `list_institutions`, `select_institution`, `current_session`

**Locations** — `list_locations`, `select_location`

**Patients** — `search_patients`, `get_patient`, `create_patient`

**Providers** — `list_providers`, `list_appointment_types`

**Availability** — `get_available_slots`

**Appointments** — `book_appointment`, `get_appointment`, `list_appointments`, `cancel_appointment`, `patch_appointment`

**Operatories** — `list_operatories`

**Working hours** — `create_working_hour`

---

## Booking flow (what Claude does automatically)

```
list_institutions  → select_institution
list_locations     → select_location
search_patients    → find patient_id
list_providers     → find provider_id
get_available_slots → pick a slot (time + operatory_id)
book_appointment   → POST the appointment
get_appointment    → verify PMS sync status
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `NEXHEALTH_API_KEY` | Yes | Your NexHealth API key |
| `NEXHEALTH_SUBDOMAIN` | No | Skip institution selection; use this subdomain directly |
| `NEXHEALTH_TIMEZONE_OVERRIDE` | No | Override state-derived timezone (e.g. `America/New_York` for Eastern TN) |

---

## Documentation

| Doc | What's in it |
|---|---|
| [docs/setup.md](docs/setup.md) | Installation, Keychain setup, Claude Desktop config, SSE mode |
| [docs/usage.md](docs/usage.md) | Session model, all 20 tools, key behaviors |
| [docs/architecture.md](docs/architecture.md) | Package layout, how to add a new tool |
| [changes.md](changes.md) | Change history |
