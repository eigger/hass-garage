"""Data update coordinators for Garage (pull side).

Garage가 이미 계산/저장해 둔 값(주행거리, 연료량, 위치, 리마인더)을 주기적으로
읽어와 HA 센서로 보여준다. push 쪽(HA → Garage)은 ``__init__.py``의
``GarageTelemetryForwarder``가 담당한다.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GarageApi, GarageAuthError, GarageError
from .const import (
    DOMAIN,
    REMINDERS_UPDATE_INTERVAL_MINUTES,
    STATUS_UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class GarageStatusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls GET /api/ingest/status."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GarageApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} status",
            update_interval=timedelta(minutes=STATUS_UPDATE_INTERVAL_MINUTES),
        )
        self._api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._api.async_get_status()
        except GarageAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GarageError as err:
            raise UpdateFailed(str(err)) from err


class GarageRemindersCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Polls GET /api/ingest/reminders."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: GarageApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} reminders",
            update_interval=timedelta(minutes=REMINDERS_UPDATE_INTERVAL_MINUTES),
        )
        self._api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self._api.async_get_reminders()
        except GarageAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GarageError as err:
            raise UpdateFailed(str(err)) from err
