"""GarageStatusCoordinator / GarageRemindersCoordinator(pull: Garage → HA) 단위 테스트.

에러 매핑이 핵심이다 — 인증 오류는 재인증(ConfigEntryAuthFailed)을,
그 외 오류는 일반 갱신 실패(UpdateFailed)를 트리거해야 한다.
"""

import asyncio

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.garage.api import GarageAuthError, GarageConnectionError
from custom_components.garage.coordinator import (
    GarageRemindersCoordinator,
    GarageStatusCoordinator,
)


def _run(coro):
    return asyncio.run(coro)


class _FakeApiStatusOk:
    async def async_get_status(self):
        return {"id": "veh1", "odometer": 12345}


class _FakeApiStatusAuthError:
    async def async_get_status(self):
        raise GarageAuthError("bad token")


class _FakeApiStatusConnectionError:
    async def async_get_status(self):
        raise GarageConnectionError("unreachable")


class _FakeApiRemindersOk:
    async def async_get_reminders(self):
        return [{"type": "engineOilFilter", "isDue": True}]


class TestGarageStatusCoordinator:
    def test_returns_api_data_unchanged(self):
        coordinator = GarageStatusCoordinator(hass=None, entry=None, api=_FakeApiStatusOk())
        result = _run(coordinator._async_update_data())
        assert result == {"id": "veh1", "odometer": 12345}

    def test_auth_error_raises_config_entry_auth_failed(self):
        coordinator = GarageStatusCoordinator(
            hass=None, entry=None, api=_FakeApiStatusAuthError()
        )
        with pytest.raises(ConfigEntryAuthFailed):
            _run(coordinator._async_update_data())

    def test_connection_error_raises_update_failed(self):
        coordinator = GarageStatusCoordinator(
            hass=None, entry=None, api=_FakeApiStatusConnectionError()
        )
        with pytest.raises(UpdateFailed):
            _run(coordinator._async_update_data())


class TestGarageRemindersCoordinator:
    def test_returns_reminders_list(self):
        coordinator = GarageRemindersCoordinator(
            hass=None, entry=None, api=_FakeApiRemindersOk()
        )
        result = _run(coordinator._async_update_data())
        assert result == [{"type": "engineOilFilter", "isDue": True}]
