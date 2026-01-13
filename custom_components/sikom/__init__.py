from __future__ import annotations

import logging
import re
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

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

# "Pakkenavn" for å gjøre feilsøking enklere i GitHub-issues
_REGISTRY_CLEANUP_TAG = "v1.1.3-registry-cleanup"

# Entiteter vi IKKE lenger støtter/bygger i v1.1.x, men som kan ligge igjen fra v1.0.8
_DEPRECATED_UNIQUE_ID_PREFIXES = (
    "sikom_connection_",   # utfaset "tilkobling" per enhet
    "sikom_switch_temp_",  # legacy "temperatur" på relé/switch
)

# sikom_sensor_<device_id>_<key>
_SENSOR_UID_RE = re.compile(r"^sikom_sensor_(\d+)_(.+)$")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to new version."""
    _LOGGER.debug("Sikom: migrating config entry %s from version %s", entry.entry_id, entry.version)

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
                    _LOGGER.warning("Sikom: kunne ikke hente gateway_id under migrering: %s", exc)
                    gid = None

                if gid is not None:
                    data["gateway_id"] = int(gid)

        hass.config_entries.async_update_entry(entry, data=data, options=options, version=2)
        _LOGGER.info("Sikom: migration to version 2 successful for %s", entry.entry_id)

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


def _parse_sikom_identifier(ident: str) -> tuple[str, int] | None:
    """Parse 'device_603905' / 'switch_603905' / 'sensor_555793' -> (kind, id)."""
    for kind in ("device", "switch", "sensor"):
        prefix = f"{kind}_"
        if ident.startswith(prefix):
            try:
                return kind, int(ident[len(prefix) :])
            except ValueError:
                return None
    return None


def _parse_sensor_uid(uid: str) -> tuple[int, str] | None:
    """Parse 'sikom_sensor_<did>_<key>' -> (did, key)."""
    m = _SENSOR_UID_RE.match(uid)
    if not m:
        return None
    try:
        return int(m.group(1)), m.group(2)
    except ValueError:
        return None


async def _migrate_registry_links(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    v1.1.3: Rydd opp i legacy device/entity registry etter v1.0.8 -> v1.1.x.

    - Disable deprecated entiteter som ikke lenger finnes/brukes (connection + switch_temp), inkl orphaned
    - Flytt entiteter som peker på legacy devices (switch_/sensor_) til canonical device_<id>
    - Slett legacy devices (switch_/sensor_) kun hvis de ender opp tomme
    """
    _LOGGER.debug("Sikom: starting %s for entry_id=%s", _REGISTRY_CLEANUP_TAG, entry.entry_id)

    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    moved = 0
    disabled = 0
    removed_devices = 0

    # --- 1) Disable deprecated entiteter (inkl orphaned) ---
    touched_orphaned = 0
    for ent in list(ent_reg.entities.values()):
        if ent.platform != DOMAIN:
            continue
        uid = ent.unique_id or ""
        if not uid.startswith(_DEPRECATED_UNIQUE_ID_PREFIXES):
            continue

        # Kun rør de som enten tilhører denne entry'en, eller er orphaned
        if ent.config_entry_id == entry.entry_id:
            pass
        elif ent.config_entry_id is None:
            touched_orphaned += 1
        else:
            continue

        if ent.disabled_by is None:
            ent_reg.async_update_entity(
                ent.entity_id,
                disabled_by=RegistryEntryDisabler.INTEGRATION,
            )
            disabled += 1

    if touched_orphaned:
        _LOGGER.debug(
            "Sikom: %s berørte også orphaned deprecated entities (%s funnet)",
            _REGISTRY_CLEANUP_TAG,
            touched_orphaned,
        )

    # --- 2) Bygg oppslag: (kind,id) -> device_entry.id ---
    by_kind_id: dict[tuple[str, int], str] = {}
    for dev in dev_reg.devices.values():
        for (domain, ident) in dev.identifiers:
            if domain != DOMAIN:
                continue
            parsed = _parse_sikom_identifier(str(ident))
            if parsed:
                kind, did = parsed
                by_kind_id[(kind, did)] = dev.id

    # --- 3) Flytt entiteter fra legacy switch_/sensor_-devices til device_<id> ---
    for e in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if e.platform != DOMAIN:
            continue
        if not e.device_id:
            continue

        dev = dev_reg.devices.get(e.device_id)
        if not dev:
            continue

        legacy_id: int | None = None
        for (domain, ident) in dev.identifiers:
            if domain != DOMAIN:
                continue
            parsed = _parse_sikom_identifier(str(ident))
            if not parsed:
                continue
            kind, did = parsed
            if kind in ("switch", "sensor"):
                legacy_id = did
                break

        if legacy_id is None:
            continue

        target_device_id = by_kind_id.get(("device", legacy_id))

        if not target_device_id:
            # Edge-case: bare switch_/sensor_-device finnes.
            # Konverter den til device_<id> ved å BEHOLDE andre identifiers og bare bytte ut legacy-identifikator.
            if ("device", legacy_id) not in by_kind_id:
                new_identifiers = set(dev.identifiers)

                new_identifiers.discard((DOMAIN, f"switch_{legacy_id}"))
                new_identifiers.discard((DOMAIN, f"sensor_{legacy_id}"))
                new_identifiers.add((DOMAIN, f"device_{legacy_id}"))

                dev_reg.async_update_device(
                    dev.id,
                    new_identifiers=new_identifiers,
                )
                by_kind_id[("device", legacy_id)] = dev.id
                target_device_id = dev.id

        if target_device_id and target_device_id != e.device_id:
            ent_reg.async_update_entity(e.entity_id, device_id=target_device_id)
            moved += 1

    # --- 4) Slett tomme legacy devices (switch_/sensor_) når canonical device_<id> finnes ---
    def _device_is_used(device_id: str) -> bool:
        return any(ent.device_id == device_id for ent in ent_reg.entities.values())

    for dev in list(dev_reg.devices.values()):
        if entry.entry_id not in dev.config_entries:
            continue

        legacy_kind: str | None = None
        legacy_id: int | None = None
        for (domain, ident) in dev.identifiers:
            if domain != DOMAIN:
                continue
            parsed = _parse_sikom_identifier(str(ident))
            if parsed and parsed[0] in ("switch", "sensor"):
                legacy_kind, legacy_id = parsed
                break

        if legacy_kind is None or legacy_id is None:
            continue

        canonical_id = by_kind_id.get(("device", legacy_id))
        if not canonical_id:
            continue

        if not _device_is_used(dev.id):
            dev_reg.async_remove_device(dev.id)
            removed_devices += 1

    if moved or disabled or removed_devices:
        _LOGGER.info(
            "Sikom: %s result: moved=%s, disabled_deprecated=%s, removed_legacy_devices=%s",
            _REGISTRY_CLEANUP_TAG,
            moved,
            disabled,
            removed_devices,
        )
    else:
        _LOGGER.debug("Sikom: %s result: no changes", _REGISTRY_CLEANUP_TAG)


def _get_available_device_ids_from_props(data: dict[str, Any] | None) -> set[int]:
    """
    AppView-normalisert data fra coordinator inneholder:
      data["props"] = {(device_id, key): value, ...}
    Vi bruker det til å se hvilke device_id-er som faktisk finnes i AppView nå.
    """
    if not isinstance(data, dict):
        return set()

    props = data.get("props")
    if not isinstance(props, dict):
        return set()

    out: set[int] = set()
    for k in props.keys():
        if not isinstance(k, tuple) or len(k) != 2:
            continue
        did = k[0]
        try:
            out.add(int(did))
        except (TypeError, ValueError):
            continue
    return out


def _get_expected_ids_from_coordinator(coordinator: SikomDataCoordinator) -> set[int]:
    """Forventede device_id-er (kun de brukeren har valgt i config flow)."""
    out: set[int] = set()
    try:
        device_map = coordinator.device_map or {}
    except Exception:  # noqa: BLE001
        device_map = {}

    if isinstance(device_map, dict):
        for k in ("climate", "switch", "sensor"):
            for did in device_map.get(k, []) or []:
                try:
                    out.add(int(did))
                except (TypeError, ValueError):
                    continue
    return out


async def _disable_stale_sensor_duplicates(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: SikomDataCoordinator
) -> None:
    """
    Rydd opp i "doble" sensorer som har samme <key>, men ulik device_id (typisk v1.0.8 vs v1.1.x).

    KONservativ regel (failsafes):
      - Ikke rydd hvis controller er offline ("0")
      - Ikke rydd hvis AppView virker ufullstendig i forhold til forventede IDs
      - Aldri disable entiteter der device_id er blant forventede IDs (valgt av bruker)
    """
    ent_reg = er.async_get(hass)

    available_ids = _get_available_device_ids_from_props(coordinator.data)
    if not available_ids:
        _LOGGER.debug("Sikom: skip stale-duplicate cleanup (ingen device_id-er i props)")
        return

    controller_online = None
    if isinstance(coordinator.data, dict):
        controller_online = coordinator.data.get("_controller_online")

    if str(controller_online) == "0":
        _LOGGER.debug("Sikom: skip stale-duplicate cleanup (controller_online=0)")
        return

    expected_ids = _get_expected_ids_from_coordinator(coordinator)
    if expected_ids:
        present_expected = available_ids & expected_ids

        if not present_expected:
            _LOGGER.debug(
                "Sikom: skip stale-duplicate cleanup (0/%s forventede enheter funnet i AppView)",
                len(expected_ids),
            )
            return

        threshold = 1
        if len(expected_ids) == 2:
            threshold = 1
        elif len(expected_ids) >= 3:
            threshold = max(2, len(expected_ids) // 2)

        if len(present_expected) < threshold:
            _LOGGER.debug(
                "Sikom: skip stale-duplicate cleanup (AppView virker ufullstendig: %s/%s forventede enheter)",
                len(present_expected),
                len(expected_ids),
            )
            return

    entries = [
        e
        for e in ent_reg.entities.values()
        if e.platform == DOMAIN and e.config_entry_id == entry.entry_id and e.unique_id
    ]

    key_to_dids: dict[str, set[int]] = {}
    uid_to_entry: dict[str, Any] = {}

    for e in entries:
        uid = e.unique_id or ""
        parsed = _parse_sensor_uid(uid)
        if not parsed:
            continue
        did, key = parsed
        key_to_dids.setdefault(key, set()).add(did)
        uid_to_entry[uid] = e

    disabled_count = 0

    for key, dids in key_to_dids.items():
        present = {d for d in dids if d in available_ids}
        missing = {d for d in dids if d not in available_ids}

        if not present:
            continue

        for did in missing:
            if expected_ids and did in expected_ids:
                continue

            uid = f"sikom_sensor_{did}_{key}"
            e = uid_to_entry.get(uid)
            if not e:
                continue
            if e.disabled_by is None:
                _LOGGER.info(
                    "Sikom: disabling stale sensor entity %s (unique_id=%s) because replacement exists in AppView",
                    e.entity_id,
                    uid,
                )
                ent_reg.async_update_entity(
                    e.entity_id,
                    disabled_by=RegistryEntryDisabler.INTEGRATION,
                )
                disabled_count += 1

    if disabled_count:
        _LOGGER.info(
            "Sikom: disabled %s stale/duplicate sensor entities after AppView refresh",
            disabled_count,
        )
    else:
        _LOGGER.debug("Sikom: stale-duplicate cleanup finished (no changes)")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sett opp Sikom fra en config entry."""
    _LOGGER.debug("Sikom: async_setup_entry start entry_id=%s version=%s", entry.entry_id, entry.version)

    merged_options: Dict[str, Any] = {**entry.data, **entry.options}

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

    username = str(merged_options.get(CONF_USERNAME, "")).strip()
    password = str(merged_options.get(CONF_PASSWORD, "")).strip()

    # Registry-migrering (ingen API-kall). Må skje før plattformer settes opp.
    try:
        await _migrate_registry_links(hass, entry)
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Sikom: %s feilet (fortsetter uten): %s", _REGISTRY_CLEANUP_TAG, exc)

    # --- gateway_id: først normalt, deretter self-heal hvis mangler ---
    try:
        gateway_id = _get_gateway_id(entry)
    except ValueError:
        _LOGGER.warning("Sikom: gateway_id mangler i config entry – forsøker å hente automatisk via API")

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

    # PK2: legg coordinator i hass.data før refresh (best practice)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:  # noqa: BLE001
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise ConfigEntryNotReady(f"Sikom first_refresh feilet: {exc}") from exc

    # Etter fersk AppView-data kan vi disable "stale duplicates"
    try:
        await _disable_stale_sensor_duplicates(hass, entry, coordinator)
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Sikom: disabling stale sensor duplicates feilet (fortsetter uten): %s", exc)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    _LOGGER.debug("Sikom: async_setup_entry complete entry_id=%s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Fjern Sikom-integrasjonen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Last inn config entry på nytt når options endres."""
    await hass.config_entries.async_reload(entry.entry_id)
