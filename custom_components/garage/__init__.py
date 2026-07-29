"""The Garage (차량관리) integration.

두 방향을 모두 지원한다:

- **push (HA → Garage)**: 옵션에서 고른 HA 엔티티들의 상태가 바뀔 때마다
  ``GarageTelemetryForwarder``가 ``POST /api/ingest/telemetry``로 전송한다.
  YAML 설정(``rest_command`` 등) 없이 화면에서 엔티티만 고르면 된다.
- **pull (Garage → HA)**: ``GarageStatusCoordinator``/``GarageRemindersCoordinator``가
  Garage가 이미 계산해 둔 주행거리·연료량·위치·리마인더를 주기적으로 읽어와
  센서로 보여준다.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .api import GarageApi, GarageError
from .const import (
    CONF_API_TOKEN,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_IN_VEHICLE,
    CONF_ENTITY_LATITUDE,
    CONF_ENTITY_LONGITUDE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    CONF_HOST,
    CONF_ONLY_WHEN_IN_VEHICLE,
    FORWARD_ENTITY_KEYS,
    IN_VEHICLE_NUMERIC_THRESHOLD,
    MIN_PUSH_INTERVAL_SECONDS,
)
from .coordinator import GarageRemindersCoordinator, GarageStatusCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
]


class GarageTelemetryForwarder:
    """Watches configured entities and pushes their values to Garage.

    상태가 바뀔 때마다 즉시 보내되, 같은 틱에 여러 엔티티가 연달아 바뀌는 경우엔
    ``MIN_PUSH_INTERVAL_SECONDS``만큼 묶어서 마지막 값만 한 번 보낸다.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: GarageApi,
        entity_map: dict[str, str],
        only_when_in_vehicle: bool = False,
    ) -> None:
        self.hass = hass
        self._api = api
        self._entity_map = entity_map
        self._only_when_in_vehicle = only_when_in_vehicle
        self._unsub_call_later: callback | None = None
        self._last_push_monotonic: float | None = None
        self.last_push_at: str | None = None
        self.last_push_ok: bool | None = None
        self.last_skipped_not_in_vehicle: bool = False

    @property
    def entity_ids(self) -> list[str]:
        """Unique entity ids referenced by the configured mapping."""
        return list(dict.fromkeys(self._entity_map.values()))

    def async_start(self) -> callback:
        """Start tracking state changes. Returns an unsubscribe callback."""
        if not self._entity_map:
            return lambda: None
        return async_track_state_change_event(
            self.hass, self.entity_ids, self._handle_state_change
        )

    @callback
    def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        now = time.monotonic()
        if (
            self._last_push_monotonic is not None
            and now - self._last_push_monotonic < MIN_PUSH_INTERVAL_SECONDS
        ):
            if self._unsub_call_later is None:
                delay = MIN_PUSH_INTERVAL_SECONDS - (now - self._last_push_monotonic)
                self._unsub_call_later = async_call_later(
                    self.hass, delay, self._handle_delayed_push
                )
            return
        self.hass.async_create_task(self._async_push())

    @callback
    def _handle_delayed_push(self, _now: Any) -> None:
        self._unsub_call_later = None
        self.hass.async_create_task(self._async_push())

    async def _async_push(self) -> None:
        self._last_push_monotonic = time.monotonic()

        if self._should_skip_not_in_vehicle():
            self.last_skipped_not_in_vehicle = True
            return
        self.last_skipped_not_in_vehicle = False

        payload = self._gather_payload()
        try:
            await self._api.async_send_telemetry(payload)
        except GarageError as err:
            self.last_push_ok = False
            _LOGGER.warning("Failed to push telemetry to Garage: %s", err)
        else:
            self.last_push_ok = True
        self.last_push_at = dt_util.utcnow().isoformat()

    def _should_skip_not_in_vehicle(self) -> bool:
        """"탑승 중일 때만 전송" 옵션이 켜져 있고, 실제로 탑승 중이 아닐 때만 건너뛴다.

        entity_in_vehicle을 지정하지 않았다면 판단할 근거가 없으므로 옵션과
        무관하게 항상 보낸다.
        """
        if not self._only_when_in_vehicle:
            return False
        if CONF_ENTITY_IN_VEHICLE not in self._entity_map:
            return False
        return self._read_bool(CONF_ENTITY_IN_VEHICLE) is not True

    def _gather_payload(self) -> dict[str, Any]:
        return {
            "lat": self._read_coordinate(CONF_ENTITY_LATITUDE, "latitude"),
            "lon": self._read_coordinate(CONF_ENTITY_LONGITUDE, "longitude"),
            "speed": self._read_float(CONF_ENTITY_SPEED),
            "rpm": self._read_float(CONF_ENTITY_RPM),
            "fuelLevel": self._read_float(CONF_ENTITY_FUEL_LEVEL),
            "odometer": self._read_int(CONF_ENTITY_ODOMETER),
            "inVehicle": self._read_bool(CONF_ENTITY_IN_VEHICLE),
        }

    def _get_state(self, key: str):
        entity_id = self._entity_map.get(key)
        if not entity_id:
            return None
        return self.hass.states.get(entity_id)

    def _read_coordinate(self, key: str, attribute: str) -> float | None:
        """lat/lon — device_tracker면 속성에서, 아니면 state 값을 그대로 float 변환."""
        state = self._get_state(key)
        if state is None:
            return None
        if state.domain == "device_tracker":
            value = state.attributes.get(attribute)
        else:
            value = state.state
        return _to_float(value)

    def _read_float(self, key: str) -> float | None:
        state = self._get_state(key)
        if state is None:
            return None
        return _to_float(state.state)

    def _read_int(self, key: str) -> int | None:
        value = self._read_float(key)
        return int(value) if value is not None else None

    def _read_bool(self, key: str) -> bool | None:
        """binary_sensor/device_tracker는 on/home 여부로, sensor는 숫자 임계값으로 판단한다.

        예: 엔진로드·RPM 같은 숫자 센서를 골랐다면 0보다 클 때 "탑승중"으로 본다
        (시동이 꺼지면 값이 0/unavailable이 되어 자동으로 False/None이 된다).
        """
        state = self._get_state(key)
        if state is None:
            return None
        if state.state in ("unknown", "unavailable"):
            return None
        if state.domain == "device_tracker":
            return state.state == "home"
        if state.domain == "sensor":
            value = _to_float(state.state)
            return value > IN_VEHICLE_NUMERIC_THRESHOLD if value is not None else None
        return state.state == "on"


def _to_float(value: Any) -> float | None:
    """지원하지 않는/알 수 없는 상태값(unknown, unavailable 등)은 None으로 취급한다."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class GarageRuntimeData:
    """Objects shared across the entry's platforms."""

    api: GarageApi
    status_coordinator: GarageStatusCoordinator
    reminders_coordinator: GarageRemindersCoordinator
    forwarder: GarageTelemetryForwarder


type GarageConfigEntry = ConfigEntry[GarageRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: GarageConfigEntry) -> bool:
    """Set up Garage from a config entry."""
    session = async_get_clientsession(hass)
    api = GarageApi(session, entry.data[CONF_HOST], entry.data[CONF_API_TOKEN])

    status_coordinator = GarageStatusCoordinator(hass, entry, api)
    await status_coordinator.async_config_entry_first_refresh()

    reminders_coordinator = GarageRemindersCoordinator(hass, entry, api)
    await reminders_coordinator.async_config_entry_first_refresh()

    entity_map = {key: entry.options[key] for key in FORWARD_ENTITY_KEYS if entry.options.get(key)}
    only_when_in_vehicle = entry.options.get(CONF_ONLY_WHEN_IN_VEHICLE, False)
    forwarder = GarageTelemetryForwarder(hass, api, entity_map, only_when_in_vehicle)
    unsub = forwarder.async_start()
    entry.async_on_unload(unsub)

    entry.runtime_data = GarageRuntimeData(
        api=api,
        status_coordinator=status_coordinator,
        reminders_coordinator=reminders_coordinator,
        forwarder=forwarder,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: GarageConfigEntry) -> None:
    """Reload the entry when options (forwarded entities) change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GarageConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
