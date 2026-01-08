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

# Device properties (fra Sikom/AppView)
PROP_SWITCH_MODE = "switch_mode"          # "0"/"1"
PROP_TEMP = "temperature"                # aktuell temp eller settpunkt (avhengig av device)
PROP_TEMP_ECO = "temperature_eco"        # eco-settpunkt
PROP_TEMP_COMFORT = "temperature_comfort"  # comfort-settpunkt

# Default fallback-settpunkter hvis Sikom ikke gir verdier (brukes i climate.py)
DEFAULT_ECO_TEMP = 16.0
DEFAULT_COMFORT_TEMP = 21.0

# Sensorfelter vi ønsker å hente ut hvis de finnes på enheter (typisk AMS/ECO-AMS osv.)
SENSOR_PROPS: list[str] = [
    # Generiske navn
    "current_power_usage",
    "power_voltage",
    "current",
    "energy",

    # AMS-spesifikke navn (ECO-AMS)
    "ams_current_power_usage",
    "ams_cumulative_imported_energy",
    "ams_cumulative_plus_calculated_energy_today",
    "ams_power_voltage",
    "ams_i1",
    "ams_i2",
    "ams_i3",
]
