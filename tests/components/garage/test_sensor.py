"""Read Garage sensors through actual HA states and entity registry."""


async def test_due_reminders_and_last_push_unavailable_when_unconfigured(
    hass, entry, api_response, entity_id
):
    """Verify due_reminders state/attributes and last_push_at unavailability without options."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    due_sensor = hass.states.get(entity_id(f"{entry.entry_id}_due_reminders"))
    assert due_sensor.state == "2"
    assert due_sensor.attributes["state_class"] == "measurement"
    assert due_sensor.attributes["due_count"] == 1
    assert due_sensor.attributes["upcoming_count"] == 1
    assert due_sensor.attributes["due_types"] == ["engineOilFilter"]
    assert due_sensor.attributes["upcoming_types"] == ["tireRotation"]

    last_push = hass.states.get(entity_id(f"{entry.entry_id}_last_push_at"))
    assert last_push.state == "unavailable"


async def test_last_push_at_sensor_updates_on_push_success_and_failure(
    hass, entry_with_options, api_response, entity_id
):
    """Verify last_push_at state, attributes, and icon across push success and failure."""
    hass.states.async_set(
        "device_tracker.phone",
        "home",
        {"latitude": 37.5665, "longitude": 126.978},
    )
    hass.states.async_set("sensor.car_rpm", "800")
    hass.states.async_set("sensor.car_speed", "30")
    hass.states.async_set("sensor.car_fuel", "60")
    hass.states.async_set("sensor.car_odometer", "12350")

    assert await hass.config_entries.async_setup(entry_with_options.entry_id)
    await hass.async_block_till_done()

    last_push_entity_id = entity_id(f"{entry_with_options.entry_id}_last_push_at")
    last_push = hass.states.get(last_push_entity_id)
    assert last_push.state == "unknown"
    assert last_push.attributes["success"] is None
    assert last_push.attributes["icon"] == "mdi:upload"
    assert last_push.attributes["forwarded_entities"] == [
        "device_tracker.phone",
        "sensor.car_rpm",
        "sensor.car_speed",
        "sensor.car_fuel",
        "sensor.car_odometer",
    ]

    # Trigger a real state change on a non-location entity -> pushes telemetry
    hass.states.async_set("sensor.car_rpm", "2100")
    await hass.async_block_till_done()

    last_push = hass.states.get(last_push_entity_id)
    assert last_push.state not in ("unknown", "unavailable")
    assert last_push.attributes["success"] is True
    assert last_push.attributes["icon"] == "mdi:upload"

    # Now make the telemetry endpoint fail and push via the forwarder
    api_response.clear_requests()
    api_response.post("http://garage.test/api/ingest/telemetry", status=500)
    await entry_with_options.runtime_data.forwarder.async_push_now()
    await hass.async_block_till_done()

    last_push = hass.states.get(last_push_entity_id)
    assert last_push.attributes["success"] is False
    assert last_push.attributes["icon"] == "mdi:alert-circle"
