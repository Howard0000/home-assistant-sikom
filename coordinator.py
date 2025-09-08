from __future__ import annotations
import asyncio
from datetime import timedelta
from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry  # Importer ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN, DEFAULT_SCAN_INTERVAL, PROP_TEMP, PROP_TEMP_COMFORT,
    PROP_TEMP_ECO, PROP_SWITCH_MODE, SENSOR_PROPS
)
from .api import SikomClient

_LOGGER = logging.getLogger(__name__)

class SikomDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, username: str, password: str,
                 device_map: dict[str, list[int]], name_map: dict[str, dict[int, str]]):
        
        # ******** DEN MANGLENDE LINJEN ER HER ********
        self.config_entry = entry
        # *********************************************

        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.client = SikomClient(hass, username, password)
        self.device_map = device_map
        self.name_map = name_map

    async def _async_update_data(self) -> dict[str, Any]:
        """Hent data for alle enheter parallelt."""
        props_to_fetch = set()
        new_props = {}

        # Finn alle unike enhets-IDer fra alle kategorier
        all_device_ids = set()
        for device_type in self.device_map:
            for device_id in self.device_map[device_type]:
                all_device_ids.add(device_id)

        # Legg til properties for hver enhetstype
        for did in self.device_map.get("climate", []):
            props_to_fetch.update([(did, PROP_TEMP), (did, PROP_TEMP_COMFORT), (did, PROP_TEMP_ECO), (did, PROP_SWITCH_MODE)])
        for did in self.device_map.get("switch", []):
            props_to_fetch.add((did, PROP_SWITCH_MODE))
        for did in self.device_map.get("sensor", []):
            for p in SENSOR_PROPS:
                props_to_fetch.add((did, p))

        # --- START PÅ NYTT TILLEGG ---
        # Legg til "connection"-sjekk for ALLE enheter
        for did in all_device_ids:
            props_to_fetch.add((did, "connection"))
        # --- SLUTT PÅ NYTT TILLEGG ---

        tasks = { (did, prop): self.client.get_property_value(did, prop) for did, prop in props_to_fetch }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for (did, prop), result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                _LOGGER.debug("Kunne ikke hente %s for enhet %s: %s", prop, did, result)
            elif result is not None:
                new_props[(did, prop)] = result
        
        return {"props": new_props}