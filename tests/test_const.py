"""상수 정의가 서로 어긋나지 않는지 확인 — 예: 새 필드를 const에만 추가하고
config_flow/forwarder에 연결하는 걸 깜빡하는 실수를 잡기 위한 안전망.
"""

from custom_components.garage.const import (
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    DEFAULT_PUSH_INTERVAL_SECONDS,
    FORWARD_ENTITY_KEYS,
    MAX_PUSH_INTERVAL_SECONDS_BOUND,
    MIN_PUSH_INTERVAL_SECONDS_BOUND,
    TRIGGER_EXCLUDED_KEYS,
)


def test_forward_entity_keys_contains_every_conf_entity_constant():
    assert set(FORWARD_ENTITY_KEYS) == {
        CONF_ENTITY_LOCATION,
        CONF_ENTITY_RPM,
        CONF_ENTITY_SPEED,
        CONF_ENTITY_FUEL_LEVEL,
        CONF_ENTITY_ODOMETER,
    }


def test_forward_entity_keys_has_no_duplicates():
    assert len(FORWARD_ENTITY_KEYS) == len(set(FORWARD_ENTITY_KEYS))


def test_location_is_excluded_from_trigger_but_still_forwardable():
    assert CONF_ENTITY_LOCATION in TRIGGER_EXCLUDED_KEYS
    assert CONF_ENTITY_LOCATION in FORWARD_ENTITY_KEYS


def test_only_location_is_excluded_from_trigger():
    assert set(TRIGGER_EXCLUDED_KEYS) == {CONF_ENTITY_LOCATION}


def test_rpm_speed_fuel_odometer_are_not_excluded_from_trigger():
    for key in (CONF_ENTITY_RPM, CONF_ENTITY_SPEED, CONF_ENTITY_FUEL_LEVEL, CONF_ENTITY_ODOMETER):
        assert key not in TRIGGER_EXCLUDED_KEYS


def test_default_push_interval_is_within_its_own_bounds():
    assert MIN_PUSH_INTERVAL_SECONDS_BOUND <= DEFAULT_PUSH_INTERVAL_SECONDS
    assert DEFAULT_PUSH_INTERVAL_SECONDS <= MAX_PUSH_INTERVAL_SECONDS_BOUND
