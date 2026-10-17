"""Exercise actual config entry setup, reload, cleanup, and error handling."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState

from custom_components.garage.const import CONF_ENTITY_RPM


async def test_setup_reload_and_unload(
    hass, entry_with_options, api_response, entity_id
):
    """Test full lifecycle: setup, state tracking, timer cleanup on reload and unload."""
    hass.states.async_set("sensor.car_rpm", "800")
    assert await hass.config_entries.async_setup(entry_with_options.entry_id)
    await hass.async_block_till_done()
    assert entry_with_options.state is ConfigEntryState.LOADED

    runtime = entry_with_options.runtime_data
    assert (
        hass.states.get(entity_id(f"{entry_with_options.entry_id}_due_reminders")).state
        == "2"
    )
    assert runtime.forwarder._unsub_state_change is not None

    # Trigger two rapid state changes so a delayed push timer (_unsub_call_later) is scheduled
    hass.states.async_set("sensor.car_rpm", "1500")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.car_rpm", "1800")
    await hass.async_block_till_done()
    assert runtime.forwarder._unsub_call_later is not None

    # Reload should cancel the pending timer and state listener on the old forwarder
    assert await hass.config_entries.async_reload(entry_with_options.entry_id)
    await hass.async_block_till_done()
    assert runtime.forwarder._unsub_call_later is None
    assert runtime.forwarder._unsub_state_change is None

    new_runtime = entry_with_options.runtime_data
    assert new_runtime is not runtime

    # Unload should cleanly stop the new forwarder and unload all platforms
    assert await hass.config_entries.async_unload(entry_with_options.entry_id)
    await hass.async_block_till_done()
    assert entry_with_options.state is ConfigEntryState.NOT_LOADED
    assert new_runtime.forwarder._unsub_call_later is None
    assert new_runtime.forwarder._unsub_state_change is None
    assert (
        hass.states.get(entity_id(f"{entry_with_options.entry_id}_due_reminders")).state
        == "unavailable"
    )


async def test_options_update_reloads_entry(hass, entry, api_response):
    """Updating options triggers _async_update_listener and reloads the config entry."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    initial_runtime = entry.runtime_data
    assert initial_runtime.forwarder.entity_ids == []

    hass.config_entries.async_update_entry(
        entry, options={CONF_ENTITY_RPM: "sensor.car_rpm"}
    )
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not initial_runtime
    assert entry.runtime_data.forwarder.entity_ids == ["sensor.car_rpm"]


async def test_status_connection_failure_sets_setup_retry(
    hass, entry, aioclient_mock, status_payload, reminders_payload
):
    """A 500 error during status first refresh puts the entry into SETUP_RETRY."""
    aioclient_mock.get("http://garage.test/api/ingest/status", status=500)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY

    aioclient_mock.clear_requests()
    aioclient_mock.get("http://garage.test/api/ingest/status", json=status_payload)
    aioclient_mock.get(
        "http://garage.test/api/ingest/reminders", json=reminders_payload
    )
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_reminders_connection_failure_sets_setup_retry(
    hass, entry, aioclient_mock, status_payload
):
    """A 500 error during reminders first refresh puts the entry into SETUP_RETRY."""
    aioclient_mock.get("http://garage.test/api/ingest/status", json=status_payload)
    aioclient_mock.get("http://garage.test/api/ingest/reminders", status=500)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_initial_auth_failure_starts_reauth(hass, entry, aioclient_mock):
    """A 401 error during initial setup sets SETUP_ERROR and triggers a reauth flow."""
    aioclient_mock.get("http://garage.test/api/ingest/status", status=401)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(
        flow["context"].get("source") == "reauth"
        for flow in hass.config_entries.flow.async_progress()
    )


async def test_partial_setup_failure_during_platform_forwarding_leaves_no_listeners(
    hass, entry_with_options, api_response
):
    """If async_forward_entry_setups fails, forwarder does not leak state listeners or timers."""
    hass.states.async_set("sensor.car_rpm", "800")
    with patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        side_effect=RuntimeError("platform setup failed"),
    ):
        assert not await hass.config_entries.async_setup(entry_with_options.entry_id)
        await hass.async_block_till_done()

    assert entry_with_options.state is ConfigEntryState.SETUP_ERROR
    forwarder = entry_with_options.runtime_data.forwarder
    assert forwarder._unsub_state_change is None
    assert forwarder._unsub_call_later is None

    before_calls = api_response.call_count
    hass.states.async_set("sensor.car_rpm", "2000")
    await hass.async_block_till_done()
    assert api_response.call_count == before_calls
