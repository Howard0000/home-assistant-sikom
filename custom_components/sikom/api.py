from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Logg kun én gang per oppstart dersom vi auto-appender !!!
_PASSWORD_EXCLAMATION_LOGGED = False

BASE_URL = "https://api.connome.com/api"

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "nb-NO,nb;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


class ApiError(Exception):
    """Generell API-feil."""


class AuthError(ApiError):
    """Autentiserings-/tilgangsfeil."""


class SikomApi:
    def __init__(self, hass, username: str, password: str) -> None:
        self._hass = hass
        self._username = (username or "").strip()

        password = (password or "").strip()

        global _PASSWORD_EXCLAMATION_LOGGED
        appended = bool(password) and not password.endswith("!!!")
        self._password = f"{password}!!!" if appended else password

        if appended and not _PASSWORD_EXCLAMATION_LOGGED:
            _LOGGER.debug(
                "SikomApi: appended '!!!' to password automatically (for compatibility)"
            )
            _PASSWORD_EXCLAMATION_LOGGED = True

        self._session: Optional[aiohttp.ClientSession] = None
        self._auth: Optional[aiohttp.BasicAuth] = None

    # -----------------------
    # Session / auth
    # -----------------------
    def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = async_get_clientsession(self._hass)

    async def login(self) -> None:
        self._ensure_session()
        self._auth = aiohttp.BasicAuth(self._username, self._password)
        await self._request("GET", "VerifyCredentials")

    # -----------------------
    # AppView
    # -----------------------
    async def get_appview_all_v21(self) -> dict[str, Any] | None:
        data = await self._request("GET", "AppView/v2.1/All")
        if not isinstance(data, dict):
            return None
        d = data.get("Data")
        if not isinstance(d, dict):
            return None
        result = d.get("bpapi_result")
        return result if isinstance(result, dict) else None

    async def get_gateway_id_from_v21(self) -> int | None:
        """Plukker første gateway_id fra AppView/v2.1/All."""
        av21 = await self.get_appview_all_v21()
        if not isinstance(av21, dict):
            return None

        gateways = av21.get("gateways")
        if not isinstance(gateways, list) or not gateways:
            return None

        gid = gateways[0].get("bpapi_gateway_id")
        try:
            return int(gid)
        except (TypeError, ValueError):
            return None

    async def get_appview_v4(self, gateway_id: int) -> dict[str, Any] | None:
        data = await self._request("GET", f"AppView/v4.0/{gateway_id}")
        if not isinstance(data, dict):
            return None
        d = data.get("Data")
        if not isinstance(d, dict):
            return None
        result = d.get("bpapi_result")
        return result if isinstance(result, dict) else None

    async def list_devices_from_v4(self, gateway_id: int) -> list[dict[str, Any]]:
        """Device-liste (for clean install) fra AppView v4."""
        av4 = await self.get_appview_v4(gateway_id)
        if not isinstance(av4, dict):
            return []

        devices = av4.get("devices")
        if not isinstance(devices, list):
            return []

        out: list[dict[str, Any]] = []
        for dev in devices:
            if not isinstance(dev, dict):
                continue

            did = dev.get("bpapi_device_id")
            try:
                did_int = int(did)
            except (TypeError, ValueError):
                continue

            name = (
                dev.get("best_effort_name")
                or dev.get("product_friendly_name")
                or f"Enhet {did_int}"
            )

            dtype = (
                dev.get("description")
                or dev.get("product_code")
                or dev.get("product_friendly_name")
                or ""
            )

            out.append(
                {
                    "id": did_int,
                    "name": str(name).strip(),
                    "type": str(dtype),
                    "gateway_id": int(gateway_id),
                    "raw": dev,
                }
            )

        _LOGGER.debug("list_devices_from_v4(%s): %s enheter", gateway_id, len(out))
        return out

    # -----------------------
    # Property / Value
    # -----------------------
    async def get_property_value(self, device_id: int, prop: str) -> Any:
        data = await self._request("GET", f"Device/{device_id}/Property/{prop}/Value")
        if isinstance(data, dict):
            data_node = data.get("Data")
            if isinstance(data_node, dict):
                if (scalar_val := data_node.get("scalar_result")) is not None:
                    return scalar_val
                if (val := data_node.get("Value")) is not None:
                    return val
            if (val := data.get("Value")) is not None:
                return val
            if (val := data.get("value")) is not None:
                return val
        return data

    async def set_property_value(self, device_id: int, prop: str, value: Any) -> None:
        await self._request("POST", f"Device/{device_id}/AddProperty/{prop}/{value}")

    async def set_property_with_confirm(
        self,
        device_id: int,
        prop: str,
        value: Any,
        *,
        tries: int = 10,
        delay_s: float = 1.0,
    ) -> bool:
        try:
            await self.set_property_value(device_id, prop, value)
        except Exception as exc:
            _LOGGER.warning(
                "Feil ved set_property_value(%s,%s): %s", device_id, prop, exc
            )
            return False

        for _ in range(max(1, tries)):
            await asyncio.sleep(delay_s)
            try:
                current_value = await self.get_property_value(device_id, prop)
                if str(current_value) == str(value):
                    return True
            except Exception:
                pass
        return False

    # -----------------------
    # HTTP helper
    # -----------------------
    async def _request(self, method: str, path: str) -> Any:
        self._ensure_session()
        url = f"{BASE_URL}/{path.lstrip('/')}"

        auth = self._auth or aiohttp.BasicAuth(self._username, self._password)
        headers = dict(DEFAULT_HEADERS)

        try:
            async with self._session.request(
                method,
                url,
                auth=auth,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status in (401, 403):
                    msg = f"Authentication/Access failed (status {resp.status})"
                    try:
                        data = await resp.json(content_type=None)
                        bp_msg = (
                            data.get("Data", {}).get("bpapi_message")
                            if isinstance(data, dict)
                            else None
                        )
                        if bp_msg:
                            msg = f"{msg}: {bp_msg}"
                    except Exception:
                        pass
                    raise AuthError(msg)

                resp.raise_for_status()
                return await resp.json(content_type=None)

        except AuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise ApiError(f"API-kall feilet for {method} {url}: {exc}") from exc
        except Exception as exc:
            raise ApiError(f"Uventet feil for {method} {url}: {exc}") from exc


SikomClient = SikomApi
