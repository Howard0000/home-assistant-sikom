from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([SikomGatewayOnlineBinarySensor(coordinator)])


class SikomGatewayOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Gateway online/offline basert på AppView controller.online."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Gateway tilkobling"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

        # Stabil unique_id
        gateway_id = getattr(coordinator, "gateway_id", "unknown")
        self._attr_unique_id = f"sikom_gateway_online_{gateway_id}"

        # Egen device i device registry (gateway)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"gateway_{gateway_id}")},
            name="Sikom Gateway",
            manufacturer="Sikom",
            model="Sikom Connect / AppView",
        )

    @property
    def is_on(self) -> bool:
        """
        Returnerer True hvis controller.online == "1".
        Hvis nøkkelen mangler blir den False (men tilgjengelighet håndteres i available()).
        """
        val = self.coordinator.data.get("_controller_online")
        return str(val) == "1"

    @property
    def available(self) -> bool:
        """
        Tilgjengelig når coordinator er tilgjengelig og vi faktisk har fått et online-felt.
        Hvis API er nede vil coordinator ofte være 'unavailable' uansett.
        """
        if not super().available:
            return False
        return self.coordinator.data.get("_controller_online") is not None
