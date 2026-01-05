from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import AuthError, ApiError, SikomApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


def _bucket_devices(devices: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Returnerer (climate_ids, switch_ids, sensor_ids) som dict[str(id)]=name."""
    climate_ids: dict[str, str] = {}
    switch_ids: dict[str, str] = {}
    sensor_ids: dict[str, str] = {}

    for d in devices:
        did = str(d["id"])
        name = str(d["name"])
        dtype = str(d.get("type") or "").lower()

        # Termostat: "Wireless Thermostat (SI-3)" / "(SI-4)"
        if "wireless thermostat" in dtype or ("thermostat" in dtype and "energy controller" not in dtype):
            climate_ids[did] = name
            continue

        # AMS: "ECO Energy Controller (ECO-AMS)"
        if "eco energy controller" in dtype or "eco-ams" in dtype:
            sensor_ids[did] = name
            continue

        # Easee
        if "easee" in dtype:
            sensor_ids[did] = name
            continue

        # Switch: har switch_mode i raw
        raw = d.get("raw") or {}
        if isinstance(raw, dict) and "switch_mode" in raw:
            switch_ids[did] = name
        else:
            sensor_ids[did] = name

    return climate_ids, switch_ids, sensor_ids


def _multi_select(options: dict[str, str], default: list[str]) -> SelectSelector:
    """Home Assistant selector for multi-select."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[{"value": k, "label": v} for k, v in options.items()],
            multiple=True,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


class SikomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

        username = user_input["username"]
        password = user_input["password"]

        api = SikomApi(self.hass, username, password)

        try:
            await api.login()

            gateway_id = await api.get_gateway_id_from_v21()
            if not gateway_id:
                raise ApiError("Fant ingen gateway_id i AppView/v2.1/All")

            devices = await api.list_devices_from_v4(gateway_id)
            if not devices:
                raise ApiError("Fant ingen enheter i AppView/v4.0/<gateway_id>")

            climate_ids, switch_ids, sensor_ids = _bucket_devices(devices)

            self._cache = {
                "username": username,
                "password": password,
                "gateway_id": gateway_id,
                "climate_ids": climate_ids,
                "switch_ids": switch_ids,
                "sensor_ids": sensor_ids,
            }

            return await self.async_step_select()

        except AuthError:
            errors["base"] = "invalid_auth"
        except Exception as exc:
            _LOGGER.exception("Uventet feil i Sikom config flow: %s", exc)
            errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_select(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        cache: dict[str, Any] = getattr(self, "_cache", {})

        climate_ids: dict[str, str] = cache.get("climate_ids", {})
        switch_ids: dict[str, str] = cache.get("switch_ids", {})
        sensor_ids: dict[str, str] = cache.get("sensor_ids", {})

        default_climate = list(climate_ids.keys())
        default_switch = list(switch_ids.keys())
        default_sensor = list(sensor_ids.keys())

        schema = vol.Schema(
            {
                vol.Optional("climate", default=default_climate): _multi_select(climate_ids, default_climate),
                vol.Optional("switch", default=default_switch): _multi_select(switch_ids, default_switch),
                vol.Optional("sensor", default=default_sensor): _multi_select(sensor_ids, default_sensor),
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="select", data_schema=schema)

        chosen_climate: list[str] = user_input.get("climate", [])
        chosen_switch: list[str] = user_input.get("switch", [])
        chosen_sensor: list[str] = user_input.get("sensor", [])

        final_climate_ids = {did: climate_ids[did] for did in chosen_climate if did in climate_ids}
        final_switch_ids = {did: switch_ids[did] for did in chosen_switch if did in switch_ids}
        final_sensor_ids = {did: sensor_ids[did] for did in chosen_sensor if did in sensor_ids}

        entry_data = {
            "username": cache["username"],
            "password": cache["password"],
            "gateway_id": cache["gateway_id"],
            "climate_ids": final_climate_ids,
            "switch_ids": final_switch_ids,
            "sensor_ids": final_sensor_ids,
        }

        await self.async_set_unique_id(f"sikom_{cache['gateway_id']}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="Sikom", data=entry_data)
