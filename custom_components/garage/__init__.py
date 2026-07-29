"""The Garage (차량관리) integration.

두 방향을 모두 지원한다:

- **push (HA → Garage)**: 옵션에서 고른 HA 엔티티들의 상태가 바뀔 때마다
  ``GarageTelemetryForwarder``가 ``POST /api/ingest/telemetry``로 위치/RPM/속도/
  연료량/주행거리를 전송한다. YAML 설정(``rest_command`` 등) 없이 화면에서
  엔티티만 고르면 된다. 위치(위경도)는 주행 중 계속 바뀌므로 전송 트리거에서는
  빼고, 나머지 값이 바뀔 때만 전송하며 그 시점의 최신 위치를 함께 실어 보낸다.
- **pull (Garage → HA)**: ``GarageStatusCoordinator``/``GarageRemindersCoordinator``가
  Garage가 이미 계산해 둔 마지막 위치·리마인더를 주기적으로 읽어와 센서로
  보여준다. 주행거리·연료량·속도는 애초에 HA 엔티티에서 보내는 원본 값이라
  Garage 쪽 계산 결과를 HA에 다시 표시하면 중복이므로 별도 표시 센서는 두지 않는다.
"""

from __future__ import annotations

import asyncio
import logging
import math
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
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    CONF_HOST,
    FORWARD_ENTITY_KEYS,
    MIN_PUSH_INTERVAL_SECONDS,
    TRIGGER_EXCLUDED_KEYS,
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
    ``MIN_PUSH_INTERVAL_SECONDS``만큼 묶어서 마지막 값만 한 번 보낸다. 위치는 전송
    "트리거"에서는 제외된다 — 트리거 대상은 ``_trigger_entity_ids`` 참고.
    """

    def __init__(self, hass: HomeAssistant, api: GarageApi, entity_map: dict[str, str]) -> None:
        self.hass = hass
        self._api = api
        self._entity_map = entity_map
        self._unsub_call_later: callback | None = None
        self._last_push_monotonic: float | None = None
        self.last_push_at: str | None = None
        self.last_push_ok: bool | None = None
        self._listeners: list[callback] = []
        # 요청이 겹쳐서 서버에 역순으로 도착하면(네트워크 타이밍) 트립 경로가 뒤바뀔 수
        # 있으므로, 실제 전송은 이 락으로 한 번에 하나씩만 나가도록 직렬화한다.
        self._send_lock = asyncio.Lock()

    def async_add_listener(self, update_callback: callback) -> callback:
        """Register a callback for telemetry updates."""
        self._listeners.append(update_callback)

        def _unsubscribe() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return _unsubscribe

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    @property
    def entity_ids(self) -> list[str]:
        """Unique entity ids referenced by the configured mapping."""
        return list(dict.fromkeys(self._entity_map.values()))

    @property
    def _trigger_entity_ids(self) -> list[str]:
        """전송을 트리거하는 엔티티 — 위치(TRIGGER_EXCLUDED_KEYS)는 제외."""
        return list(
            dict.fromkeys(
                entity_id
                for key, entity_id in self._entity_map.items()
                if key not in TRIGGER_EXCLUDED_KEYS
            )
        )

    def async_start(self) -> callback:
        """Start tracking state changes. Returns an unsubscribe callback."""
        trigger_ids = self._trigger_entity_ids
        if not trigger_ids:
            return lambda: None
        return async_track_state_change_event(
            self.hass, trigger_ids, self._handle_state_change
        )

    @callback
    def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        self._async_schedule_push()

    @callback
    def _handle_delayed_push(self, _now: Any) -> None:
        self._unsub_call_later = None
        self._async_schedule_push()

    @callback
    def _async_schedule_push(self) -> None:
        """디바운스 판단과 예약을 전부 동기(@callback) 안에서 끝낸다.

        타임스탬프 갱신을 여기서(비동기 ``_async_push`` 안이 아니라) 동기적으로
        하는 게 핵심이다 — 그래야 첫 push 직후 거의 동시에 두 번째 이벤트가 들어와도
        "직전 push 시각"을 즉시 보고 디바운스되며, 두 push가 동시에 나가서 서버에
        역순으로 도착(예: 트립 경로 화살표가 뒤집힘)하는 경쟁 상태가 생기지 않는다.
        """
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
        self._last_push_monotonic = now
        self.hass.async_create_task(self._async_push())

    async def _async_push(self) -> None:
        # 락으로 실제 전송을 직렬화한다 — 락 획득 순서(FIFO)대로 보내지므로, 여러 push가
        # 예약됐더라도 서버에는 예약된 순서 그대로 도착한다(네트워크 타이밍에 의한 역전 방지).
        async with self._send_lock:
            payload = self._gather_payload()
            try:
                await self._api.async_send_telemetry(payload)
            except GarageError as err:
                self.last_push_ok = False
                _LOGGER.warning("Failed to push telemetry to Garage: %s", err)
            else:
                self.last_push_ok = True
        # 사용자에게 보이는 진단 센서 값이므로 UTC가 아니라 HA에 설정된 로컬 시간으로 남긴다.
        self.last_push_at = dt_util.now().isoformat()
        self._notify_listeners()

    def _gather_payload(self) -> dict[str, Any]:
        lat, lon = self._read_location()
        return {
            "lat": lat,
            "lon": lon,
            "rpm": self._read_float(CONF_ENTITY_RPM),
            "speed": self._read_float(CONF_ENTITY_SPEED),
            "fuelLevel": self._read_float(CONF_ENTITY_FUEL_LEVEL),
            "odometer": self._read_float(CONF_ENTITY_ODOMETER),
        }

    def _get_state(self, key: str):
        entity_id = self._entity_map.get(key)
        if not entity_id:
            return None
        return self.hass.states.get(entity_id)

    def _read_location(self) -> tuple[float | None, float | None]:
        """device_tracker 엔티티 하나에서 위도/경도 속성을 함께 읽는다."""
        state = self._get_state(CONF_ENTITY_LOCATION)
        if state is None:
            return None, None
        return (
            _to_float(state.attributes.get("latitude")),
            _to_float(state.attributes.get("longitude")),
        )

    def _read_float(self, key: str) -> float | None:
        state = self._get_state(key)
        if state is None:
            return None
        return _to_float(state.state)


def _to_float(value: Any) -> float | None:
    """지원하지 않는/알 수 없는 상태값(unknown, unavailable 등)은 None으로 취급한다.

    nan/inf도 거른다 — 그대로 두면 텔레메트리 payload를 JSON으로 직렬화할 때
    표준 JSON에 없는 NaN/Infinity 리터럴이 나가 서버 쪽 파싱이 깨질 수 있다.
    """
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


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
    forwarder = GarageTelemetryForwarder(hass, api, entity_map)
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
