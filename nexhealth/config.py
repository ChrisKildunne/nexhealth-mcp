BASE_URL    = "https://nexhealth.info"
API_VERSION = "v20240412"
USER_AGENT  = "NexHealth-MCP-Server/1.0 Mozilla/5.0 (compatible; MCP; Python)"

# Maps US state abbreviations to their primary IANA timezone identifier.
# Covers the majority timezone for each state. Split-timezone states are
# handled via CITY_TIMEZONE_OVERRIDES below; a warning is surfaced when a
# location is in a split-timezone state and the city isn't recognised.
STATE_TIMEZONES = {
    "AL": "America/Chicago",
    "AK": "America/Anchorage",
    "AZ": "America/Phoenix",
    "AR": "America/Chicago",
    "CA": "America/Los_Angeles",
    "CO": "America/Denver",
    "CT": "America/New_York",
    "DE": "America/New_York",
    "FL": "America/New_York",
    "GA": "America/New_York",
    "HI": "Pacific/Honolulu",
    "ID": "America/Boise",
    "IL": "America/Chicago",
    "IN": "America/Indiana/Indianapolis",
    "IA": "America/Chicago",
    "KS": "America/Chicago",
    "KY": "America/Kentucky/Louisville",
    "LA": "America/Chicago",
    "ME": "America/New_York",
    "MD": "America/New_York",
    "MA": "America/New_York",
    "MI": "America/Detroit",
    "MN": "America/Chicago",
    "MS": "America/Chicago",
    "MO": "America/Chicago",
    "MT": "America/Denver",
    "NE": "America/Chicago",
    "NV": "America/Los_Angeles",
    "NH": "America/New_York",
    "NJ": "America/New_York",
    "NM": "America/Denver",
    "NY": "America/New_York",
    "NC": "America/New_York",
    "ND": "America/Chicago",
    "OH": "America/New_York",
    "OK": "America/Chicago",
    "OR": "America/Los_Angeles",
    "PA": "America/New_York",
    "RI": "America/New_York",
    "SC": "America/New_York",
    "SD": "America/Chicago",
    "TN": "America/Chicago",
    "TX": "America/Chicago",
    "UT": "America/Denver",
    "VT": "America/New_York",
    "VA": "America/New_York",
    "WA": "America/Los_Angeles",
    "WV": "America/New_York",
    "WI": "America/Chicago",
    "WY": "America/Denver",
    "DC": "America/New_York",
    "PR": "America/Puerto_Rico",
    "VI": "America/St_Thomas",
    "GU": "Pacific/Guam",
    "AS": "Pacific/Pago_Pago",
    "MP": "Pacific/Saipan",
}

# City-level timezone overrides for states whose timezone varies by region.
# Keys are lowercase city names; values are the correct IANA timezone.
# Used by time_utils._tz_for_city() before falling back to the state default.
CITY_TIMEZONE_OVERRIDES: dict[str, str] = {
    # Tennessee — Eastern TN is America/New_York; the rest is America/Chicago
    "knoxville":     "America/New_York",
    "chattanooga":   "America/New_York",
    "oak ridge":     "America/New_York",
    "kingsport":     "America/New_York",
    "bristol":       "America/New_York",
    "johnson city":  "America/New_York",
    "morristown":    "America/New_York",
    "maryville":     "America/New_York",
    "greeneville":   "America/New_York",
    "newport":       "America/New_York",
    "harriman":      "America/New_York",
    # Idaho — Northern panhandle is America/Los_Angeles; the rest is America/Boise
    "coeur d'alene": "America/Los_Angeles",
    "coeur dalene":  "America/Los_Angeles",
    "moscow":        "America/Los_Angeles",
    "sandpoint":     "America/Los_Angeles",
    "lewiston":      "America/Los_Angeles",
    "post falls":    "America/Los_Angeles",
    "hayden":        "America/Los_Angeles",
    "rathdrum":      "America/Los_Angeles",
    "priest river":  "America/Los_Angeles",
}

# States that have more than one timezone — used to trigger a warning when
# the city isn't found in CITY_TIMEZONE_OVERRIDES so the builder is informed.
SPLIT_TIMEZONE_STATES: dict[str, str] = {
    "TN": "Eastern TN (Knoxville, Chattanooga) uses America/New_York; "
          "set timezone_override in config.yaml if your practice is there.",
    "ID": "Northern ID (Coeur d'Alene, Moscow, Lewiston) uses America/Los_Angeles; "
          "set timezone_override in config.yaml if your practice is there.",
    "IN": "Some Indiana border counties differ from America/Indiana/Indianapolis; "
          "set timezone_override in config.yaml if needed.",
}
