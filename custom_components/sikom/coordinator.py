from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import SikomClient
from .const import (
    DOMAIN, DEFAULT_SCAN_INTERVAL, PROP_SWITCH_MODE, PROP_TEMP,
    PROP_TEMP_ECO, PROP_TEMP_COMFORT, SENSOR_PROPS,
)

_LOGGER = logging.getLogger(__name__)
RELAY_POLL_INTERVAL = timedelta(minutes=5)


def _extract_relay_states(payload: Any, wanted_ids: set[int]) -> dict[int, dict[str, Any]]:
    """Normaliser Device/All uten å gjette på reléverdier ved uventet format."""
    if not isinstance(payload, dict):
        return {}
    data = payload.get("Data", payload)
    if not isinstance(data, dict):
        return {}
    devices = data.get("bpapi_array")
    if not isinstance(devices, list):
        _LOGGER.warning("Sikom relédiagnostikk: Device/All mangler Data.bpapi_array")
        return {}
    found: dict[int, dict[str, Any]] = {}
    for item in devices:
        if not isinstance(item, dict):
            continue
        device = item.get("device")
        if not isinstance(device, dict):
            continue
        props = device.get("Properties")
        if not isinstance(props, dict):
            continue
        id_property = props.get("bpapi_device_id")
        if not isinstance(id_property, dict):
            continue
        try:
            did = int(id_property.get("Value"))
        except (TypeError, ValueError):
            continue
        if did not in wanted_ids:
            continue
        prop = props.get("switch_state")
        if not isinstance(prop, dict):
            continue
        value = str(prop.get("Value", "")).strip()
        if value not in ("0", "1"):
            continue
        found[did] = {
            "value": value,
            "created": prop.get("Created"),
            "last_valid": prop.get("LastValid"),
        }
    return found


class SikomDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """AppView v4 + valgfri, begrenset Device/All-relédiagnostikk."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, username: str,
                 password: str, gateway_id: int, device_map: dict[str, list[int]],
                 name_map: dict[str, dict[int, str]]) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{gateway_id}",
                         update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.entry = entry
        self.client = SikomClient(hass, username, password)
        self.gateway_id = int(gateway_id)
        self.device_map = device_map
        self.name_map = name_map
        self._last_appview_ts: str | None = None
        self._relay_last_poll = None
        self._relay_states: dict[int, dict[str, Any]] = {}

    def _all_device_ids(self) -> set[int]:
        ids: set[int] = set()
        for k in ("climate", "switch", "sensor"):
            for did in self.device_map.get(k, []):
                try:
                    ids.add(int(did))
                except (TypeError, ValueError):
                    continue
        return ids

    def _enabled_relay_ids(self) -> set[int]:
        """Bare entiteter aktivert av bruker i HA entity registry."""
        registry = er.async_get(self.hass)
        enabled: set[int] = set()
        for did in self.device_map.get("climate", []):
            try:
                device_id = int(did)
            except (TypeError, ValueError):
                continue
            # Begge diagnostikksensorene kan starte samme Device/All-polling.
            for platform, uid in (
                ("binary_sensor", f"sikom_relay_state_{device_id}"),
                ("sensor", f"sikom_relay_created_{device_id}"),
            ):
                entity_id = registry.async_get_entity_id(platform, DOMAIN, uid)
                if entity_id:
                    entity = registry.async_get(entity_id)
                    if entity is not None and entity.disabled_by is None:
                        enabled.add(device_id)
                        break
        return enabled

    async def _refresh_relay_data(self) -> None:
        active_ids = self._enabled_relay_ids()
        if not active_ids:
            self._relay_states = {}
            self._relay_last_poll = None
            return
        now = dt_util.utcnow()
        if self._relay_last_poll is not None and now - self._relay_last_poll < RELAY_POLL_INTERVAL:
            return
        # Tell forsøket før nettverkskallet; API-feil skal ikke utløse nye kall hvert minutt.
        self._relay_last_poll = now
        try:
            raw = await self.client.get_device_all()
            self._relay_states = _extract_relay_states(raw, active_ids)
            _LOGGER.debug("Sikom relédiagnostikk: mottok %s av %s aktive reléverdier", len(self._relay_states), len(active_ids))
        except Exception as exc:  # noqa: BLE001
            self._relay_states = {}
            _LOGGER.warning("Sikom relédiagnostikk: Device/All feilet: %s", exc)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            av4 = await self.client.get_appview_v4(self.gateway_id)
        except Exception as exc:  # noqa: BLE001
            raise UpdateFailed(f"Sikom AppView feilet: {exc}") from exc
        if not isinstance(av4, dict):
            raise UpdateFailed("Sikom AppView returnerte ingen data (None/ugyldig)")
        controller = av4.get("controller") or {}
        devices = av4.get("devices") or []
        wanted_ids = self._all_device_ids()
        controller_online = controller.get("online")
        alarm_mode = controller.get("alarm_notification_mode")
        alarm_triggered = controller.get("alarm_notification_triggered")
        alarm_message = controller.get("alarm_notification_message")
        alarm_invert_mode = controller.get("alarm_invert_notification_mode")
        new_props: dict[tuple[int, str], Any] = {}
        if isinstance(devices, list):
            for dev in devices:
                if not isinstance(dev, dict):
                    continue
                try:
                    did_int = int(dev.get("bpapi_device_id"))
                except (TypeError, ValueError):
                    continue
                if did_int not in wanted_ids:
                    continue
                for key in (PROP_SWITCH_MODE, PROP_TEMP, PROP_TEMP_ECO, PROP_TEMP_COMFORT):
                    if key in dev:
                        new_props[(did_int, key)] = dev.get(key)
                for key in SENSOR_PROPS:
                    if key in dev:
                        new_props[(did_int, key)] = dev.get(key)
        # Ekstra oppslag bare ved aktivert reléstatus eller tidsstempel, maksimalt hvert 5. minutt.
        await self._refresh_relay_data()
        self._last_appview_ts = dt_util.utcnow().replace(microsecond=0).isoformat()
        return {
            "props": new_props,
            "_relay_states": dict(self._relay_states),
            "_appview_heartbeat": self._last_appview_ts,
            "_controller_online": controller_online,
            "_alarm_notification_mode": alarm_mode,
            "_alarm_notification_triggered": alarm_triggered,
            "_alarm_notification_message": alarm_message,
            "_alarm_invert_notification_mode": alarm_invert_mode,
        }
