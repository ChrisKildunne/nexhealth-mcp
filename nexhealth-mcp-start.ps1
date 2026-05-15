# NexHealth MCP Server — Windows start script for Claude Desktop.
#
# The API key is read automatically from Windows Credential Manager at runtime.
# To store your key: python -m nexhealth setup
#
# Optional env var overrides (uncomment and fill in to use):
# $env:NEXHEALTH_API_KEY = "your_key"          # skips Credential Manager lookup
# $env:NEXHEALTH_SUBDOMAIN = "your-subdomain"  # skips institution selection

$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) {
    Write-Error "python not found. Install Python 3.11+ and try again."
    exit 1
}

& $python "$env:USERPROFILE\Nexhealth\server.py"
