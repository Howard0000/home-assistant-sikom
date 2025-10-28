from __future__ import annotations
import asyncio
import time
from datetime import timedelta
from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, DEFAULT_SCAN_INTERVAL, PROP_TEMP, PROP_TEMP_COMFORT,
    PROP_TEMP_ECO, PROP_SWITCH_MODE, SENSOR_PROPS
)
from .api import SikomClient

_LOGGER = logging.getLogger(__name__)

class SikomDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, username: str, password: str,
                 device_map: dict[str, list[int]], name_map: dict[str, dict[int, str]]):
        self.config_entry = entry
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )
        self.client = SikomClient(hass, username, password)
        self.device_map = device_map
        self.name_map = name_map

        # AppView-refresh bokføring
        self._last_appview_refresh = 0.0
        self._gateway_ids: set[int] | None = None
        self._last_appview_ts: str | None = None  # oppdateres KUN når nudge kjøres

    async def _async_update_data(self) -> dict[str, Any]:
        """Hent data for alle enheter parallelt."""
        # --- AppView "nudge" hver ~5.5 min ---
        now_monotonic = time.monotonic()
        if now_monotonic - self._last_appview_refresh >= 330:
            if self._gateway_ids is None:
                try:
                    devices = await self.client.list_devices()
                    self._gateway_ids = {
                        int(d["gateway_id"])
                        for d in devices
                        if d.get("gateway_id") is not None
                    }
                    _LOGGER.debug("Discovered gateway IDs for AppView refresh: %s", self._gateway_ids)
                except Exception as e:
                    _LOGGER.warning("Could not list devices to find gateway IDs for refresh: %s", e)
                    self._gateway_ids = set()

            if self._gateway_ids:
                results = await asyncio.gather(
                    *[self.client.async_refresh_appview(gid) for gid in self._gateway_ids],
                    return_exceptions=True
                )
                for gid, res in zip(self._gateway_ids, results):
                    if isinstance(res, Exception):
                        _LOGGER.warning("Failed to trigger AppView refresh for gateway %s: %s", gid, res)

            self._last_appview_refresh = now_monotonic
            # Sett heartbeat når vi faktisk har forsøkt nudge
            self._last_appview_ts = dt_util.utcnow().replace(microsecond=0).isoformat()

        # --- Pull av properties ---
        props_to_fetch = set()
        new_props: dict[tuple[int, str], Any] = {}

        all_device_ids = set()
        for device_type in self.device_map:
            for device_id in self.device_map[device_type]:
                all_device_ids.add(device_id)

        # climate
        for did in self.device_map.get("climate", []):
            props_to_fetch.update([
                (did, PROP_TEMP), (did, PROP_TEMP_COMFORT),
                (did, PROP_TEMP_ECO), (did, PROP_SWITCH_MODE)
            ])

        # switch (relé): HENT OGSÅ TEMPERATUR
        for did in self.device_map.get("switch", []):
            props_to_fetch.add((did, PROP_SWITCH_MODE))
            props_to_fetch.add((did, "temperature"))  # <--- NY

        # sensor (AMS)
        for did in self.device_map.get("sensor", []):
            for p in SENSOR_PROPS:
                props_to_fetch.add((did, p))

        # connection for alle
        for did in all_device_ids:
            props_to_fetch.add((did, "connection"))

        tasks = {(did, prop): self.client.get_property_value(did, prop) for did, prop in props_to_fetch}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for (did, prop), result in zip(tasks.keys(), results):
            if not isinstance(result, Exception) and result is not None:
                new_props[(did, prop)] = result

        # Inkluder AppView-heartbeat i datasettet (oppdateres kun ved nudge)
        data: dict[str, Any] = {"props": new_props}
        data["_appview_heartbeat"] = self._last_appview_ts
        return data
