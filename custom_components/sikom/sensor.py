from __future__ import annotations

from typing import Any
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def _to_float_safe(val: Any) -> float | None:
    """Parse tall fra str/Any. Returnerer None for 'X'/tom/ikke-tall."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.upper() == "X":
        return None
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", "."))
    except (ValueError, TypeError):
        return None


SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "power_usage": SensorEntityDescription(
        key="power_usage",
        name="Strømforbruk",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "voltage": SensorEntityDescription(
        key="voltage",
        name="Spenning",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current_l1": SensorEntityDescription(
        key="current_l1",
        name="Strøm L1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current_l2": SensorEntityDescription(
        key="current_l2",
        name="Strøm L2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "current_l3": SensorEntityDescription(
        key="current_l3",
        name="Strøm L3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "energy_total": SensorEntityDescription(
        key="energy_total",
        name="Energi importert (total)",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "energy_today": SensorEntityDescription(
        key="energy_today",
        name="Energi i dag",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
    ),
}

MEASURED_TEMP_DESC = SensorEntityDescription(
    key="measured_temp",
    name="Målt temperatur",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
)

# Kandidater per måling: vi prøver ams_* først (som finnes i din AppView når de finnes)
METER_METRICS: list[tuple[str, list[str]]] = [
    ("power_usage", ["ams_current_power_usage", "current_power_usage"]),
    ("voltage", ["ams_power_voltage", "power_voltage"]),
    ("current_l1", ["ams_i1"]),
    ("current_l2", ["ams_i2"]),
    ("current_l3", ["ams_i3"]),
    ("energy_today", ["ams_cumulative_plus_calculated_energy_today"]),
    ("energy_total", ["ams_cumulative_imported_energy"]),
]


def _props_keys_for_device(coordinator, device_id: int) -> set[str]:
    """Hvilke props har vi faktisk for device_id i siste refresh."""
    props = (coordinator.data or {}).get("props", {})
    if not isinstance(props, dict):
        return set()

    out: set[str] = set()
    for (did, key) in props.keys():
        if int(did) == int(device_id):
            out.add(str(key))
    return out


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    # AMS / energimåler: lag kun sensorer som faktisk finnes i AppView props
    for device_id in coordinator.device_map.get("sensor", []):
        did = int(device_id)
        available_keys = _props_keys_for_device(coordinator, did)

        for metric_key, candidates in METER_METRICS:
            # Hvis ingen av kandidatene finnes i AppView-data -> ikke lag entity (unngå "Utilgjengelig")
            if not any(c in available_keys for c in candidates):
                continue

            desc = SENSOR_DESCRIPTIONS[metric_key]
            entities.append(SikomMeterMetricSensor(coordinator, did, desc, candidates))

    # Målt temperatur for termostater: kun hvis temperature finnes og ikke er "X"
    for device_id in coordinator.device_map.get("climate", []):
        did = int(device_id)
        props = (coordinator.data or {}).get("props", {})
        raw = props.get((did, "temperature"))
        if _to_float_safe(raw) is None:
            continue
        entities.append(SikomMeasuredTempSensor(coordinator, did))

    # IKKE lag temperatur for relé (switch). Den er "X" hos deg og skaper støy.

    # Alarm-melding (diagnostikk) – kun hvis alarmfelt finnes i controller
    entities.append(SikomGatewayAlarmMessageSensor(coordinator))

    # Heartbeat / diagnostikk
    entities.append(SikomAppViewHeartbeatSensor(coordinator, entry.entry_id))

    async_add_entities(entities)


class SikomMeterMetricSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        device_id: int,
        description: SensorEntityDescription,
        candidates: list[str],
    ) -> None:
        super().__init__(coordinator)
        self._device_id = int(device_id)
        self.entity_description = description
        self._candidates = list(candidates)

        device_name = coordinator.name_map.get("sensor", {}).get(self._device_id) or f"Sikom Meter {self._device_id}"

        # ✅ behold samme unique_id-format som før
        self._attr_unique_id = f"sikom_sensor_{self._device_id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{self._device_id}")},
            name=device_name,
            manufacturer="Sikom",
            model="ECO Energy Controller (AMS)",
        )

    def _first_present(self) -> tuple[str | None, Any | None]:
        props = (self.coordinator.data or {}).get("props", {})
        for prop in self._candidates:
            key = (self._device_id, prop)
            if key in props:
                return prop, props.get(key)
        return None, None

    @property
    def native_value(self) -> float | None:
        _, raw = self._first_present()
        parsed = _to_float_safe(raw)
        if parsed is None:
            return None

        # Energi i AppView ser ut som Wh hos deg → kWh i HA
        if (
            self.device_class == SensorDeviceClass.ENERGY
            and self.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
        ):
            return parsed / 1000.0

        return parsed

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        prop, raw = self._first_present()
        return prop is not None and _to_float_safe(raw) is not None


class SikomMeasuredTempSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    entity_description = MEASURED_TEMP_DESC

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = int(device_id)

        base_name = coordinator.name_map.get("climate", {}).get(self._device_id) or f"Sikom Thermostat {self._device_id}"
        self._base_name = base_name
        self._attr_unique_id = f"sikom_measured_temp_{self._device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{self._device_id}")},
            name=base_name,
            manufacturer="Sikom",
            model="Thermostat",
        )

    @property
    def name(self) -> str:
        return f"{self._base_name} {self.entity_description.name}"

    @property
    def native_value(self) -> float | None:
        raw = (self.coordinator.data or {}).get("props", {}).get((self._device_id, "temperature"))
        return _to_float_safe(raw)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        raw = (self.coordinator.data or {}).get("props", {}).get((self._device_id, "temperature"))
        return _to_float_safe(raw) is not None


class SikomGatewayAlarmMessageSensor(CoordinatorEntity, SensorEntity):
    """Alarmmelding fra gateway/controller (diagnostikk)."""

    _attr_has_entity_name = True
    _attr_name = "Alarm melding"
    _attr_icon = "mdi:alert"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        gateway_id = getattr(coordinator, "gateway_id", "unknown")
        self._attr_unique_id = f"sikom_gateway_alarm_message_{gateway_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"gateway_{gateway_id}")},
            name="Sikom Gateway",
            manufacturer="Sikom",
            model="Sikom Connect / AppView",
        )

    @property
    def native_value(self) -> str | None:
        msg = (self.coordinator.data or {}).get("_alarm_notification_message")
        if msg is None:
            return None
        s = str(msg).strip()
        return s or None

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        # Tilgjengelig når feltet finnes i controller (selv om meldingen kan være tom)
        return (self.coordinator.data or {}).get("_alarm_notification_message") is not None


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
        return (self.coordinator.data or {}).get("_appview_heartbeat")
