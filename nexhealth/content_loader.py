"""
Loads onboarding and workflow markdown files from disk at import time.
Content authors can update any .md file without touching Python code.
"""
import os

_PKG_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_PKG_DIR)   # ~/Nexhealth/

ONBOARDING_DIR = os.path.join(_PROJECT_DIR, "docs", "onboarding")
WORKFLOW_DIR   = os.path.join(_PROJECT_DIR, "docs", "workflows")


def _load_dir(directory: str) -> dict:
    """Read all .md files in directory and return {stem: content} dict."""
    sections = {}
    if not os.path.isdir(directory):
        return sections
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".md"):
            continue
        key = filename[:-3]
        try:
            with open(os.path.join(directory, filename), encoding="utf-8") as f:
                sections[key] = f.read().strip()
        except Exception as e:
            sections[key] = f"[Could not load {filename}: {e}]"
    return sections


def _build_guide(sections: dict, keys: list) -> str:
    parts = [
        sections.get(k, f"[Section '{k}' not found — check onboarding/ directory]")
        for k in keys
    ]
    return "\n\n---\n\n".join(parts)


ONBOARDING = _load_dir(ONBOARDING_DIR)
WORKFLOWS  = _load_dir(WORKFLOW_DIR)

_SANDBOX_KEYS    = ["sandbox_overview", "dev_portal", "api_key", "sandbox_first_call"]
_PRODUCTION_KEYS = [
    "production_overview", "production_institution",
    "production_datasource", "production_api_key", "production_first_call",
]

SANDBOX_GUIDE    = "## NexHealth Sandbox Setup — Full Guide\n\n"    + _build_guide(ONBOARDING, _SANDBOX_KEYS)
PRODUCTION_GUIDE = "## NexHealth Production Setup — Full Guide\n\n" + _build_guide(ONBOARDING, _PRODUCTION_KEYS)
