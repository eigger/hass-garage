"""GarageTelemetryForwarder(push: HA → Garage) 단위 테스트."""

import asyncio
from datetime import datetime

from custom_components.garage import GarageTelemetryForwarder, _to_float
from custom_components.garage.api import GarageError
from custom_components.garage.const import (
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    DEFAULT_PUSH_INTERVAL_SECONDS,
)


class FakeState:
    def __init__(self, state, domain="sensor", attributes=None):
        self.state = state
        self.domain = domain
        self.attributes = attributes or {}


class FakeStates:
    def __init__(self, mapping):
        self._mapping = mapping

    def get(self, entity_id):
        return self._mapping.get(entity_id)


class FakeHass:
    def __init__(self, mapping=None):
        self.states = FakeStates(mapping or {})


def _run(coro):
    return asyncio.run(coro)


class TestToFloat:
    def test_numeric_string(self):
        assert _to_float("3.5") == 3.5

    def test_int_input(self):
        assert _to_float(5) == 5.0

    def test_none(self):
        assert _to_float(None) is None

    def test_non_numeric_string(self):
        assert _to_float("unavailable") is None

    def test_invalid_strings(self):
        assert _to_float("unknown") is None
        assert _to_float("none") is None
        assert _to_float("null") is None
        assert _to_float("nan") is None
        assert _to_float("inf") is None


class TestReadLocation:
    def test_device_tracker_reads_lat_lon_attributes(self):
        hass = FakeHass(
            {
                "device_tracker.car": FakeState(
                    "home",
                    domain="device_tracker",
                    attributes={"latitude": 37.1, "longitude": 127.2},
                )
            }
        )
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_LOCATION: "device_tracker.car"}
        )
        assert forwarder._read_location() == (37.1, 127.2)

    def test_unconfigured_returns_none_none(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        assert forwarder._read_location() == (None, None)

    def test_entity_removed_from_ha_returns_none_none(self):
        forwarder = GarageTelemetryForwarder(
            FakeHass({}),
            api=None,
            entity_map={CONF_ENTITY_LOCATION: "device_tracker.gone"},
        )
        assert forwarder._read_location() == (None, None)

    def test_missing_attribute_returns_none_for_that_axis(self):
        hass = FakeHass(
            {
                "device_tracker.car": FakeState(
                    "home", domain="device_tracker", attributes={"latitude": 37.1}
                )
            }
        )
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_LOCATION: "device_tracker.car"}
        )
        assert forwarder._read_location() == (37.1, None)


class TestGatherPayload:
    def test_full_mapping_produces_full_payload(self):
        hass = FakeHass(
            {
                "device_tracker.car": FakeState(
                    "home",
                    domain="device_tracker",
                    attributes={"latitude": 37.1, "longitude": 127.2},
                ),
                "sensor.rpm": FakeState("1800"),
                "sensor.speed": FakeState("42.3"),
                "sensor.fuel": FakeState("55"),
                "sensor.odo": FakeState("12345"),
            }
        )
        entity_map = {
            CONF_ENTITY_LOCATION: "device_tracker.car",
            CONF_ENTITY_RPM: "sensor.rpm",
            CONF_ENTITY_SPEED: "sensor.speed",
            CONF_ENTITY_FUEL_LEVEL: "sensor.fuel",
            CONF_ENTITY_ODOMETER: "sensor.odo",
        }
        forwarder = GarageTelemetryForwarder(hass, api=None, entity_map=entity_map)

        payload = forwarder._gather_payload()

        assert payload == {
            "lat": 37.1,
            "lon": 127.2,
            "rpm": 1800.0,
            "speed": 42.3,
            "fuelLevel": 55.0,
            "odometer": 12345.0,
        }

    def test_empty_mapping_produces_all_none(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        payload = forwarder._gather_payload()
        assert all(value is None for value in payload.values())


class TestEntityIds:
    def test_dedupes_entity_shared_across_fields(self):
        entity_map = {
            CONF_ENTITY_LOCATION: "device_tracker.car",
            CONF_ENTITY_RPM: "device_tracker.car",
        }
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        assert forwarder.entity_ids == ["device_tracker.car"]

    def test_empty_when_no_fields_configured(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        assert forwarder.entity_ids == []


class TestTriggerEntityIds:
    """위치는 전송 트리거에서 제외되고, 나머지 값(RPM/속도/연료/주행거리)이
    바뀔 때만 전송을 트리거한다."""

    def test_location_excluded_from_trigger(self):
        entity_map = {
            CONF_ENTITY_LOCATION: "device_tracker.car",
            CONF_ENTITY_RPM: "sensor.rpm",
        }
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        assert forwarder._trigger_entity_ids == ["sensor.rpm"]

    def test_speed_fuel_odometer_all_trigger(self):
        entity_map = {
            CONF_ENTITY_LOCATION: "device_tracker.car",
            CONF_ENTITY_SPEED: "sensor.speed",
            CONF_ENTITY_FUEL_LEVEL: "sensor.fuel",
            CONF_ENTITY_ODOMETER: "sensor.odo",
        }
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        assert set(forwarder._trigger_entity_ids) == {
            "sensor.speed",
            "sensor.fuel",
            "sensor.odo",
        }

    def test_only_location_configured_yields_no_trigger(self):
        entity_map = {CONF_ENTITY_LOCATION: "device_tracker.car"}
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        assert forwarder._trigger_entity_ids == []


class TestAsyncStart:
    def test_no_trigger_entities_configured_is_a_noop(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        unsub = forwarder.async_start()
        assert callable(unsub)
        unsub()  # 예외 없이 그냥 끝나야 한다.

    def test_location_only_is_also_a_noop(self):
        """위치만 골랐다면 트리거 대상이 없으므로 async_track_state_change_event를 걸지 않는다."""
        entity_map = {CONF_ENTITY_LOCATION: "device_tracker.car"}
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        unsub = forwarder.async_start()
        assert callable(unsub)
        unsub()


class _FakeApiOk:
    def __init__(self):
        self.calls = 0

    async def async_send_telemetry(self, payload):
        self.calls += 1


class _FakeApiFailing:
    async def async_send_telemetry(self, payload):
        raise GarageError("boom")


class TestAsyncPush:
    def test_success_marks_last_push_ok(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=_FakeApiOk(), entity_map={})
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is True
        assert isinstance(forwarder.last_push_at, datetime)

    def test_failure_marks_last_push_not_ok(self):
        forwarder = GarageTelemetryForwarder(
            FakeHass(), api=_FakeApiFailing(), entity_map={}
        )
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is False
        assert isinstance(forwarder.last_push_at, datetime)

    def test_concurrent_pushes_are_serialized_by_the_send_lock(self):
        """두 push가 거의 동시에 예약되어도 실제 전송은 락으로 한 번에 하나씩만 나간다.

        트립 경로 화살표가 뒤집히는 버그의 원인이었던, 두 HTTP 요청이 동시에 나가서
        네트워크 타이밍에 따라 서버에 역순으로 도착할 수 있는 경쟁 상태를 막는 락이
        실제로 걸려 있는지 확인한다.
        """
        order: list[str] = []

        class _SlowFirstThenFastApi:
            def __init__(self):
                self._calls = 0

            async def async_send_telemetry(self, payload):
                self._calls += 1
                call_id = self._calls
                order.append(f"start-{call_id}")
                if call_id == 1:
                    await asyncio.sleep(0.05)
                order.append(f"end-{call_id}")

        forwarder = GarageTelemetryForwarder(
            FakeHass(), api=_SlowFirstThenFastApi(), entity_map={}
        )

        async def _scenario():
            task1 = asyncio.create_task(forwarder._async_push())
            await asyncio.sleep(0)  # task1이 락을 먼저 잡도록 양보
            task2 = asyncio.create_task(forwarder._async_push())
            await asyncio.gather(task1, task2)

        _run(_scenario())

        assert order == ["start-1", "end-1", "start-2", "end-2"]


class TestScheduleDebounce:
    """디바운스 타임스탬프를 동기적으로(스케줄링 시점에) 남겨야 하는 이유를 검증한다.

    이전 버그: 타임스탬프를 비동기 _async_push 안에서 갱신했기 때문에, 첫 push
    직후 아주 짧은 간격으로 두 번째 이벤트가 들어오면 디바운스가 걸리지 않고 두
    push가 동시에 스케줄됐다.
    """

    def test_second_immediate_call_is_debounced_after_first_schedules(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=_FakeApiOk(), entity_map={})

        created_tasks: list[object] = []
        forwarder.hass = type(
            "_Hass", (), {"async_create_task": staticmethod(created_tasks.append)}
        )()

        try:
            forwarder._async_schedule_push()
            assert len(created_tasks) == 1
            assert forwarder._last_push_monotonic is not None

            forwarder._async_schedule_push()
            assert len(created_tasks) == 1  # 두 번째는 디바운스되어 새 task가 생기지 않는다.
        finally:
            for coro in created_tasks:
                coro.close()  # 실제로 스케줄되지 않은 코루틴이므로 명시적으로 닫아 경고를 막는다.

    def test_after_interval_elapses_a_new_push_is_scheduled(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=_FakeApiOk(), entity_map={})
        created_tasks: list[object] = []
        forwarder.hass = type(
            "_Hass", (), {"async_create_task": staticmethod(created_tasks.append)}
        )()

        try:
            forwarder._async_schedule_push()
            assert len(created_tasks) == 1

            forwarder._last_push_monotonic -= DEFAULT_PUSH_INTERVAL_SECONDS + 1
            forwarder._async_schedule_push()
            assert len(created_tasks) == 2
        finally:
            for coro in created_tasks:
                coro.close()

    def test_default_interval_used_when_not_specified(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=_FakeApiOk(), entity_map={})
        assert forwarder._push_interval_seconds == DEFAULT_PUSH_INTERVAL_SECONDS

    def test_custom_interval_shortens_the_debounce_window(self):
        """RPM처럼 초 단위로 바뀌는 값을 쓰는 사용자가 간격을 줄일 수 있어야 한다."""
        forwarder = GarageTelemetryForwarder(
            FakeHass(), api=_FakeApiOk(), entity_map={}, push_interval_seconds=2
        )
        created_tasks: list[object] = []
        forwarder.hass = type(
            "_Hass", (), {"async_create_task": staticmethod(created_tasks.append)}
        )()

        try:
            forwarder._async_schedule_push()
            assert len(created_tasks) == 1

            # 기본값(10초)보다는 지났지만 커스텀 간격(2초)보다는 짧게 지난 경우에도
            # 이미 디바운스가 풀려서 즉시 다시 전송되어야 한다.
            forwarder._last_push_monotonic -= 3
            forwarder._async_schedule_push()
            assert len(created_tasks) == 2
        finally:
            for coro in created_tasks:
                coro.close()
