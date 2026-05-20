import json

from nexhealth.app import mcp
from nexhealth.content_loader import (
    ONBOARDING, WORKFLOWS, WORKFLOW_DIR,
    SANDBOX_GUIDE, PRODUCTION_GUIDE,
)
from nexhealth.tools._decorator import _tool

_WORKFLOW_ALIASES = {
    # book appointment
    "book":                        "book_appointment",
    "booking":                     "book_appointment",
    "schedule":                    "book_appointment",
    "book appointment":            "book_appointment",
    "book_appointment":            "book_appointment",
    # create patient
    "create patient":              "create_patient",
    "create_patient":              "create_patient",
    "new patient":                 "create_patient",
    "add patient":                 "create_patient",
    # working hours
    "working hour":                "create_working_hour",
    "working hours":               "create_working_hour",
    "create_working_hour":         "create_working_hour",
    "availability":                "create_working_hour",
    # appointment types
    "appointment type":            "create_appointment_type",
    "appointment types":           "create_appointment_type",
    "create appointment type":     "create_appointment_type",
    "create_appointment_type":     "create_appointment_type",
    "descriptors":                 "create_appointment_type",
    "procedure codes":             "create_appointment_type",
    # patch / update appointment
    "patch":                       "patch_appointment",
    "patch appointment":           "patch_appointment",
    "patch_appointment":           "patch_appointment",
    "confirm":                     "patch_appointment",
    "cancel":                      "patch_appointment",
    "reschedule":                  "patch_appointment",
    "check in":                    "patch_appointment",
    "checkin":                     "patch_appointment",
    # session setup
    "session":                     "session_setup",
    "session setup":               "session_setup",
    "session_setup":               "session_setup",
    "setup":                       "session_setup",
    "get started":                 "session_setup",
    # troubleshooting
    "troubleshoot":                "troubleshoot",
    "error":                       "troubleshoot",
    "debug":                       "troubleshoot",
    "help":                        "troubleshoot",
}


@mcp.tool()
@_tool
def get_started(section: str = None, mode: str = None) -> str:
    """
    Developer onboarding guide for the NexHealth MCP server.

    Supports both sandbox and production setup flows. Always ask the developer
    which mode they want before calling this tool.

    Call with no arguments to get a prompt asking which mode the developer wants.
    Call with mode="sandbox" or mode="production" for the full guide for that mode.
    Call with a specific section name to get guidance on that step only.

    Args:
        mode:    (Optional) "sandbox" or "production". Returns the full guide
                 for that mode when no section is specified.
        section: (Optional) A specific section to return. Sandbox sections:
                   "sandbox_overview"      — High-level summary of sandbox steps
                   "dev_portal"            — Create developer account and sandbox API key
                   "vm_setup"              — Mac users: install Parallels Windows VM
                   "open_dental"           — Install Open Dental demo EHR
                   "synchronizer"          — Install the NexHealth synchronizer
                   "api_key"               — Store API key securely in Mac keychain
                   "sandbox_first_call"    — Make first sandbox API call end-to-end
                 Production sections:
                   "production_overview"      — High-level summary of production steps
                   "production_institution"   — Create a production institution
                   "production_datasource"    — Connect Open Dental as a datasource
                   "production_api_key"       — Generate and store production API key
                   "production_first_call"    — Make first production API call

    If neither argument is provided, returns an overview of both modes and asks
    the developer which they want to proceed with.
    """
    if section:
        section = section.strip().lower()
        if section not in ONBOARDING:
            valid = ", ".join(f'"{s}"' for s in ONBOARDING)
            return f"Section '{section}' not found. Available sections: {valid}."
        return ONBOARDING[section]

    if mode:
        mode = mode.strip().lower()
        if mode == "sandbox":
            return SANDBOX_GUIDE
        if mode == "production":
            return PRODUCTION_GUIDE
        return f"Mode '{mode}' not recognised. Use mode='sandbox' or mode='production'."

    return """
## NexHealth Developer Setup

Welcome! Before we get started, are you setting up a sandbox (test) environment
or a production environment?

  - Sandbox    — Uses test data pre-populated by NexHealth. Recommended for
                 first-time setup and integration testing. No real patient data.

  - Production — Connects to a live Open Dental instance and real practice data.
                 Requires a production institution to be configured first.

Please tell me which you'd like to set up and I'll walk you through it step by step.
"""


@mcp.tool()
@_tool
def get_workflow(task: str = None) -> str:
    """
    Return step-by-step workflow guidance for a specific task.
    Claude should call this proactively before executing any multi-step operation
    to ensure tools are called in the correct order with the right validations.

    Call with no arguments to see all available workflows.
    Call with a task name or natural-language description to get that workflow.

    Args:
        task: The task or workflow to retrieve. Accepts natural language or exact names.
              Examples: "book appointment", "create patient", "working hours",
              "appointment type", "patch", "cancel", "session setup", "troubleshoot"

    Available workflows:
        "book_appointment"        — Full booking flow: patient → provider → slots → confirm → book
        "create_patient"          — Create a new patient with duplicate checking
        "create_working_hour"     — Set up provider availability (recurring, one-off, or custom)
        "create_appointment_type" — Create appointment types and associate descriptors
        "patch_appointment"       — Confirm, cancel, check in, or reschedule an appointment
        "session_setup"           — Establish institution and location at session start
        "troubleshoot"            — Error code reference and debugging steps

    When to call this tool:
        - At the start of any booking, creation, or update operation
        - When an error is returned and you need to diagnose it
        - When the user asks "how do I..." for any supported task
        - When you are unsure of the correct tool sequence for a task
    """
    if not WORKFLOWS:
        return json.dumps({
            "error":   True,
            "message": (
                f"Workflow directory not found at {WORKFLOW_DIR}. "
                "Ensure the workflows/ folder exists next to server.py."
            ),
        }, indent=2)

    if not task:
        return json.dumps({
            "message":             "Available workflows — call get_workflow(task='...') for any of these:",
            "available_workflows": sorted(WORKFLOWS.keys()),
            "tip":                 "You can also use natural language e.g. get_workflow('book appointment')",
        }, indent=2)

    key = _WORKFLOW_ALIASES.get(task.strip().lower()) or task.strip().lower()

    if key not in WORKFLOWS:
        matches = [k for k in WORKFLOWS if task.lower() in k or k in task.lower()]
        if len(matches) == 1:
            key = matches[0]
        elif len(matches) > 1:
            return json.dumps({
                "message": f"Multiple workflows match '{task}'. Please be more specific:",
                "matches": matches,
            }, indent=2)
        else:
            return json.dumps({
                "error":     True,
                "message":   f"No workflow found for '{task}'.",
                "available": sorted(WORKFLOWS.keys()),
            }, indent=2)

    return WORKFLOWS[key]
