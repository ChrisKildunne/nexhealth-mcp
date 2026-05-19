# NexHealth MCP Server
Exposes the NexHealth API as MCP tools so Claude (or any MCP-compatible agent) can book appointments, manage patients, check availability, and guide developers through setup — conversationally, without writing any API code.

---

## Quickstart

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install the NexHealth MCP server
uv tool install git+https://github.com/ChrisKildunne/nexhealth-mcp.git

# 3. Run the setup wizard — stores your API key securely
nexhealth-mcp init

# 4. Add to Claude Desktop config (see below)

# 5. Restart Claude Desktop — done
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "nexhealth": {
      "command": "/Users/YOUR_USERNAME/nexhealth/nexhealth-mcp-start.sh",
      "args": []
    }
  }
}
```

Replace `YOUR_USERNAME` with your Mac username.

---

## Updating

To update to the latest version:
```bash
uv tool install git+https://github.com/ChrisKildunne/nexhealth-mcp.git --force
```

---

## API Key Storage

Your API key is stored securely in your system keychain — never in any file.

**Store via setup wizard (recommended):**
```bash
nexhealth-mcp setup
```

**Or via the macOS security CLI directly:**
```bash
security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_api_key_here"
```

Both methods store the key in the same place. The start script reads it automatically at runtime.

**Verify your key is stored:**
```bash
security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w
```

---

## For Developers (local setup)

```bash
git clone https://github.com/ChrisKildunne/nexhealth-mcp.git
cd nexhealth-mcp
uv sync
nexhealth-mcp init
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
list_institutions   → select_institution
list_locations      → select_location
search_patients     → find patient_id
list_providers      → find provider_id
get_available_slots → pick a slot (time + operatory_id)
book_appointment    → POST the appointment
get_appointment     → verify PMS sync status
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `NEXHEALTH_API_KEY` | Yes | Your NexHealth API key (overrides keychain if set) |
| `NEXHEALTH_SUBDOMAIN` | No | Skip institution selection; use this subdomain directly |
| `NEXHEALTH_TIMEZONE_OVERRIDE` | No | Override state-derived timezone (e.g. `America/New_York` for Eastern TN) |

---

## Troubleshooting

**`nexhealth-mcp` command not found after install**
Close and reopen your terminal — `uv tool install` adds the command to your PATH but the current session may not see it yet.

**SSL: CERTIFICATE_VERIFY_FAILED**
Your Python installation is missing macOS SSL certificates. Fix it:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
# or
pip install certifi
```

**Invalid Credentials (401)**
Verify your API key is stored and correct:
```bash
security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w
```
If wrong, re-run `nexhealth-mcp setup`.

**Claude doesn't see NexHealth tools**
Fully quit Claude Desktop (`Cmd+Q`) and relaunch. Check that `claude_desktop_config.json` points to the correct path.

---

## Documentation

| Doc | What's in it |
|---|---|
| [docs/setup.md](docs/setup.md) | Installation, Keychain setup, Claude Desktop config, SSE mode |
| [docs/usage.md](docs/usage.md) | Session model, all 20 tools, key behaviors |
| [docs/architecture.md](docs/architecture.md) | Package layout, how to add a new tool |
| [changes.md](changes.md) | Change history |
