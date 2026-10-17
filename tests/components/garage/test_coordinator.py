"""GarageStatusCoordinator / GarageRemindersCoordinator(pull: Garage → HA) 테스트.

에러 매핑이 핵심이다 — 인증 오류는 재인증(ConfigEntryAuthFailed)을,
그 외 오류는 일반 갱신 실패(UpdateFailed)를 트리거해야 한다.
"""

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.garage.api import GarageAuthError, GarageConnectionError
from custom_components.garage.coordinator import (
    GarageRemindersCoordinator,
    GarageStatusCoordinator,
)


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


class _FakeApiRemindersAuthError:
    async def async_get_reminders(self):
        raise GarageAuthError("bad token")


class _FakeApiRemindersConnectionError:
    async def async_get_reminders(self):
        raise GarageConnectionError("unreachable")


class TestGarageStatusCoordinator:
    async def test_returns_api_data_unchanged(self, hass, entry):
        coordinator = GarageStatusCoordinator(
            hass=hass, entry=entry, api=_FakeApiStatusOk()
        )
        result = await coordinator._async_update_data()
        assert result == {"id": "veh1", "odometer": 12345}

    async def test_auth_error_raises_config_entry_auth_failed(self, hass, entry):
        coordinator = GarageStatusCoordinator(
            hass=hass, entry=entry, api=_FakeApiStatusAuthError()
        )
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_connection_error_raises_update_failed(self, hass, entry):
        coordinator = GarageStatusCoordinator(
            hass=hass, entry=entry, api=_FakeApiStatusConnectionError()
        )
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


class TestGarageRemindersCoordinator:
    async def test_returns_reminders_list(self, hass, entry):
        coordinator = GarageRemindersCoordinator(
            hass=hass, entry=entry, api=_FakeApiRemindersOk()
        )
        result = await coordinator._async_update_data()
        assert result == [{"type": "engineOilFilter", "isDue": True}]

    async def test_auth_error_raises_config_entry_auth_failed(self, hass, entry):
        coordinator = GarageRemindersCoordinator(
            hass=hass, entry=entry, api=_FakeApiRemindersAuthError()
        )
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_connection_error_raises_update_failed(self, hass, entry):
        coordinator = GarageRemindersCoordinator(
            hass=hass, entry=entry, api=_FakeApiRemindersConnectionError()
        )
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_runtime_failure_and_reauth_flow_through_real_coordinators(
    hass, entry, api_response, status_payload, reminders_payload, entity_id
):
    """Verify coordinator refresh failure preserves last data and 401 starts reauth."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    status_coordinator = entry.runtime_data.status_coordinator
    reminders_coordinator = entry.runtime_data.reminders_coordinator

    api_response.clear_requests()
    api_response.get("http://garage.test/api/ingest/status", status=500)
    await status_coordinator.async_refresh()
    await hass.async_block_till_done()
    assert status_coordinator.last_update_success is False
    assert status_coordinator.data == status_payload

    api_response.clear_requests()
    api_response.get("http://garage.test/api/ingest/status", json=status_payload)
    await status_coordinator.async_refresh()
    await hass.async_block_till_done()
    assert status_coordinator.last_update_success is True

    api_response.clear_requests()
    api_response.get("http://garage.test/api/ingest/reminders", status=401)
    await reminders_coordinator.async_refresh()
    await hass.async_block_till_done()
    assert reminders_coordinator.last_update_success is False
    assert any(
        flow["context"].get("source") == "reauth"
        for flow in hass.config_entries.flow.async_progress()
    )
