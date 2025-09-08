# Fil: custom_components/sikom/config_flow.py

from __future__ import annotations
import logging
from typing import Dict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIMATE_IDS,
    CONF_SWITCH_IDS,
    CONF_SENSOR_IDS,
)
from .api import SikomClient, AuthError, ApiError

_LOGGER = logging.getLogger(__name__)

class SikomOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry
        self._discovered: dict[str, dict[str, str]] | None = None

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            def pick(kind: str) -> Dict[int, str]:
                # Sørg for at _discovered ikke er None før vi bruker det
                if not self._discovered:
                    return {}
                return {int(i): self._discovered[kind][i] for i in user_input.get(kind, [])}
            return self.async_create_entry(title="", data={
                CONF_CLIMATE_IDS: pick("climate"),
                CONF_SWITCH_IDS: pick("switch"),
                CONF_SENSOR_IDS: pick("sensor")
            })

        # --- START PÅ SKUDDSIKKER KODE ---
        errors = {}
        try:
            api = SikomClient(self.hass, self.entry.data[CONF_USERNAME], self.entry.data[CONF_PASSWORD])
            devices = await api.list_devices()
        except (ApiError, AuthError):
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Uventet feil i options flow")
            errors["base"] = "unknown"
        
        if errors:
            return self.async_show_form(step_id="init", errors=errors)
        # --- SLUTT PÅ SKUDDSIKKER KODE ---

        clim, sw, ams = {}, {}, {}
        for d in devices:
            did, name, dtype = str(d["id"]), d["name"], (d["type"] or "").lower()
            if any(k in dtype for k in ["thermostat", "wirelessthermostat", "si-"]):
                clim[did] = name
            elif any(k in dtype for k in ["relay", "switch", "econode", "tech-rel"]):
                sw[did] = name
            else:
                ams[did] = name
        self._discovered = {"climate": clim, "switch": sw, "sensor": ams}

        current_options = {**self.entry.data, **self.entry.options}
        def configured_ids(key: str) -> list[str]:
            return [str(k) for k in (current_options.get(key) or {}).keys()]

        schema = vol.Schema({
            vol.Optional("climate", default=configured_ids(CONF_CLIMATE_IDS)): cv.multi_select(self._discovered["climate"]),
            vol.Optional("switch", default=configured_ids(CONF_SWITCH_IDS)): cv.multi_select(self._discovered["switch"]),
            vol.Optional("sensor", default=configured_ids(CONF_SENSOR_IDS)): cv.multi_select(self._discovered["sensor"])})
        return self.async_show_form(step_id="init", data_schema=schema)


class SikomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SikomOptionsFlowHandler:
        return SikomOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()

            self._api = SikomClient(self.hass, username, user_input[CONF_PASSWORD])
            try:
                await self._api.login()
            except AuthError:
                errors["base"] = "auth_failed"
            except Exception:
                errors["base"] = "unknown"
            else:
                self._username = username
                self._password = user_input[CONF_PASSWORD]
                return await self.async_step_select()

        schema = vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select(self, user_input=None):
        if not hasattr(self, "_discovered"):
            try:
                devices = await self._api.list_devices()
            except ApiError:
                return self.async_abort(reason="cannot_connect")
            
            clim, sw, ams = {}, {}, {}
            for d in devices:
                did, name, dtype = str(d["id"]), d["name"], (d["type"] or "").lower()
                if any(k in dtype for k in ["thermostat", "wirelessthermostat", "si-"]):
                    clim[did] = name
                elif any(k in dtype for k in ["relay", "switch", "econode", "tech-rel"]):
                    sw[did] = name
                elif any(k in dtype for k in ["eco", "ams", "energy", "controller"]):
                    ams[did] = name
                else:
                    ams[did] = name
            self._discovered = {"climate": clim, "switch": sw, "sensor": ams}

        if user_input is not None:
            def pick(kind: str) -> Dict[int, str]:
                return {int(i): self._discovered[kind][i] for i in user_input.get(kind, [])}
            return self.async_create_entry(
                title=self._username,
                data={
                    CONF_USERNAME: self._username, CONF_PASSWORD: self._password,
                    CONF_CLIMATE_IDS: pick("climate"), CONF_SWITCH_IDS: pick("switch"),
                    CONF_SENSOR_IDS: pick("sensor")
                })

        schema = vol.Schema({
            vol.Optional("climate", default=list(self._discovered["climate"].keys())): cv.multi_select(self._discovered["climate"]),
            vol.Optional("switch", default=list(self._discovered["switch"].keys())): cv.multi_select(self._discovered["switch"]),
            vol.Optional("sensor", default=list(self._discovered["sensor"].keys())): cv.multi_select(self._discovered["sensor"])})
        return self.async_show_form(step_id="select", data_schema=schema)