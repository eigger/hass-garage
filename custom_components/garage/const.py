"""Constants for the Garage integration."""

from __future__ import annotations

DOMAIN = "garage"

# Config entry keys
CONF_HOST = "host"
CONF_API_TOKEN = "api_token"

# Options keys — HA entities to forward to Garage as telemetry (all optional).
# 위치는 device_tracker 하나로만 받는다 — 위경도를 함께 들고 있는 표준 HA 엔티티라
# 위도/경도를 따로 고를 필요가 없다.
CONF_ENTITY_LOCATION = "entity_location"
CONF_ENTITY_RPM = "entity_rpm"
CONF_ENTITY_SPEED = "entity_speed"
CONF_ENTITY_FUEL_LEVEL = "entity_fuel_level"
CONF_ENTITY_ODOMETER = "entity_odometer"

FORWARD_ENTITY_KEYS: tuple[str, ...] = (
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_ODOMETER,
)

# 전송 트리거(상태 변화 감시 대상)에서는 제외하는 필드 — 위치는 주행 중 계속 바뀌므로
# 이걸 트리거로 삼으면 사실상 끊임없이 전송하게 된다. 위치가 아닌 값(RPM 등)이 바뀔 때만
# 전송을 트리거하고, 전송 시점의 최신 위치를 함께 실어 보낸다.
TRIGGER_EXCLUDED_KEYS: tuple[str, ...] = (CONF_ENTITY_LOCATION,)

# Garage 서버로 push하되, 같은 틱에 여러 엔티티가 연달아 바뀌는 경우까지 매번
# 요청하지 않도록 최소 간격을 둔다.
MIN_PUSH_INTERVAL_SECONDS = 10

# GET /api/ingest/status, /api/ingest/reminders 폴링 주기 — Garage가 자체적으로
# 계산/저장한 값을 HA 센서로 다시 보여주는 용도라 자주 갱신할 필요는 없다.
STATUS_UPDATE_INTERVAL_MINUTES = 5
REMINDERS_UPDATE_INTERVAL_MINUTES = 30
