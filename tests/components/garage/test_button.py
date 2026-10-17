"""Invoke Garage button actions using the actual HA service registry."""


async def test_push_now_unavailable_when_no_entities_configured(
    hass, entry, api_response, entity_id
):
    """Push now button is unavailable when no forwarded entities are configured."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    push_button_id = entity_id(f"{entry.entry_id}_push_now", "button")
    assert hass.states.get(push_button_id).state == "unavailable"


async def test_push_now_and_refresh_now_buttons(
    hass, entry_with_options, api_response, entity_id
):
    """Pressing push_now sends telemetry immediately; refresh_now refreshes both coordinators."""
    hass.states.async_set(
        "device_tracker.phone",
        "home",
        {"latitude": 37.5665, "longitude": 126.978},
    )
    hass.states.async_set("sensor.car_rpm", "1200")

    assert await hass.config_entries.async_setup(entry_with_options.entry_id)
    await hass.async_block_till_done()

    push_button_id = entity_id(f"{entry_with_options.entry_id}_push_now", "button")
    refresh_button_id = entity_id(
        f"{entry_with_options.entry_id}_refresh_now", "button"
    )
    assert hass.states.get(push_button_id).state == "unknown"
    assert hass.states.get(refresh_button_id).state == "unknown"

    before_calls = api_response.call_count
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": push_button_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert api_response.call_count == before_calls + 1
    assert entry_with_options.runtime_data.forwarder.last_push_ok is True

    before_refresh_calls = api_response.call_count
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": refresh_button_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    # Refresh now refreshes both status_coordinator and reminders_coordinator (2 GET calls)
    assert api_response.call_count == before_refresh_calls + 2
