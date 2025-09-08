from __future__ import annotations

DOMAIN = "sikom"

# Polling-interval (sekunder). 60 gir rask toveis synk.
DEFAULT_SCAN_INTERVAL = 60

# Config keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

CONF_CLIMATE_IDS = "climate_ids"
CONF_SWITCH_IDS = "switch_ids"
CONF_SENSOR_IDS = "sensor_ids"

# "id:name" alias-kart
CONF_CLIMATE_NAMES = "climate_names"
CONF_SWITCH_NAMES = "switch_names"
CONF_SENSOR_NAMES = "sensor_names"

# Sikom property names
PROP_SWITCH_MODE = "switch_mode"
PROP_TEMP = "temperature"
PROP_TEMP_COMFORT = "temperature_comfort"
PROP_TEMP_ECO = "temperature_eco"

# Default fallbacks hvis API ikke gir settpunkt
DEFAULT_ECO_TEMP = 10.0
DEFAULT_COMFORT_TEMP = 21.0

# ******** OPPDATERT LISTE MED KORREKTE NAVN ********
# Hvilke strømmåler-verdier vi prøver å hente
SENSOR_PROPS = [
    # Generiske navn
    "current_power_usage",
    "power_voltage",
    "current",
    "energy",

    # AMS-spesifikke navn
    "ams_current_power_usage",
    "ams_cumulative_imported_energy",
    "ams_cumulative_plus_calculated_energy_today",
    "ams_power_voltage",
    "ams_i1",
    "ams_i2",
    "ams_i3",
]