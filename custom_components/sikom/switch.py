from __future__ import annotations
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, PROP_SWITCH_MODE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SikomSwitch(coordinator, did) for did in coordinator.device_map.get("switch", [])]
    async_add_entities(entities)

class SikomSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        friendly = coordinator.name_map.get("switch", {}).get(device_id) or f"Sikom Switch {device_id}"
        self._attr_name = friendly
        self._attr_unique_id = f"sikom_switch_{device_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"switch_{self._device_id}")},
            name=self.name,
            manufacturer="Sikom",
            model="Eco Relay",
        )

    @property
    def is_on(self) -> bool:
        v = self.coordinator.data.get("props", {}).get((self._device_id, PROP_SWITCH_MODE))
        return str(v) == "1"

    async def async_turn_on(self, **kwargs):
        ok = await self.coordinator.client.set_property_with_confirm(self._device_id, PROP_SWITCH_MODE, 1)
        if not ok:
            _LOGGER.warning("Sikom: switch_mode ble ikke bekreftet som PÅ for device %s", self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        ok = await self.coordinator.client.set_property_with_confirm(self._device_id, PROP_SWITCH_MODE, 0)
        if not ok:
            _LOGGER.warning("Sikom: switch_mode ble ikke bekreftet som AV for device %s", self._device_id)
        await self.coordinator.async_request_refresh()
