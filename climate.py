from __future__ import annotations
from typing import Any
import logging
import re

from homeassistant.components.climate import ClimateEntity, HVACMode, ClimateEntityFeature
from homeassistant.components.climate.const import HVACAction
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN, PROP_TEMP, PROP_TEMP_COMFORT, PROP_TEMP_ECO,
    PROP_SWITCH_MODE, DEFAULT_ECO_TEMP, DEFAULT_COMFORT_TEMP
)

_LOGGER = logging.getLogger(__name__)
PRESET_SPARING = "Sparing"
PRESET_KOMFORT = "Komfort"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SikomClimate(coordinator, did) for did in coordinator.device_map.get("climate", [])]
    async_add_entities(entities)

class SikomClimate(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_preset_modes = [PRESET_SPARING, PRESET_KOMFORT]
    _attr_min_temp = 5.0
    _attr_max_temp = 35.0
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        friendly = coordinator.name_map.get("climate", {}).get(device_id) or f"Sikom Thermostat {device_id}"
        self._attr_name = friendly
        self._attr_unique_id = f"sikom_climate_{device_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"climate_{self._device_id}")}, name=self.name,
            manufacturer="Sikom", model="Thermostat")

    def _get_prop(self, prop: str) -> str | None:
        return self.coordinator.data.get("props", {}).get((self._device_id, prop))

    def _to_float(self, val) -> float | None:
        if val is None: return None
        if isinstance(val, (int, float)): return float(val)
        s = str(val).strip()
        m = re.search(r"[-+]?\d+(?:[.,]\d+)?", s)
        if not m: return None
        num = m.group(0).replace(",", ".")
        try:
            return float(num)
        except ValueError:
            return None

    def _get_prop_float(self, prop: str) -> float | None:
        return self._to_float(self._get_prop(prop))

    def _int_to_send(self, v: float | int) -> int:
        return int(round(float(v)))

    @property
    def current_temperature(self) -> float | None:
        return self._get_prop_float(PROP_TEMP)

    @property
    def preset_mode(self) -> str | None:
        return PRESET_KOMFORT if str(self._get_prop(PROP_SWITCH_MODE)) == "1" else PRESET_SPARING

    def _comfort_target(self) -> float:
        return self._get_prop_float(PROP_TEMP_COMFORT) or DEFAULT_COMFORT_TEMP

    def _eco_target(self) -> float:
        return self._get_prop_float(PROP_TEMP_ECO) or DEFAULT_ECO_TEMP

    @property
    def target_temperature(self) -> float | None:
        return self._comfort_target() if self.preset_mode == PRESET_KOMFORT else self._eco_target()

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        cur = self.current_temperature
        tgt = self.target_temperature
        if cur is None or tgt is None: return HVACAction.IDLE
        return HVACAction.HEATING if cur < tgt - 0.1 else HVACAction.IDLE

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode = 1 if preset_mode == PRESET_KOMFORT else 0
        await self.coordinator.client.set_property_value(self._device_id, PROP_SWITCH_MODE, mode)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None: return
        prop = PROP_TEMP_COMFORT if self.preset_mode == PRESET_KOMFORT else PROP_TEMP_ECO
        await self.coordinator.client.set_property_value(self._device_id, prop, self._int_to_send(temp))
        await self.coordinator.async_request_refresh()