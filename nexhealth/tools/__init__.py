# Import every tool module so their @mcp.tool() decorators fire at import time.
from nexhealth.tools import (  # noqa: F401
    institutions,
    locations,
    patients,
    providers,
    slots,
    appointments,
    operatories,
    working_hours,
    sync,
    content,
)
