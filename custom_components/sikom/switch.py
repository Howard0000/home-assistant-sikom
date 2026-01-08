from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PROP_SWITCH_MODE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switch_ids = coordinator.device_map.get("switch", [])
    name_map = coordinator.name_map.get("switch", {})

    entities: list[SikomSwitch] = []
    for did in switch_ids:
        try:
            did_int = int(did)
        except (TypeError, ValueError):
            continue

        name = name_map.get(did_int, f"Switch {did_int}")
        entities.append(SikomSwitch(coordinator, did_int, name))

    async_add_entities(entities)


class SikomSwitch(CoordinatorEntity, SwitchEntity):
    """Sikom switch (typisk relé / varmtvannsbereder osv.)."""

    def __init__(self, coordinator, device_id: int, name: str) -> None:
        super().__init__(coordinator)
        self._device_id = int(device_id)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_switch_{self._device_id}"

    @property
    def device_info(self) -> DeviceInfo:
        # Viktig: bruk samme device-identifiers som resten (device_{id})
        return DeviceInfo(
            identifiers={(DOMAIN, f"device_{self._device_id}")},
            name=self.name,
            manufacturer="Sikom",
            model="Switch/Relay",
        )

    @property
    def available(self) -> bool:
        # Tilgjengelig når coordinator er tilgjengelig og vi faktisk har fått switch_mode for denne enheten
        if not super().available:
            return False
        v = self.coordinator.data.get("props", {}).get((self._device_id, PROP_SWITCH_MODE))
        return v is not None

    @property
    def is_on(self) -> bool:
        v = self.coordinator.data.get("props", {}).get((self._device_id, PROP_SWITCH_MODE))
        return str(v) == "1"

    async def async_turn_on(self, **kwargs) -> None:
        ok = await self.coordinator.client.set_property_with_confirm(
            self._device_id,
            PROP_SWITCH_MODE,
            1,
        )
        if not ok:
            _LOGGER.warning(
                "Sikom: switch_mode ble ikke bekreftet som PÅ for device %s",
                self._device_id,
            )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        ok = await self.coordinator.client.set_property_with_confirm(
            self._device_id,
            PROP_SWITCH_MODE,
            0,
        )
        if not ok:
            _LOGGER.warning(
                "Sikom: switch_mode ble ikke bekreftet som AV for device %s",
                self._device_id,
            )
        await self.coordinator.async_request_refresh()
