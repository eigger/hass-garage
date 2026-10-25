"""Garage config entries and external HTTP boundary fixtures."""

# <!-- hass-standards:domain-fixtures:start -->
# Use pytest_homeassistant_custom_component.common.MockConfigEntry for
# mock_config_entry when the integration uses config entries.
# Define mock_client only when an external communication client is present.
# Mock external communication boundaries, never Home Assistant core modules.
# Keep integration-specific fixtures below this managed block.
# <!-- hass-standards:domain-fixtures:end -->

import json
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.garage.const import (
    CONF_API_TOKEN,
    CONF_ENTITY_FUEL_LEVEL,
    CONF_ENTITY_LOCATION,
    CONF_ENTITY_ODOMETER,
    CONF_ENTITY_RPM,
    CONF_ENTITY_SPEED,
    CONF_HOST,
    CONF_PUSH_INTERVAL_SECONDS,
    DOMAIN,
)


@pytest.fixture
def status_payload():
    """Return a parsed status response fixture."""
    return json.loads((Path(__file__).parent / "fixtures/status.json").read_text())


@pytest.fixture
def reminders_payload():
    """Return a parsed reminders response fixture."""
    return json.loads((Path(__file__).parent / "fixtures/reminders.json").read_text())


@pytest.fixture
def entry(hass):
    """Create a Garage config entry without forwarded entities."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="My Car",
        unique_id="veh-1",
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
        options={},
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def entry_with_options(hass):
    """Create a Garage config entry with forwarded telemetry entities configured."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="My Car",
        unique_id="veh-1",
        data={CONF_HOST: "http://garage.test", CONF_API_TOKEN: "test-token"},
        options={
            CONF_ENTITY_LOCATION: "device_tracker.phone",
            CONF_ENTITY_RPM: "sensor.car_rpm",
            CONF_ENTITY_SPEED: "sensor.car_speed",
            CONF_ENTITY_FUEL_LEVEL: "sensor.car_fuel",
            CONF_ENTITY_ODOMETER: "sensor.car_odometer",
            CONF_PUSH_INTERVAL_SECONDS: 10,
        },
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def api_response(aioclient_mock, status_payload, reminders_payload):
    """Mock the Garage server HTTP endpoints."""
    aioclient_mock.get("http://garage.test/api/ingest/status", json=status_payload)
    aioclient_mock.get(
        "http://garage.test/api/ingest/reminders", json=reminders_payload
    )
    aioclient_mock.post("http://garage.test/api/ingest/telemetry", json={"ok": True})
    return aioclient_mock


@pytest.fixture
def entity_id(hass):
    """Look up an entity_id registered by the Garage integration."""
    from homeassistant.helpers import entity_registry as er

    def lookup(unique_id: str, domain: str = "sensor") -> str:
        result = er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique_id)
        assert result is not None
        return result

    return lookup


@pytest.fixture
def mock_config_entry(entry):
    """Expose the existing real HA entry through the shared fixture role."""
    return entry
