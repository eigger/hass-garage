"""pytest 설정 — homeassistant/aiohttp 없이 단위 테스트 실행 가능하도록 mock."""

import sys
from unittest.mock import MagicMock


class _MockBase:
    """제네릭 서브클래싱(예: ConfigEntry[T], DataUpdateCoordinator[T])을 지원하는 기본 Mock 클래스."""

    def __init__(self, *args, **kwargs):
        pass

    def __class_getitem__(cls, item):
        return cls


class _MockUpdateFailed(Exception):
    """UpdateFailed mock — raise UpdateFailed(...) 구문을 허용."""


class _MockConfigEntryAuthFailed(Exception):
    """ConfigEntryAuthFailed mock."""


class _MockClientError(Exception):
    """aiohttp.ClientError mock — 실제 Exception 서브클래스여야 except 절이 정상 동작한다."""


def _identity_decorator(func):
    """homeassistant.core.callback mock — 데코레이터가 함수를 MagicMock으로 바꿔치기하지 않게 한다."""
    return func


# homeassistant.config_entries — ConfigEntry[T] 서브스크립트 지원 필요.
_mock_config_entries = MagicMock()
_mock_config_entries.ConfigEntry = _MockBase
sys.modules["homeassistant.config_entries"] = _mock_config_entries

# homeassistant.exceptions
_mock_exceptions = MagicMock()
_mock_exceptions.ConfigEntryAuthFailed = _MockConfigEntryAuthFailed
sys.modules["homeassistant.exceptions"] = _mock_exceptions

# homeassistant.helpers.update_coordinator — DataUpdateCoordinator/CoordinatorEntity는
# 실제로 서브클래싱되므로 _MockBase 사용.
_mock_ha_coordinator = MagicMock()
_mock_ha_coordinator.DataUpdateCoordinator = _MockBase
_mock_ha_coordinator.CoordinatorEntity = _MockBase
_mock_ha_coordinator.UpdateFailed = _MockUpdateFailed
sys.modules["homeassistant.helpers.update_coordinator"] = _mock_ha_coordinator

# homeassistant.core — callback은 데코레이터이므로 항등함수로 둔다.
_mock_core = MagicMock()
_mock_core.callback = _identity_decorator
sys.modules["homeassistant.core"] = _mock_core

# aiohttp — ClientError는 실제 Exception 서브클래스로 둬야 except 절이 통과한다.
_mock_aiohttp = MagicMock()
_mock_aiohttp.ClientError = _MockClientError
sys.modules["aiohttp"] = _mock_aiohttp

# 나머지 homeassistant 모듈 — 값을 직접 사용하지 않고 타입 힌트나 단순 참조로만
# 쓰이므로 MagicMock으로 충분하다.
for _mod in [
    "homeassistant",
    "homeassistant.const",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.event",
    "homeassistant.helpers.selector",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.components",
    "homeassistant.components.device_tracker",
    "homeassistant.components.sensor",
    "homeassistant.util",
    "homeassistant.util.dt",
]:
    sys.modules[_mod] = MagicMock()
