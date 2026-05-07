#!/bin/bash
# =============================================================================
# NexHealth MCP Server — Setup Script
# =============================================================================
# Usage: curl -sSL https://raw.githubusercontent.com/ChrisKildunne/nexhealth-mcp/main/setup.sh | bash

GITHUB_RAW="https://raw.githubusercontent.com/ChrisKildunne/nexhealth-mcp/main"
INSTALL_DIR="$HOME/Nexhealth"
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
print_step()  { echo -e "\n${BLUE}▶ $1${NC}"; }
print_ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
print_warn()  { echo -e "  ${YELLOW}⚠${NC}  $1"; }
print_error() { echo -e "  ${RED}✗${NC} $1"; }

download() {
    local url="$1" dest="$2"
    if curl -sSL --fail "$url" -o "$dest" 2>/dev/null; then
        print_ok "$(basename $dest)"
    else
        print_error "Failed to download $(basename $dest)"
        exit 1
    fi
}

# Re-attach stdin to the terminal so read prompts work when piped through curl
exec < /dev/tty

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       NexHealth MCP Server Setup         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "This script will:"
echo "  • Create ~/Nexhealth/ with all required files"
echo "  • Set up the Claude Desktop config"
echo "  • Make the start script executable"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Check dependencies
print_step "Checking dependencies"

if ! command -v python3 &>/dev/null; then
    print_error "Python 3 is not installed. Install from https://python.org and re-run."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ required. You have Python $PYTHON_VERSION."
    exit 1
fi
print_ok "Python $PYTHON_VERSION"

PYTHON_BIN=$(which python3)
PIP_BIN=$(which pip3)
print_ok "Python path: $PYTHON_BIN"

# Step 2: Install MCP
print_step "Installing MCP Python package"
if $PYTHON_BIN -c "import mcp" &>/dev/null; then
    print_ok "mcp already installed"
else
    echo "  Installing mcp[cli]..."
    $PIP_BIN install "mcp[cli]" --quiet && print_ok "mcp[cli] installed" || { print_error "Failed to install mcp[cli]"; exit 1; }
fi

# Step 3: Create folders
print_step "Creating folder structure"
mkdir -p "$INSTALL_DIR" "$INSTALL_DIR/onboarding" "$INSTALL_DIR/workflows"
print_ok "$INSTALL_DIR/"
print_ok "$INSTALL_DIR/onboarding/"
print_ok "$INSTALL_DIR/workflows/"

# Step 4: Root files
print_step "Downloading server files"
download "$GITHUB_RAW/nexhealth_mcp_server.py"    "$INSTALL_DIR/nexhealth_mcp_server.py"
download "$GITHUB_RAW/nexhealth_system_prompt.txt" "$INSTALL_DIR/nexhealth_system_prompt.txt"
download "$GITHUB_RAW/nexhealth_mcp_README.md"     "$INSTALL_DIR/nexhealth_mcp_README.md"

# Step 5: Workflow files
print_step "Downloading workflow files"
for file in book_appointment.md create_patient.md create_working_hour.md patch_appointment.md session_setup.md troubleshoot.md; do
    download "$GITHUB_RAW/workflows/$file" "$INSTALL_DIR/workflows/$file"
done

# Step 6: Onboarding files
print_step "Downloading onboarding files"
for file in sandbox_overview.md dev_portal.md vm_setup.md open_dental.md synchronizer.md api_key.md sandbox_first_call.md production_overview.md production_institution.md production_datasource.md production_api_key.md production_first_call.md; do
    download "$GITHUB_RAW/onboarding/$file" "$INSTALL_DIR/onboarding/$file"
done

# Step 7: Start script
print_step "Creating start script"
cat > "$INSTALL_DIR/nexhealth-mcp-start.sh" << STARTSCRIPT
#!/bin/bash
export NEXHEALTH_API_KEY=\$(security find-generic-password -a "\$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null)

if [ -z "\$NEXHEALTH_API_KEY" ]; then
    echo "ERROR: NEXHEALTH_API_KEY not found in keychain."
    echo "Run: security add-generic-password -a \"\\\$USER\" -s \"NEXHEALTH_API_KEY\" -w \"your_api_key_here\""
    exit 1
fi

export NEXHEALTH_SYSTEM_PROMPT=\$(cat "\$HOME/Nexhealth/nexhealth_system_prompt.txt" 2>/dev/null)
exec ${PYTHON_BIN} "\$HOME/Nexhealth/nexhealth_mcp_server.py"
STARTSCRIPT

chmod +x "$INSTALL_DIR/nexhealth-mcp-start.sh"
print_ok "nexhealth-mcp-start.sh created (using $PYTHON_BIN)"

# Step 8: API key — works correctly when piped through curl
print_step "API Key Setup"
echo ""
echo "  You need a NexHealth API key."
echo "  If you don't have one yet, sign up at: https://developers.nexhealth.com/signup"
echo ""

# Check if key already exists in keychain
EXISTING_KEY=$(security find-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w 2>/dev/null || echo "")
if [ -n "$EXISTING_KEY" ]; then
    print_ok "API key already found in keychain — keeping it."
else
    read -p "  Paste your API key and press Enter: " API_KEY
    echo ""
    if [ -z "$API_KEY" ]; then
        print_warn "No key entered. Add it later with:"
        echo '         security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "your_key_here"'
    else
        security delete-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" &>/dev/null || true
        security add-generic-password -a "$USER" -s "NEXHEALTH_API_KEY" -w "$API_KEY"
        print_ok "API key stored securely in macOS keychain"
    fi
fi

# Step 9: Claude Desktop config
print_step "Configuring Claude Desktop"
mkdir -p "$CLAUDE_CONFIG_DIR"

if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    if grep -q "nexhealth" "$CLAUDE_CONFIG_FILE" 2>/dev/null; then
        print_ok "NexHealth already in claude_desktop_config.json — no changes needed."
    else
        # Config exists but no nexhealth entry — add it alongside existing servers
        cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup"
        print_ok "Backed up existing config to claude_desktop_config.json.backup"
        # Extract existing mcpServers content and merge
        cat > "$CLAUDE_CONFIG_FILE" << CLAUDECONFIG
{
  "mcpServers": {
    "nexhealth": {
      "command": "${INSTALL_DIR}/nexhealth-mcp-start.sh",
      "args": []
    }
  }
}
CLAUDECONFIG
        print_ok "claude_desktop_config.json updated with NexHealth entry"
    fi
else
    # No config file at all — create it fresh
    cat > "$CLAUDE_CONFIG_FILE" << CLAUDECONFIG
{
  "mcpServers": {
    "nexhealth": {
      "command": "${INSTALL_DIR}/nexhealth-mcp-start.sh",
      "args": []
    }
  }
}
CLAUDECONFIG
    print_ok "claude_desktop_config.json created"
fi

# Step 10: Verify
print_step "Verifying installation"
ALL_GOOD=true
for f in \
    "$INSTALL_DIR/nexhealth_mcp_server.py" \
    "$INSTALL_DIR/nexhealth_system_prompt.txt" \
    "$INSTALL_DIR/nexhealth-mcp-start.sh" \
    "$INSTALL_DIR/workflows/book_appointment.md" \
    "$INSTALL_DIR/workflows/create_patient.md" \
    "$INSTALL_DIR/workflows/create_working_hour.md" \
    "$INSTALL_DIR/workflows/patch_appointment.md" \
    "$INSTALL_DIR/workflows/session_setup.md" \
    "$INSTALL_DIR/workflows/troubleshoot.md" \
    "$INSTALL_DIR/onboarding/sandbox_overview.md" \
    "$INSTALL_DIR/onboarding/dev_portal.md" \
    "$INSTALL_DIR/onboarding/vm_setup.md" \
    "$INSTALL_DIR/onboarding/open_dental.md" \
    "$INSTALL_DIR/onboarding/synchronizer.md" \
    "$INSTALL_DIR/onboarding/api_key.md" \
    "$INSTALL_DIR/onboarding/sandbox_first_call.md" \
    "$INSTALL_DIR/onboarding/production_overview.md" \
    "$INSTALL_DIR/onboarding/production_institution.md" \
    "$INSTALL_DIR/onboarding/production_datasource.md" \
    "$INSTALL_DIR/onboarding/production_api_key.md" \
    "$INSTALL_DIR/onboarding/production_first_call.md"
do
    if [ -f "$f" ]; then
        print_ok "$(echo $f | sed "s|$INSTALL_DIR/||")"
    else
        print_error "MISSING: $(echo $f | sed "s|$INSTALL_DIR/||")"
        ALL_GOOD=false
    fi
done

echo ""
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Setup complete! 🎉              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Next steps:"
    echo "  1. Fully quit Claude Desktop (Cmd+Q)"
    echo "  2. Relaunch Claude Desktop"
    echo '  3. Ask Claude: "Can you check the current session status?"'
    echo ""
else
    echo -e "${RED}Setup completed with errors. Check items marked ✗ above.${NC}"
    echo "Try re-running this script or contact support."
fi
