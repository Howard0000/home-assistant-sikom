from __future__ import annotations
from typing import Any
import re

from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPower, UnitOfEnergy, UnitOfElectricCurrent, UnitOfElectricPotential,
    UnitOfTemperature
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, SENSOR_PROPS


SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "power_usage": SensorEntityDescription(
        key="power_usage", name="Strømforbruk", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT),
    "energy_total": SensorEntityDescription(
        key="energy_total", name="Energi importert (total)", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL_INCREASING),
    "energy_today": SensorEntityDescription(
        key="energy_today", name="Energi i dag", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL),
    "voltage": SensorEntityDescription(
        key="voltage", name="Spenning", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT),
    "current_l1": SensorEntityDescription(
        key="current_l1", name="Strøm L1", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT),
    "current_l2": SensorEntityDescription(
        key="current_l2", name="Strøm L2", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT),
    "current_l3": SensorEntityDescription(
        key="current_l3", name="Strøm L3", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT),
}

MEASURED_TEMP_DESC = SensorEntityDescription(
    key="measured_temp",
    name="Målt temperatur",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
)

PROPERTY_ALIASES = {
    "ams_current_power_usage": "power_usage",
    "current_power_usage": "power_usage",
    "ams_cumulative_imported_energy": "energy_total",
    "ams_cumulative_plus_calculated_energy_today": "energy_today",
    "ams_power_voltage": "voltage",
    "power_voltage": "voltage",
    "ams_i1": "current_l1",
    "ams_i2": "current_l2",
    "ams_i3": "current_l3",
}

def _to_float_safe(val: Any) -> float | None:
    if val is None:
        return None
    s = str(val).strip()
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", s)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except (ValueError, TypeError):
        return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    created_sensors: set[tuple[int, str]] = set()

    # AMS / energimåler-sensorer
    for device_id in coordinator.device_map.get("sensor", []):
        for prop_name in SENSOR_PROPS:
            raw_value = coordinator.data.get("props", {}).get((device_id, prop_name))
            if _to_float_safe(raw_value) is not None:
                internal_key = PROPERTY_ALIASES.get(prop_name)
                if internal_key and (device_id, internal_key) not in created_sensors:
                    description = SENSOR_DESCRIPTIONS[internal_key]
                    entities.append(SikomMeterSensor(coordinator, device_id, description, prop_name))
                    created_sensors.add((device_id, internal_key))

    # Målt temperatur for climate-enheter
    for device_id in coordinator.device_map.get("climate", []):
        raw_temp = coordinator.data.get("props", {}).get((device_id, "temperature"))
        if _to_float_safe(raw_temp) is None:
            continue
        key = (device_id, "measured_temp")
        if key in created_sensors:
            continue
        entities.append(SikomMeasuredTempSensor(coordinator, device_id))
        created_sensors.add(key)

    # Temperatur fra relé (switch) – NYTT
    for device_id in coordinator.device_map.get("switch", []):
        raw_temp = coordinator.data.get("props", {}).get((device_id, "temperature"))
        if _to_float_safe(raw_temp) is None:
            continue
        key = (device_id, "switch_temp")
        if key in created_sensors:
            continue
        entities.append(SikomSwitchTempSensor(coordinator, device_id))
        created_sensors.add(key)

    # AppView-heartbeat (diagnostikk)
    entities.append(SikomAppViewHeartbeatSensor(coordinator, entry.entry_id))

    async_add_entities(entities)


class SikomMeterSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device_id: int, description: SensorEntityDescription, prop_name: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._prop_name = prop_name

        device_name = coordinator.name_map.get("sensor", {}).get(device_id) or f"Sikom Meter {device_id}"
        self._attr_unique_id = f"sikom_sensor_{device_id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"sensor_{device_id}")},
            name=device_name,
            manufacturer="Sikom",
            model="Energy Meter",
        )

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get("props", {}).get((self._device_id, self._prop_name))
        parsed_val = _to_float_safe(raw)
        if parsed_val is None:
            return None
        if self.device_class == SensorDeviceClass.ENERGY and self.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR:
            return parsed_val / 1000.0
        return parsed_val

    @property
    def available(self) -> bool:
        return super().available and (self._device_id, self._prop_name) in self.coordinator.data.get("props", {})


class SikomMeasuredTempSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    entity_description = MEASURED_TEMP_DESC

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

        base_name = coordinator.name_map.get("climate", {}).get(device_id) or f"Sikom Thermostat {device_id}"
        self._base_name = base_name
        self._attr_unique_id = f"sikom_measured_temp_{device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=base_name,
            manufacturer="Sikom",
            model="Thermostat",
        )

    @property
    def name(self) -> str:
        return f"{self._base_name} {self.entity_description.name}"

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get("props", {}).get((self._device_id, "temperature"))
        return _to_float_safe(raw)

    @property
    def available(self) -> bool:
        return super().available and (self._device_id, "temperature") in self.coordinator.data.get("props", {})


class SikomSwitchTempSensor(CoordinatorEntity, SensorEntity):
    """Temperatur fra reléets probe (Eco Controller 3)."""
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        base_name = coordinator.name_map.get("switch", {}).get(device_id) or f"Sikom Switch {device_id}"
        self._base_name = base_name
        self._attr_name = f"{base_name} Temperatur"
        self._attr_unique_id = f"sikom_switch_temp_{device_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"switch_{device_id}")},
            name=base_name,
            manufacturer="Sikom",
            model="Eco Relay",
        )

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get("props", {}).get((self._device_id, "temperature"))
        return _to_float_safe(raw)

    @property
    def available(self) -> bool:
        return super().available and (self._device_id, "temperature") in self.coordinator.data.get("props", {})


# AppView-heartbeat (diagnostikk: oppdateres KUN ved nudge hver ~5–6 min)
class SikomAppViewHeartbeatSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "AppView Heartbeat"
    _attr_icon = "mdi:pulse"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_appview_heartbeat"

    @property
    def native_value(self) -> str | None:
        # Viser tidspunkt for SISTE AppView-nudge (5–6 min-raten). Endrer seg ikke ved minutt-poll.
        return self.coordinator.data.get("_appview_heartbeat")
