"""Verify Garage vehicle location device_tracker entity through HA states and registries."""

from homeassistant.components.device_tracker import SourceType
from homeassistant.helpers import device_registry as dr

from custom_components.garage.const import DOMAIN


async def test_vehicle_location_tracker(hass, entry, api_response, entity_id):
    """Verify GPS coordinates, source_type, attributes, and device registry entry."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    tracker_id = entity_id(f"{entry.entry_id}_location", "device_tracker")
    state = hass.states.get(tracker_id)
    assert state is not None
    assert state.attributes["source_type"] == SourceType.GPS
    assert state.attributes["latitude"] == 37.5665
    assert state.attributes["longitude"] == 126.978
    assert state.attributes["location_updated_at"] == "2026-10-17T12:00:00Z"

    device_reg = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_reg, entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, entry.entry_id)}
    assert device.name == "My Car"
    assert device.manufacturer == "Garage (self-hosted)"
    assert device.model == "Vehicle"
