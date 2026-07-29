"""GarageApi 단위 테스트 — 실제 네트워크 호출 없이 aiohttp 세션을 흉내낸다."""

import asyncio

import pytest
from aiohttp import ClientError

from custom_components.garage.api import (
    GarageApi,
    GarageAuthError,
    GarageConnectionError,
)


class FakeResponse:
    """``async with session.get(...) as resp:`` 프로토콜을 흉내내는 더미 응답."""

    def __init__(self, status=200, json_data=None, text_data="", raise_error=None):
        self.status = status
        self._json = json_data
        self._text = text_data
        self._raise_error = raise_error

    async def __aenter__(self):
        if self._raise_error is not None:
            raise self._raise_error
        return self

    async def __aexit__(self, *exc_info):
        return False

    def raise_for_status(self):
        pass  # api.py는 401을 먼저 직접 체크하므로 여기선 아무것도 안 해도 된다.

    async def json(self):
        return self._json

    async def text(self):
        return self._text


class FakeSession:
    """호출된 URL/헤더/바디를 기록하고, 미리 정해둔 응답을 돌려주는 더미 세션."""

    def __init__(self, response: FakeResponse):
        self._response = response
        self.last_method = None
        self.last_url = None
        self.last_headers = None
        self.last_json = None

    def get(self, url, headers=None):
        self.last_method = "GET"
        self.last_url = url
        self.last_headers = headers
        return self._response

    def post(self, url, headers=None, json=None):
        self.last_method = "POST"
        self.last_url = url
        self.last_headers = headers
        self.last_json = json
        return self._response


def _run(coro):
    return asyncio.run(coro)


class TestAsyncGetStatus:
    def test_success_returns_json_body(self):
        session = FakeSession(FakeResponse(status=200, json_data={"id": "veh1", "odometer": 100}))
        api = GarageApi(session, "http://garage.local", "tok123")

        result = _run(api.async_get_status())

        assert result == {"id": "veh1", "odometer": 100}
        assert session.last_method == "GET"
        assert session.last_url == "http://garage.local/api/ingest/status"
        assert session.last_headers == {"Authorization": "Bearer tok123"}

    def test_strips_trailing_slash_from_host(self):
        session = FakeSession(FakeResponse(status=200, json_data={}))
        api = GarageApi(session, "http://garage.local/", "tok123")

        _run(api.async_get_status())

        assert session.last_url == "http://garage.local/api/ingest/status"

    def test_401_raises_auth_error(self):
        session = FakeSession(FakeResponse(status=401))
        api = GarageApi(session, "http://garage.local", "bad-token")

        with pytest.raises(GarageAuthError):
            _run(api.async_get_status())

    def test_connection_error_is_wrapped(self):
        session = FakeSession(FakeResponse(raise_error=ClientError("boom")))
        api = GarageApi(session, "http://garage.local", "tok123")

        with pytest.raises(GarageConnectionError):
            _run(api.async_get_status())


class TestAsyncGetReminders:
    def test_returns_list_as_is(self):
        session = FakeSession(FakeResponse(status=200, json_data=[{"type": "oil"}]))
        api = GarageApi(session, "http://garage.local", "tok123")

        result = _run(api.async_get_reminders())

        assert result == [{"type": "oil"}]

    def test_non_list_response_becomes_empty_list(self):
        session = FakeSession(FakeResponse(status=200, json_data={"unexpected": "shape"}))
        api = GarageApi(session, "http://garage.local", "tok123")

        result = _run(api.async_get_reminders())

        assert result == []


class TestAsyncSendTelemetry:
    def test_drops_none_fields_before_sending(self):
        session = FakeSession(FakeResponse(status=200))
        api = GarageApi(session, "http://garage.local", "tok123")

        _run(
            api.async_send_telemetry(
                {"lat": 37.5, "lon": None, "speed": 60, "rpm": None}
            )
        )

        assert session.last_method == "POST"
        assert session.last_url == "http://garage.local/api/ingest/telemetry"
        assert session.last_json == {"lat": 37.5, "speed": 60}

    def test_all_none_payload_skips_request_entirely(self):
        session = FakeSession(FakeResponse(status=200))
        api = GarageApi(session, "http://garage.local", "tok123")

        _run(api.async_send_telemetry({"lat": None, "lon": None}))

        assert session.last_method is None

    def test_401_raises_auth_error(self):
        session = FakeSession(FakeResponse(status=401))
        api = GarageApi(session, "http://garage.local", "tok123")

        with pytest.raises(GarageAuthError):
            _run(api.async_send_telemetry({"lat": 37.5}))
