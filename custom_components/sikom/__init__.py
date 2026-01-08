from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import AuthError, SikomApi
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIMATE_IDS,
    CONF_SWITCH_IDS,
    CONF_SENSOR_IDS,
)
from .coordinator import SikomDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["climate", "switch", "sensor", "binary_sensor"]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to new version."""
    _LOGGER.debug("Migrating Sikom config entry from version %s", entry.version)

    # v1 -> v2: fjern gamle/utgåtte felt (ADRESSE) + sørg for gateway_id hvis mulig
    if entry.version == 1:
        data = dict(entry.data)
        options = dict(entry.options)

        # Fjern felt som ikke skal være der lenger
        data.pop("ADRESSE", None)
        options.pop("ADRESSE", None)

        # Forsøk å sette gateway_id hvis den mangler (ikke fail migrering om det ikke går)
        merged: Dict[str, Any] = {**data, **options}
        if merged.get("gateway_id") is None:
            username = str(merged.get(CONF_USERNAME, "")).strip()
            password = str(merged.get(CONF_PASSWORD, "")).strip()

            if username and password:
                try:
                    api = SikomApi(hass, username, password)
                    await api.login()
                    gid = await api.get_gateway_id_from_v21()
                except Exception as exc:  # noqa: BLE001
                    _LOGGER.warning("Kunne ikke hente gateway_id under migrering: %s", exc)
                    gid = None

                if gid is not None:
                    data["gateway_id"] = int(gid)

        hass.config_entries.async_update_entry(entry, data=data, options=options, version=2)
        _LOGGER.info("Migration to version 2 successful")

    return True


def _to_int_keyed_map(raw: Any) -> dict[int, str]:
    """Konverter { '591040': 'Bad' } -> { 591040: 'Bad' } (robust)."""
    out: dict[int, str] = {}
    if not isinstance(raw, dict):
        return out

    for k, v in raw.items():
        try:
            out[int(k)] = str(v)
        except (TypeError, ValueError):
            continue
    return out


def _get_gateway_id(entry: ConfigEntry) -> int:
    """Hent gateway_id fra entry.data/options (robust)."""
    merged: Dict[str, Any] = {**entry.data, **entry.options}
    gid = merged.get("gateway_id")

    if gid is None:
        raise ValueError("Mangler gateway_id i Sikom config entry (data/options).")

    try:
        return int(gid)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Ugyldig gateway_id i Sikom config entry: {gid}") from exc


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sett opp Sikom fra en config entry."""
    merged_options: Dict[str, Any] = {**entry.data, **entry.options}

    # Viktig: Keys i entry/options er ofte str -> vi må ha int overalt internt
    climate_map = _to_int_keyed_map(merged_options.get(CONF_CLIMATE_IDS, {}))
    switch_map = _to_int_keyed_map(merged_options.get(CONF_SWITCH_IDS, {}))
    sensor_map = _to_int_keyed_map(merged_options.get(CONF_SENSOR_IDS, {}))

    device_map = {
        "climate": list(climate_map.keys()),
        "switch": list(switch_map.keys()),
        "sensor": list(sensor_map.keys()),
    }

    name_map = {
        "climate": climate_map,
        "switch": switch_map,
        "sensor": sensor_map,
    }

    # Hent brukernavn/passord robust (kan ligge i options hvis senere endret)
    username = str(merged_options.get(CONF_USERNAME, "")).strip()
    password = str(merged_options.get(CONF_PASSWORD, "")).strip()

    # --- gateway_id: først normalt, deretter self-heal hvis mangler ---
    try:
        gateway_id = _get_gateway_id(entry)
    except ValueError:
        _LOGGER.warning("gateway_id mangler i config entry – forsøker å hente automatisk via API")

        if not username or not password:
            raise ConfigEntryNotReady("Mangler brukernavn/passord for å hente gateway_id")

        try:
            api = SikomApi(hass, username, password)
            await api.login()
            gid = await api.get_gateway_id_from_v21()
        except AuthError as exc:
            raise ConfigEntryNotReady(f"Autentisering feilet ved henting av gateway_id: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise ConfigEntryNotReady(f"Feil ved henting av gateway_id: {exc}") from exc

        if gid is None:
            raise ConfigEntryNotReady("Kunne ikke hente gateway_id fra Sikom API")

        # Lagre gateway_id tilbake i entry.data så dette kun skjer én gang
        hass.config_entries.async_update_entry(entry, data={**entry.data, "gateway_id": int(gid)})
        gateway_id = int(gid)

    coordinator = SikomDataCoordinator(
        hass=hass,
        entry=entry,
        username=username,
        password=password,
        gateway_id=gateway_id,
        device_map=device_map,
        name_map=name_map,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjern Sikom-integrasjonen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Last inn config entry på nytt når options endres."""
    await hass.config_entries.async_reload(entry.entry_id)
