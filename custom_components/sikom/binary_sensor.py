from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SikomGatewayOnlineBinarySensor(coordinator), SikomGatewayAlarmBinarySensor(coordinator)]
    entities.extend(SikomRelayStateBinarySensor(coordinator, int(did))
                    for did in coordinator.device_map.get("climate", []))
    async_add_entities(entities)


class SikomRelayStateBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Sist rapporterte reléstatus fra Sikom; ikke sanntidsmåling."""

    _attr_has_entity_name = True
    _attr_name = "Reléstatus"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:electric-switch"

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"sikom_relay_state_{device_id}"
        name = coordinator.name_map.get("climate", {}).get(device_id) or f"Sikom Thermostat {device_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=name,
            manufacturer="Sikom",
            model="Thermostat",
        )

    def _relay(self) -> dict | None:
        data = self.coordinator.data or {}
        return data.get("_relay_states", {}).get(self._device_id)

    @property
    def is_on(self) -> bool | None:
        relay = self._relay()
        if relay is None:
            return None
        return relay["value"] == "1"

    @property
    def available(self) -> bool:
        return super().available and self._relay() is not None

    @property
    def extra_state_attributes(self) -> dict:
        relay = self._relay()
        if relay is None:
            return {}
        return {
            "sikom_created": relay.get("created"),
            "sikom_last_valid": relay.get("last_valid"),
            "source": "Sikom Device/All (reported relay state)",
        }


class SikomGatewayOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Gateway online/offline basert på AppView controller.online."""
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = "Tilkobling"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        gateway_id = getattr(coordinator, "gateway_id", "unknown")
        self._attr_unique_id = f"sikom_gateway_online_{gateway_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"gateway_{gateway_id}")},
            name="Sikom Gateway", manufacturer="Sikom", model="Sikom Connect / AppView",
        )

    @property
    def is_on(self) -> bool:
        val = self.coordinator.data.get("_controller_online")
        return str(val) == "1"

    @property
    def available(self) -> bool:
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
            name="Sikom Gateway", manufacturer="Sikom", model="Sikom Connect / AppView",
        )

    @property
    def is_on(self) -> bool:
        val = self.coordinator.data.get("_alarm_notification_triggered")
        return str(val) == "1"

    @property
    def extra_state_attributes(self) -> dict:
        msg = self.coordinator.data.get("_alarm_notification_message")
        mode = self.coordinator.data.get("_alarm_notification_mode")
        inv = self.coordinator.data.get("_alarm_invert_notification_mode")
        return {"message": msg, "mode": mode, "invert_mode": inv}

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        return self.coordinator.data.get("_alarm_notification_triggered") is not None
