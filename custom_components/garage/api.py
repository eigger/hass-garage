"""Async client for a self-hosted Garage server's per-vehicle apiToken API.

Garage(https://github.com/eigger/garage)의 차량별 ``apiToken``으로 인증하는
비로그인 엔드포인트만 사용한다 — 문서: ``docs/INTEGRATIONS.md`` 3절/11절.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class GarageError(Exception):
    """Base error for the Garage API."""


class GarageAuthError(GarageError):
    """Raised when the vehicle apiToken is rejected."""


class GarageConnectionError(GarageError):
    """Raised when the Garage server cannot be reached."""


class GarageApi:
    """Thin wrapper around a Garage server's ``/api/ingest`` endpoints."""

    def __init__(self, session: ClientSession, host: str, api_token: str) -> None:
        """Initialize the client."""
        self._session = session
        self._host = host.rstrip("/")
        self._api_token = api_token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_token}"}

    async def async_get_status(self) -> dict[str, Any]:
        """GET /api/ingest/status — vehicle info + latest known telemetry."""
        return await self._get("/api/ingest/status")

    async def async_get_reminders(self) -> list[dict[str, Any]]:
        """GET /api/ingest/reminders — pending maintenance/admin reminders."""
        data = await self._get("/api/ingest/reminders")
        return data if isinstance(data, list) else []

    async def async_send_telemetry(self, payload: dict[str, Any]) -> None:
        """POST /api/ingest/telemetry — push current sensor values.

        모든 필드가 선택값이므로 비어 있는(None) 값은 보내지 않는다.
        """
        body = {key: value for key, value in payload.items() if value is not None}
        if not body:
            return
        url = f"{self._host}/api/ingest/telemetry"
        try:
            async with self._session.post(
                url, headers=self._headers, json=body
            ) as resp:
                if resp.status == 401:
                    raise GarageAuthError("Garage rejected the API token")
                resp.raise_for_status()
        except ClientError as err:
            raise GarageConnectionError(f"Garage request failed: {err}") from err

    async def _get(self, path: str) -> Any:
        url = f"{self._host}{path}"
        try:
            async with self._session.get(url, headers=self._headers) as resp:
                if resp.status == 401:
                    raise GarageAuthError("Garage rejected the API token")
                resp.raise_for_status()
                return await resp.json()
        except ClientError as err:
            raise GarageConnectionError(f"Garage request failed: {err}") from err
