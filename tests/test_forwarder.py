"""GarageTelemetryForwarder(push: HA → Garage) 단위 테스트."""

import asyncio

from custom_components.garage import GarageTelemetryForwarder, _to_float
from custom_components.garage.api import GarageError
from custom_components.garage.const import (
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_IN_VEHICLE,
    CONF_ENTITY_LATITUDE,
    CONF_ENTITY_LONGITUDE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
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


class TestReadCoordinate:
    def test_plain_sensor_state(self):
        hass = FakeHass({"sensor.lat": FakeState("37.5665")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_LATITUDE: "sensor.lat"}
        )
        assert forwarder._read_coordinate(CONF_ENTITY_LATITUDE, "latitude") == 37.5665

    def test_device_tracker_reads_attribute_not_state(self):
        hass = FakeHass(
            {
                "device_tracker.phone": FakeState(
                    "home",
                    domain="device_tracker",
                    attributes={"latitude": 37.1, "longitude": 127.2},
                )
            }
        )
        forwarder = GarageTelemetryForwarder(
            hass,
            api=None,
            entity_map={
                CONF_ENTITY_LATITUDE: "device_tracker.phone",
                CONF_ENTITY_LONGITUDE: "device_tracker.phone",
            },
        )
        assert forwarder._read_coordinate(CONF_ENTITY_LATITUDE, "latitude") == 37.1
        assert forwarder._read_coordinate(CONF_ENTITY_LONGITUDE, "longitude") == 127.2

    def test_unconfigured_field_returns_none(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        assert forwarder._read_coordinate(CONF_ENTITY_LATITUDE, "latitude") is None

    def test_entity_removed_from_ha_returns_none(self):
        forwarder = GarageTelemetryForwarder(
            FakeHass({}), api=None, entity_map={CONF_ENTITY_LATITUDE: "sensor.gone"}
        )
        assert forwarder._read_coordinate(CONF_ENTITY_LATITUDE, "latitude") is None


class TestReadBool:
    """탑승 여부(inVehicle) 판단 — binary_sensor/device_tracker/숫자 sensor 세 갈래."""

    def test_binary_sensor_on(self):
        hass = FakeHass({"binary_sensor.bt": FakeState("on", domain="binary_sensor")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "binary_sensor.bt"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is True

    def test_binary_sensor_off(self):
        hass = FakeHass({"binary_sensor.bt": FakeState("off", domain="binary_sensor")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "binary_sensor.bt"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is False

    def test_device_tracker_home_is_true(self):
        hass = FakeHass({"device_tracker.car": FakeState("home", domain="device_tracker")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "device_tracker.car"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is True

    def test_device_tracker_not_home_is_false(self):
        hass = FakeHass(
            {"device_tracker.car": FakeState("not_home", domain="device_tracker")}
        )
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "device_tracker.car"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is False

    def test_numeric_sensor_above_zero_is_true(self):
        """실사용 사례: 엔진로드/RPM 센서로 탑승 여부를 판단."""
        hass = FakeHass({"sensor.engine_load": FakeState("23.5")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "sensor.engine_load"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is True

    def test_numeric_sensor_zero_is_false(self):
        hass = FakeHass({"sensor.engine_load": FakeState("0")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "sensor.engine_load"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is False

    def test_unavailable_state_returns_none(self):
        hass = FakeHass({"sensor.engine_load": FakeState("unavailable")})
        forwarder = GarageTelemetryForwarder(
            hass, api=None, entity_map={CONF_ENTITY_IN_VEHICLE: "sensor.engine_load"}
        )
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is None

    def test_unconfigured_returns_none(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        assert forwarder._read_bool(CONF_ENTITY_IN_VEHICLE) is None


class TestGatherPayload:
    def test_full_mapping_produces_full_payload(self):
        hass = FakeHass(
            {
                "device_tracker.phone": FakeState(
                    "home",
                    domain="device_tracker",
                    attributes={"latitude": 37.1, "longitude": 127.2},
                ),
                "sensor.speed": FakeState("42.3"),
                "sensor.rpm": FakeState("1800"),
                "sensor.fuel": FakeState("55"),
                "sensor.odo": FakeState("12345.6"),
                "sensor.engine_load": FakeState("18"),
            }
        )
        entity_map = {
            CONF_ENTITY_LATITUDE: "device_tracker.phone",
            CONF_ENTITY_LONGITUDE: "device_tracker.phone",
            CONF_ENTITY_SPEED: "sensor.speed",
            CONF_ENTITY_RPM: "sensor.rpm",
            CONF_ENTITY_FUEL_LEVEL: "sensor.fuel",
            CONF_ENTITY_ODOMETER: "sensor.odo",
            CONF_ENTITY_IN_VEHICLE: "sensor.engine_load",
        }
        forwarder = GarageTelemetryForwarder(hass, api=None, entity_map=entity_map)

        payload = forwarder._gather_payload()

        assert payload == {
            "lat": 37.1,
            "lon": 127.2,
            "speed": 42.3,
            "rpm": 1800.0,
            "fuelLevel": 55.0,
            "odometer": 12345,
            "inVehicle": True,
        }

    def test_empty_mapping_produces_all_none(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        payload = forwarder._gather_payload()
        assert all(value is None for value in payload.values())


class TestEntityIds:
    def test_dedupes_entity_shared_across_fields(self):
        entity_map = {
            CONF_ENTITY_LATITUDE: "device_tracker.phone",
            CONF_ENTITY_LONGITUDE: "device_tracker.phone",
        }
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map=entity_map)
        assert forwarder.entity_ids == ["device_tracker.phone"]

    def test_empty_when_no_fields_configured(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        assert forwarder.entity_ids == []


class TestAsyncStart:
    def test_no_entities_configured_is_a_noop(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=None, entity_map={})
        unsub = forwarder.async_start()
        assert callable(unsub)
        unsub()  # 예외 없이 그냥 끝나야 한다.


class _FakeApiOk:
    async def async_send_telemetry(self, payload):
        return None


class _FakeApiFailing:
    async def async_send_telemetry(self, payload):
        raise GarageError("boom")


class TestAsyncPush:
    def test_success_marks_last_push_ok(self):
        forwarder = GarageTelemetryForwarder(FakeHass(), api=_FakeApiOk(), entity_map={})
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is True
        assert forwarder.last_push_at is not None

    def test_failure_marks_last_push_not_ok(self):
        forwarder = GarageTelemetryForwarder(
            FakeHass(), api=_FakeApiFailing(), entity_map={}
        )
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is False
        assert forwarder.last_push_at is not None


class TestOnlyWhenInVehicleGate:
    """"탑승 중일 때만 전송" 옵션 — 사용자 요청으로 추가된 게이트."""

    def test_disabled_always_sends_even_when_not_in_vehicle(self):
        hass = FakeHass({"binary_sensor.bt": FakeState("off", domain="binary_sensor")})
        forwarder = GarageTelemetryForwarder(
            hass,
            api=_FakeApiOk(),
            entity_map={CONF_ENTITY_IN_VEHICLE: "binary_sensor.bt"},
            only_when_in_vehicle=False,
        )
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is True
        assert forwarder.last_skipped_not_in_vehicle is False

    def test_enabled_and_in_vehicle_sends(self):
        hass = FakeHass({"binary_sensor.bt": FakeState("on", domain="binary_sensor")})
        forwarder = GarageTelemetryForwarder(
            hass,
            api=_FakeApiOk(),
            entity_map={CONF_ENTITY_IN_VEHICLE: "binary_sensor.bt"},
            only_when_in_vehicle=True,
        )
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is True
        assert forwarder.last_skipped_not_in_vehicle is False

    def test_enabled_and_not_in_vehicle_skips(self):
        hass = FakeHass({"binary_sensor.bt": FakeState("off", domain="binary_sensor")})
        forwarder = GarageTelemetryForwarder(
            hass,
            api=_FakeApiOk(),
            entity_map={CONF_ENTITY_IN_VEHICLE: "binary_sensor.bt"},
            only_when_in_vehicle=True,
        )
        _run(forwarder._async_push())
        # last_push_ok/last_push_at는 "실제로 보낸 적이 없다"는 뜻으로 그대로 None.
        assert forwarder.last_push_ok is None
        assert forwarder.last_push_at is None
        assert forwarder.last_skipped_not_in_vehicle is True

    def test_enabled_and_unavailable_state_skips(self):
        """탑승 여부를 판단할 수 없으면(unavailable) 안전하게 건너뛴다."""
        hass = FakeHass(
            {"sensor.engine_load": FakeState("unavailable", domain="sensor")}
        )
        forwarder = GarageTelemetryForwarder(
            hass,
            api=_FakeApiOk(),
            entity_map={CONF_ENTITY_IN_VEHICLE: "sensor.engine_load"},
            only_when_in_vehicle=True,
        )
        _run(forwarder._async_push())
        assert forwarder.last_skipped_not_in_vehicle is True

    def test_enabled_but_no_in_vehicle_entity_configured_always_sends(self):
        """탑승 여부 엔티티를 아예 안 골랐다면 판단 근거가 없으므로 옵션과 무관하게 보낸다."""
        forwarder = GarageTelemetryForwarder(
            FakeHass(),
            api=_FakeApiOk(),
            entity_map={CONF_ENTITY_SPEED: "sensor.speed"},
            only_when_in_vehicle=True,
        )
        _run(forwarder._async_push())
        assert forwarder.last_push_ok is True
        assert forwarder.last_skipped_not_in_vehicle is False
