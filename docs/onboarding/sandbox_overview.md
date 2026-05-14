## NexHealth Sandbox Setup — Overview

Welcome! The NexHealth sandbox is a pre-populated test environment that lets
you explore and test the API without affecting any real patients or practices.

There are two levels of sandbox setup depending on what you want to test:

---

### Level 1 — API Only (no EHR required)
The sandbox comes pre-populated with test institutions, locations, providers,
operatories, and patients. You can make API calls immediately — no PMS or EHR
setup needed. This is the fastest way to get started.

Steps:
  1. dev_portal         — Create your developer account and get your sandbox API key
  2. api_key            — Store your API key securely
  3. sandbox_first_call — Make your first API call and verify everything works

---

### Level 2 — Full End-to-End (sandbox + live Open Dental test instance)
If you want to verify that appointments created through the API actually appear
in a real EHR, you can connect a live Open Dental test instance to your sandbox
environment. This gives you full end-to-end visibility.

This is optional — you can always start with Level 1 and add this later.

Steps (after completing Level 1):
  1. In your developer portal, go to Institutions and click "Create new sync"
  2. Select Open Dental as the system you are syncing with
  3. Note your product key — you will need it to install the synchronizer
  4. Install Open Dental and the NexHealth synchronizer:
     - Mac users: install Parallels first (vm_setup), then Open Dental inside
       the Windows VM (open_dental), then the synchronizer (synchronizer)
     - Windows users: install Open Dental directly (open_dental), then the
       synchronizer (synchronizer)

Ask me about any section by name or say "walk me through sandbox setup" to go
step by step.