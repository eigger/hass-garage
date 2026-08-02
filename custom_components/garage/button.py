"""Button platform for Garage — manual triggers that skip the usual wait.

- **지금 전송**: 디바운스 대기 없이 텔레메트리를 즉시 한 번 push한다. HA 재시작
  직후처럼 실제 값이 안 바뀌어서 자동 전송이 안 걸리는 상황에서 유용하다.
- **지금 새로고침**: 상태(5분)·리마인더(30분) 폴링 주기를 기다리지 않고 즉시
  다시 조회한다.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GarageRuntimeData, GarageTelemetryForwarder
from .const import DOMAIN


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Garage (self-hosted)",
        model="Vehicle",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Garage buttons for the entry."""
    data: GarageRuntimeData = entry.runtime_data

    async_add_entities(
        [
            GaragePushNowButton(data.forwarder, entry),
            GarageRefreshNowButton(data, entry),
        ]
    )


class GaragePushNowButton(ButtonEntity):
    """디바운스 대기 없이 지금 바로 텔레메트리를 한 번 전송한다."""

    _attr_has_entity_name = True
    _attr_translation_key = "push_now"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:upload"

    def __init__(self, forwarder: GarageTelemetryForwarder, entry: ConfigEntry) -> None:
        self._forwarder = forwarder
        self._attr_unique_id = f"{entry.entry_id}_push_now"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return bool(self._forwarder.entity_ids)

    async def async_press(self) -> None:
        await self._forwarder.async_push_now()


class GarageRefreshNowButton(ButtonEntity):
    """5분/30분 폴링 주기를 기다리지 않고 상태·리마인더를 지금 새로고침한다."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh_now"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    def __init__(self, data: GarageRuntimeData, entry: ConfigEntry) -> None:
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_refresh_now"
        self._attr_device_info = _device_info(entry)

    async def async_press(self) -> None:
        await self._data.status_coordinator.async_request_refresh()
        await self._data.reminders_coordinator.async_request_refresh()
