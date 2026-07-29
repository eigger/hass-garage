"""상수 정의가 서로 어긋나지 않는지 확인 — 예: 새 필드를 const에만 추가하고
config_flow/forwarder에 연결하는 걸 깜빡하는 실수를 잡기 위한 안전망.
"""

from custom_components.garage.const import (
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_IN_VEHICLE,
    CONF_ENTITY_LATITUDE,
    CONF_ENTITY_LONGITUDE,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    FORWARD_ENTITY_KEYS,
)


def test_forward_entity_keys_contains_every_conf_entity_constant():
    expected = {
        CONF_ENTITY_LATITUDE,
        CONF_ENTITY_LONGITUDE,
        CONF_ENTITY_SPEED,
        CONF_ENTITY_RPM,
        CONF_ENTITY_FUEL_LEVEL,
        CONF_ENTITY_ODOMETER,
        CONF_ENTITY_IN_VEHICLE,
    }
    assert set(FORWARD_ENTITY_KEYS) == expected


def test_forward_entity_keys_has_no_duplicates():
    assert len(FORWARD_ENTITY_KEYS) == len(set(FORWARD_ENTITY_KEYS))
