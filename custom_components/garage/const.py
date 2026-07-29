"""Constants for the Garage integration."""

from __future__ import annotations

DOMAIN = "garage"

# Config entry keys
CONF_HOST = "host"
CONF_API_TOKEN = "api_token"

# Options keys — HA entities to forward to Garage as telemetry (all optional).
CONF_ENTITY_LATITUDE = "entity_latitude"
CONF_ENTITY_LONGITUDE = "entity_longitude"
CONF_ENTITY_SPEED = "entity_speed"
CONF_ENTITY_RPM = "entity_rpm"
CONF_ENTITY_FUEL_LEVEL = "entity_fuel_level"
CONF_ENTITY_ODOMETER = "entity_odometer"
CONF_ENTITY_IN_VEHICLE = "entity_in_vehicle"

FORWARD_ENTITY_KEYS: tuple[str, ...] = (
    CONF_ENTITY_LATITUDE,
    CONF_ENTITY_LONGITUDE,
    CONF_ENTITY_SPEED,
    CONF_ENTITY_RPM,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_IN_VEHICLE,
)

# 켜면 entity_in_vehicle이 True일 때만 전송하고, False/판단 불가일 때는 건너뛴다.
# entity_in_vehicle을 아예 지정하지 않았다면 판단 기준이 없으므로 이 옵션과 무관하게
# 항상 전송한다.
CONF_ONLY_WHEN_IN_VEHICLE = "only_when_in_vehicle"

# entity_in_vehicle 에 binary_sensor/device_tracker 대신 숫자 sensor(예: 엔진로드, RPM)를
# 골랐을 때 "탑승중"으로 판단하는 기준값 — 이 값보다 크면 True.
IN_VEHICLE_NUMERIC_THRESHOLD = 0

# Garage 서버가 값이 바뀔 때마다 push 받지만, 같은 틱에 여러 엔티티가 연달아
# 바뀌는 경우까지 매번 요청하지 않도록 최소 간격을 둔다.
MIN_PUSH_INTERVAL_SECONDS = 10

# GET /api/ingest/status, /api/ingest/reminders 폴링 주기 — Garage가 자체적으로
# 계산/저장한 값을 HA 센서로 다시 보여주는 용도라 자주 갱신할 필요는 없다.
STATUS_UPDATE_INTERVAL_MINUTES = 5
REMINDERS_UPDATE_INTERVAL_MINUTES = 30
