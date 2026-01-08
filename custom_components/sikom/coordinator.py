from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SikomClient
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    PROP_SWITCH_MODE,
    PROP_TEMP,
    PROP_TEMP_ECO,
    PROP_TEMP_COMFORT,
    SENSOR_PROPS,
)

_LOGGER = logging.getLogger(__name__)


class SikomDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Henter og normaliserer data fra Sikom AppView v4."""

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
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{gateway_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Hent data fra Sikom og normaliser props."""
        try:
            # NB: get_appview_v4() returnerer allerede "bpapi_result"
            av4 = await self.client.get_appview_v4(self.gateway_id)
        except Exception as exc:  # noqa: BLE001
            raise UpdateFailed(f"Sikom AppView feilet: {exc}") from exc

        if not isinstance(av4, dict):
            raise UpdateFailed("Sikom AppView returnerte ingen data (None/ugyldig)")

        controller = av4.get("controller") or {}
        devices = av4.get("devices") or []

        wanted_ids = self._all_device_ids()

        # Controller online-status (string "1"/"0" i API)
        controller_online = controller.get("online")

        # Alarmfelter på controller (gateway)
        alarm_mode = controller.get("alarm_notification_mode")
        alarm_triggered = controller.get("alarm_notification_triggered")
        alarm_message = controller.get("alarm_notification_message")
        alarm_invert_mode = controller.get("alarm_invert_notification_mode")

        # Props-map: (device_id, key) -> value
        new_props: dict[tuple[int, str], Any] = {}

        if isinstance(devices, list):
            for dev in devices:
                if not isinstance(dev, dict):
                    continue

                did = dev.get("bpapi_device_id")
                try:
                    did_int = int(did)
                except (TypeError, ValueError):
                    continue

                if did_int not in wanted_ids:
                    continue

                # Termostat/switch-props
                for key in (PROP_SWITCH_MODE, PROP_TEMP, PROP_TEMP_ECO, PROP_TEMP_COMFORT):
                    if key in dev:
                        new_props[(did_int, key)] = dev.get(key)

                # Sensor props (AMS m.m.)
                for key in SENSOR_PROPS:
                    if key in dev:
                        new_props[(did_int, key)] = dev.get(key)

        self._last_appview_ts = dt_util.utcnow().replace(microsecond=0).isoformat()

        return {
            "props": new_props,
            "_appview_heartbeat": self._last_appview_ts,

            # Gateway online (connectivity)
            "_controller_online": controller_online,  # "1"/"0" (eller None)

            # Alarm/varsling (controller/gateway)
            "_alarm_notification_mode": alarm_mode,               # "0"/"1" eller None
            "_alarm_notification_triggered": alarm_triggered,     # "0"/"1" eller None
            "_alarm_notification_message": alarm_message,         # tekst eller None
            "_alarm_invert_notification_mode": alarm_invert_mode, # "0"/"1" eller None
        }
