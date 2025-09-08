from __future__ import annotations
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_CLIMATE_IDS, 
    CONF_SWITCH_IDS, CONF_SENSOR_IDS
)
from .coordinator import SikomDataCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["climate", "switch", "sensor", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sett opp Sikom fra en config entry."""
    merged_options: Dict[str, Any] = {**entry.data, **entry.options}

    device_map = {
        "climate": list(merged_options.get(CONF_CLIMATE_IDS, {}).keys()),
        "switch": list(merged_options.get(CONF_SWITCH_IDS, {}).keys()),
        "sensor": list(merged_options.get(CONF_SENSOR_IDS, {}).keys()),
    }
    name_map = {
        "climate": merged_options.get(CONF_CLIMATE_IDS, {}),
        "switch": merged_options.get(CONF_SWITCH_IDS, {}),
        "sensor": merged_options.get(CONF_SENSOR_IDS, {}),
    }

    coordinator = SikomDataCoordinator(
        hass=hass,
        entry=entry,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        device_map=device_map,
        name_map=name_map,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjern Sikom-integrasjonen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Last inn config entry på nytt når options endres."""
    await hass.config_entries.async_reload(entry.entry_id)
