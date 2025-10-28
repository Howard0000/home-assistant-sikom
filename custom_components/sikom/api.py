from __future__ import annotations

import aiohttp
import asyncio
import logging
from typing import Any, Dict, List, Optional

from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
BASE_URL = "https://api.connome.com/api/"

class ApiError(Exception): pass
class AuthError(ApiError): pass

class SikomApi:
    """Klient for Connome/Sikom API."""

    def __init__(self, hass, username: str, password: str) -> None:
        self._hass = hass
        self._username = username
        self._password = f"{password}!!!" if not password.endswith("!!!") else password
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth: Optional[aiohttp.BasicAuth] = None

    async def login(self) -> None:
        """Verifiserer legitimasjon."""
        self._ensure_session()
        self._auth = aiohttp.BasicAuth(self._username, self._password)
        try:
            await self._request("GET", "Customer/")
        except AuthError:
            _LOGGER.error("Sikom-innlogging feilet. Sjekk brukernavn og passord.")
            raise

    async def list_devices(self) -> List[Dict[str, Any]]:
        """Henter og parser den globale enhetslisten fra /Device/All/."""
        response_data = await self._request("GET", "Device/All/")
        device_list = self._find_array(response_data, candidates=["bpapi_array"])
        if not device_list:
            _LOGGER.error("Fikk ingen enhetsliste fra /Device/All/.")
            return []
        
        parsed_devices = [self._parse_device(dev) for dev in device_list]
        
        seen_ids = set()
        unique_devices = []
        for device in parsed_devices:
            if device and device['id'] not in seen_ids:
                unique_devices.append(device)
                seen_ids.add(device['id'])
        
        _LOGGER.info("Autodeteksjon fant %d unike enheter.", len(unique_devices))
        return unique_devices

    def _parse_device(self, device_data: Any) -> Dict[str, Any] | None:
        if not isinstance(device_data, dict): return None
        device_info = device_data.get('device', device_data)
        props = device_info.get('Properties')
        if not props: return None
        try:
            bpapi_device_id = int(props['bpapi_device_id']['Value'])
            name_prop = props.get('best_effort_name') or props.get('user_defined_name')
            name = (name_prop.get('Value') or f"Enhet {bpapi_device_id}").strip()
            type_prop = props.get('vendor_and_device_model_readable') or props.get('device_type_readable') or props.get('device_type')
            dtype = (type_prop.get('Value') or "").lower()
            gid = props.get('bpapi_gateway_id', {}).get('Value')
            return {"id": bpapi_device_id, "name": name, "type": dtype, "gateway_id": gid}
        except (KeyError, ValueError, TypeError):
            return None

    # --- NY FUNKSJON ---
    async def async_refresh_appview(self, gateway_id: int) -> None:
        """Trigger AppView-refresh i skyen (ikke kall oftere enn hvert ~5 min)."""
        await self._request("GET", f"AppView/v4.0/{gateway_id}")
    # --- SLUTT PÅ NY FUNKSJON ---

    async def get_property_value(self, device_id: int, prop: str) -> Any:
        """Hent verdi for en property, basert på fungerende REST-sensor."""
        data = await self._request("GET", f"Device/{device_id}/Property/{prop}/Value")
        if isinstance(data, dict):
            if (data_node := data.get("Data")) and isinstance(data_node, dict):
                if (scalar_val := data_node.get("scalar_result")) is not None:
                    return scalar_val
            if (val := self._pick(data, "Value", "value")) is not None:
                return val
            if isinstance(data_node, dict):
                return data_node.get("Value")
        return data

    async def set_property_value(self, device_id: int, prop: str, value: Any) -> None:
        await self._request("POST", f"Device/{device_id}/AddProperty/{prop}/{value}")
        
    async def set_property_with_confirm(self, device_id: int, prop: str, value: Any, **kwargs) -> bool:
        try:
            await self.set_property_value(device_id, prop, value)
            await asyncio.sleep(1.5)
            current_value = await self.get_property_value(device_id, prop)
            return str(current_value) == str(value)
        except Exception as e:
            _LOGGER.warning("Feil under set_property_with_confirm: %s", e)
            return False
            
    def _find_array(self, data: Any, *, candidates: List[str]) -> List[Any]:
        if isinstance(data, list): return data
        if not isinstance(data, dict): return []
        for key in candidates:
            if isinstance(arr := data.get(key), list): return arr
        data_node = data.get("Data") or data.get("data")
        if isinstance(data_node, dict):
            for key in candidates:
                if isinstance(arr := data_node.get(key), list): return arr
        return []

    def _pick(self, d: Dict[str, Any], *keys, default=None):
        for k in keys:
            if (v := d.get(k)) not in (None, ""): return v
        return default
        
    def _ensure_session(self) -> None:
        if self._session is None or self._session.closed: self._session = async_get_clientsession(self._hass)

    async def _request(self, method: str, path: str) -> Any:
        self._ensure_session()
        url = BASE_URL + path.lstrip("/")
        auth = self._auth or aiohttp.BasicAuth(self._username, self._password)
        try:
            async with self._session.request(method, url, auth=auth, timeout=30) as resp:
                if resp.status in (401, 403): raise AuthError("Authentication failed")
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except Exception as exc:
            raise ApiError(f"API-kall feilet for {method} {url}: {exc}") from exc

SikomClient = SikomApi