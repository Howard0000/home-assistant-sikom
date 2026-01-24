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

    async_add_entities(
        [
            SikomGatewayOnlineBinarySensor(coordinator),
            SikomGatewayAlarmBinarySensor(coordinator),
        ]
    )


class SikomGatewayOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Gateway online/offline basert på AppView controller.online."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Tilkobling"

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


class SikomGatewayAlarmBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Alarm trigget på gateway/controller (AppView controller.alarm_notification_triggered)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True
    _attr_name = "Alarm"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

        gateway_id = getattr(coordinator, "gateway_id", "unknown")
        self._attr_unique_id = f"sikom_gateway_alarm_{gateway_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"gateway_{gateway_id}")},
            name="Sikom Gateway",
            manufacturer="Sikom",
            model="Sikom Connect / AppView",
        )

    @property
    def is_on(self) -> bool:
        # "1" betyr trigget
        val = self.coordinator.data.get("_alarm_notification_triggered")
        return str(val) == "1"

    @property
    def extra_state_attributes(self) -> dict:
        # Legg meldingen som attributt (praktisk i UI og automasjoner)
        msg = self.coordinator.data.get("_alarm_notification_message")
        mode = self.coordinator.data.get("_alarm_notification_mode")
        inv = self.coordinator.data.get("_alarm_invert_notification_mode")
        return {
            "message": msg,
            "mode": mode,
            "invert_mode": inv,
        }

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        # Vi regner den som tilgjengelig når feltet eksisterer i det hele tatt
        return self.coordinator.data.get("_alarm_notification_triggered") is not None
