"""Exercise config, options, and reauth flows through the actual HA flow manager."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.garage.api import GarageError
from custom_components.garage.const import (
    CONF_API_TOKEN,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_RPM,
    CONF_HOST,
    CONF_PUSH_INTERVAL_SECONDS,
    DOMAIN,
)


async def test_user_and_sensors_flow_creates_entry_and_aborts_duplicate(
    hass, api_response
):
    """Test two-step user -> sensors config flow and duplicate vehicle abort."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: " http://garage.test/ ", CONF_API_TOKEN: " test-token "},
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "sensors"

    hass.states.async_set(
        "device_tracker.phone",
        "home",
        {"latitude": 37.5, "longitude": 127.0},
    )
    hass.states.async_set("sensor.car_rpm", "900")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_LOCATION: "device_tracker.phone",
            CONF_ENTITY_RPM: "sensor.car_rpm",
            CONF_PUSH_INTERVAL_SECONDS: 15,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Car"
    assert result["data"] == {
        CONF_HOST: "http://garage.test",
        CONF_API_TOKEN: "test-token",
    }
    assert result["options"] == {
        CONF_ENTITY_LOCATION: "device_tracker.phone",
        CONF_ENTITY_RPM: "sensor.car_rpm",
        CONF_PUSH_INTERVAL_SECONDS: 15.0,
    }
    assert result["result"].unique_id == "veh-1"

    duplicate = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
    )
    assert duplicate["type"] is data_entry_flow.FlowResultType.ABORT
    assert duplicate["reason"] == "already_configured"


async def test_default_title_when_vehicle_name_missing(
    hass, aioclient_mock, reminders_payload
):
    """Fallback title 'Garage' is used when status response has no name."""
    aioclient_mock.get("http://garage.test/api/ingest/status", json={"id": "veh-2"})
    aioclient_mock.get(
        "http://garage.test/api/ingest/reminders", json=reminders_payload
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
    )
    assert result["step_id"] == "sensors"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Garage"
    assert result["options"] == {CONF_PUSH_INTERVAL_SECONDS: 10.0}


@pytest.mark.parametrize(
    ("status", "expected"),
    [(401, "invalid_auth"), (500, "cannot_connect")],
)
async def test_user_step_http_errors(hass, aioclient_mock, status, expected):
    """Verify HTTP 401 and 500 map to invalid_auth and cannot_connect."""
    aioclient_mock.get("http://garage.test/api/ingest/status", status=status)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": expected}


async def test_user_step_missing_id_and_generic_garage_error(hass, aioclient_mock):
    """Missing vehicle id or base GarageError sets unknown error."""
    aioclient_mock.get("http://garage.test/api/ingest/status", json={"name": "No ID"})
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}

    with patch(
        "custom_components.garage.config_flow.GarageApi.async_get_status",
        side_effect=GarageError("unexpected"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
        )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_reauth_flow_errors_and_success(
    hass, entry, aioclient_mock, status_payload, reminders_payload
):
    """Test reauth_confirm error handling and successful token update."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    for status, error in [(401, "invalid_auth"), (500, "cannot_connect")]:
        aioclient_mock.clear_requests()
        aioclient_mock.get("http://garage.test/api/ingest/status", status=status)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "bad-token"}
        )
        assert result["errors"] == {"base": error}

    with patch(
        "custom_components.garage.config_flow.GarageApi.async_get_status",
        side_effect=GarageError("unexpected"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_TOKEN: "bad-token"}
        )
    assert result["errors"] == {"base": "unknown"}

    aioclient_mock.clear_requests()
    aioclient_mock.get("http://garage.test/api/ingest/status", json=status_payload)
    aioclient_mock.get(
        "http://garage.test/api/ingest/reminders", json=reminders_payload
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: " new-token "}
    )
    await hass.async_block_till_done()
    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_API_TOKEN] == "new-token"


async def test_options_flow_updates_forwarded_entities(hass, entry, api_response):
    """Test configuring forwarded entities and push interval through OptionsFlow."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.car_rpm", "1000")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_RPM: "sensor.car_rpm",
            CONF_PUSH_INTERVAL_SECONDS: 20,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_ENTITY_RPM: "sensor.car_rpm",
        CONF_PUSH_INTERVAL_SECONDS: 20.0,
    }
