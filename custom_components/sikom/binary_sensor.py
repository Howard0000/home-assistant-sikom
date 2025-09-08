# Fil: custom_components/sikom/binary_sensor.py

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

# Property-navnet vi ser etter i API-dataene
CONNECTION_PROPERTY = "connection"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Sett opp tilkoblingssensorer for enheter som rapporterer dette."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    # Se gjennom ALLE enheter (ikke bare sensorer) for å finne de som har "connection"-status
    all_device_ids = set()
    for device_type in coordinator.device_map:
        for device_id in coordinator.device_map[device_type]:
            all_device_ids.add(device_id)

    for device_id in all_device_ids:
        # Sjekk om denne enheten har en "connection"-property i de hentede dataene
        if (device_id, CONNECTION_PROPERTY) in coordinator.data.get("props", {}):
            entities.append(SikomConnectionSensor(coordinator, device_id))
    
    async_add_entities(entities)


class SikomConnectionSensor(CoordinatorEntity, BinarySensorEntity):
    """Representerer tilkoblingsstatusen for en Sikom-enhet."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

        # Finn et passende navn for enheten, uansett type
        device_name = "Ukjent enhet"
        for device_type in coordinator.name_map:
            if name := coordinator.name_map[device_type].get(device_id):
                device_name = name
                break
        
        self._attr_name = "Tilkobling"
        self._attr_unique_id = f"sikom_connection_{device_id}"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},  # Bruk en generell device-ID
            name=device_name,
            manufacturer="Sikom",
        )

    @property
    def is_on(self) -> bool:
        """Returner True hvis enheten er online."""
        value = self.coordinator.data.get("props", {}).get((self._device_id, CONNECTION_PROPERTY))
        # API returnerer typisk "online" som en streng
        return isinstance(value, str) and value.lower() == "online"

    @property
    def available(self) -> bool:
        """Sensoren er tilgjengelig hvis vi har data for den."""
        return (
            super().available
            and (self._device_id, CONNECTION_PROPERTY) in self.coordinator.data.get("props", {})
        )