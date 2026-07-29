"""상수 정의가 서로 어긋나지 않는지 확인 — 예: 새 필드를 const에만 추가하고
config_flow/forwarder에 연결하는 걸 깜빡하는 실수를 잡기 위한 안전망.
"""

from custom_components.garage.const import (
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_RPM,
    FORWARD_ENTITY_KEYS,
    TRIGGER_EXCLUDED_KEYS,
)


def test_forward_entity_keys_contains_every_conf_entity_constant():
    assert set(FORWARD_ENTITY_KEYS) == {CONF_ENTITY_LOCATION, CONF_ENTITY_RPM}


def test_forward_entity_keys_has_no_duplicates():
    assert len(FORWARD_ENTITY_KEYS) == len(set(FORWARD_ENTITY_KEYS))


def test_location_is_excluded_from_trigger_but_still_forwardable():
    assert CONF_ENTITY_LOCATION in TRIGGER_EXCLUDED_KEYS
    assert CONF_ENTITY_LOCATION in FORWARD_ENTITY_KEYS


def test_rpm_is_not_excluded_from_trigger():
    assert CONF_ENTITY_RPM not in TRIGGER_EXCLUDED_KEYS
