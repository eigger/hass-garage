"""Device tracker platform for Garage — shows the vehicle's last known location."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GarageRuntimeData
from .const import DOMAIN
from .coordinator import GarageStatusCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the vehicle location tracker."""
    data: GarageRuntimeData = entry.runtime_data
    async_add_entities([GarageVehicleTracker(data.status_coordinator, entry)])


class GarageVehicleTracker(CoordinatorEntity[GarageStatusCoordinator], TrackerEntity):
    """차량 마지막 위치(GPS) — 지도에 표시된다."""

    _attr_has_entity_name = True
    _attr_translation_key = "vehicle_location"
    _attr_icon = "mdi:car"

    def __init__(self, coordinator: GarageStatusCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_location"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Garage (self-hosted)",
            model="Vehicle",
        )

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return (self.coordinator.data or {}).get("latitude")

    @property
    def longitude(self) -> float | None:
        return (self.coordinator.data or {}).get("longitude")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "location_updated_at": data.get("locationUpdatedAt"),
        }
