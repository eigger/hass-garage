"""Sensor platform for Garage."""

from __future__ import annotations

from typing import Any, ClassVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GarageRuntimeData, GarageTelemetryForwarder
from .const import DOMAIN
from .coordinator import GarageRemindersCoordinator, GarageStatusCoordinator


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Garage (self-hosted)",
        model="Vehicle",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Garage sensors for the entry."""
    data: GarageRuntimeData = entry.runtime_data

    async_add_entities(
        [
            GarageOdometerSensor(data.status_coordinator, entry),
            GarageFuelLevelSensor(data.status_coordinator, entry),
            GarageSpeedSensor(data.status_coordinator, entry),
            GarageDueRemindersSensor(data.reminders_coordinator, entry),
            GarageLastPushAtSensor(data.forwarder, entry),
            GarageLastPushOkSensor(data.forwarder, entry),
        ]
    )


class GarageStatusSensor(CoordinatorEntity[GarageStatusCoordinator], SensorEntity):
    """Base class for sensors backed by GET /api/ingest/status."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: GarageStatusCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = _device_info(entry)


class GarageOdometerSensor(GarageStatusSensor):
    """Vehicle odometer, as last known by Garage."""

    _attr_native_unit_of_measurement = "km"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: GarageStatusCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "odometer")

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("odometer")


class GarageFuelLevelSensor(GarageStatusSensor):
    """Fuel/battery level, as last known by Garage."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gas-station"

    def __init__(self, coordinator: GarageStatusCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "fuel_level")

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("fuelLevel")


class GarageSpeedSensor(GarageStatusSensor):
    """Last known speed reported to Garage."""

    _attr_native_unit_of_measurement = "km/h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: GarageStatusCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "speed")

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("speed")


class GarageDueRemindersSensor(
    CoordinatorEntity[GarageRemindersCoordinator], SensorEntity
):
    """Count of maintenance/admin reminders that are due or upcoming.

    Garage 대시보드의 "지난 N건 임박 N건" 배지와 같은 기준(``isDue`` 또는
    ``isUpcoming``)으로 집계해야 웹 화면에 보이는 건수와 이 센서 값이 일치한다.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "due_reminders"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-alert"

    def __init__(
        self, coordinator: GarageRemindersCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_due_reminders"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> int:
        return len(self._needs_attention)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        reminders = self.coordinator.data or []
        return {
            "due_count": sum(1 for r in reminders if r.get("isDue")),
            "upcoming_count": sum(1 for r in reminders if r.get("isUpcoming")),
            "due_types": [r.get("type") for r in reminders if r.get("isDue")],
            "upcoming_types": [r.get("type") for r in reminders if r.get("isUpcoming")],
        }

    @property
    def _needs_attention(self) -> list[dict[str, Any]]:
        reminders = self.coordinator.data or []
        return [r for r in reminders if r.get("isDue") or r.get("isUpcoming")]


class GarageLastPushAtSensor(SensorEntity):
    """Timestamp of the last telemetry push to Garage (diagnostic)."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_push_at"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:upload"
    _attr_should_poll = False

    def __init__(self, forwarder: GarageTelemetryForwarder, entry: ConfigEntry) -> None:
        self._forwarder = forwarder
        self._attr_unique_id = f"{entry.entry_id}_last_push_at"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Register listener for forwarder updates."""
        self.async_on_remove(
            self._forwarder.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> str | None:
        return self._forwarder.last_push_at

    @property
    def available(self) -> bool:
        return bool(self._forwarder.entity_ids)


class GarageLastPushOkSensor(SensorEntity):
    """Whether the last telemetry push succeeded (diagnostic)."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_push_ok"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options: ClassVar[list[str]] = ["ok", "error"]
    _attr_should_poll = False

    def __init__(self, forwarder: GarageTelemetryForwarder, entry: ConfigEntry) -> None:
        self._forwarder = forwarder
        self._attr_unique_id = f"{entry.entry_id}_last_push_ok"
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Register listener for forwarder updates."""
        self.async_on_remove(
            self._forwarder.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> str | None:
        if self._forwarder.last_push_ok is None:
            return None
        return "ok" if self._forwarder.last_push_ok else "error"

    @property
    def icon(self) -> str:
        return "mdi:check-circle" if self._forwarder.last_push_ok else "mdi:alert-circle"

    @property
    def available(self) -> bool:
        return bool(self._forwarder.entity_ids)
