from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .api import SikomClient
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    PROP_SWITCH_MODE,
    PROP_TEMP,
    PROP_TEMP_COMFORT,
    PROP_TEMP_ECO,
    SENSOR_PROPS,
)

_LOGGER = logging.getLogger(__name__)


class SikomDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        username: str,
        password: str,
        gateway_id: int,
        device_map: dict[str, list[int]],
        name_map: dict[str, dict[int, str]],
    ) -> None:
        self.config_entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self.client = SikomClient(hass, username, password)
        self.gateway_id = int(gateway_id)
        self.device_map = device_map
        self.name_map = name_map
        self._last_appview_ts: str | None = None

    def _all_device_ids(self) -> set[int]:
        ids: set[int] = set()
        for k in ("climate", "switch", "sensor"):
            for did in self.device_map.get(k, []):
                try:
                    ids.add(int(did))
                except (TypeError, ValueError):
                    continue
        return ids

    def _normalize_appview(self, res: Any) -> dict[str, Any]:
        """
        Sikom API kan komme i ulike 'wrappers':
        - Noen klienter returnerer direkte bpapi_result (med keys: controller, devices)
        - Andre returnerer hele payloaden (med Data/bpapi_result)
        Denne gjør det robust.
        """
        if not isinstance(res, dict):
            return {}

        # Case A: allerede normalisert
        if "devices" in res or "controller" in res:
            return res

        # Case B: wrapper med Data -> bpapi_result
        data = res.get("Data")
        if isinstance(data, dict):
            bp = data.get("bpapi_result")
            if isinstance(bp, dict):
                return bp

        # Case C: wrapper med bpapi_result direkte
        bp = res.get("bpapi_result")
        if isinstance(bp, dict):
            return bp

        return {}

    async def _async_update_data(self) -> dict[str, Any]:
        wanted_ids = self._all_device_ids()
        new_props: dict[tuple[int, str], Any] = {}

        # Default: ukjent/ikke satt
        controller_online: str | None = None

        res_raw = await self.client.get_appview_v4(self.gateway_id)
        res = self._normalize_appview(res_raw)

        # controller.online
        controller = res.get("controller")
        if isinstance(controller, dict):
            online_val = controller.get("online")
            if online_val is not None:
                controller_online = str(online_val)

        devices = res.get("devices")
        if isinstance(devices, list):
            for dev in devices:
                if not isinstance(dev, dict):
                    continue

                did_raw = dev.get("bpapi_device_id")
                try:
                    did = int(did_raw)
                except (TypeError, ValueError):
                    continue

                if did not in wanted_ids:
                    continue

                # Termostat/switch
                for key in (PROP_SWITCH_MODE, PROP_TEMP, PROP_TEMP_ECO, PROP_TEMP_COMFORT, "temperature"):
                    if key in dev:
                        new_props[(did, key)] = dev.get(key)

                # Sensor props (AMS m.m.)
                for key in SENSOR_PROPS:
                    if key in dev:
                        new_props[(did, key)] = dev.get(key)

        self._last_appview_ts = dt_util.utcnow().replace(microsecond=0).isoformat()

        return {
            "props": new_props,
            "_appview_heartbeat": self._last_appview_ts,
            "_controller_online": controller_online,  # "1"/"0" (eller None hvis ikke funnet)
        }
