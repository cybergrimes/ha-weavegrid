"""Support for WeaveGrid binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeaveGridConfigEntry, WeaveGridDataUpdateCoordinator
from .entity import WeaveGridEntity
from .models import WeaveGridData

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class WeaveGridBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a WeaveGrid binary sensor."""

    is_on_fn: Callable[[WeaveGridData], bool | None]


DESCRIPTIONS: tuple[WeaveGridBinarySensorDescription, ...] = (
    WeaveGridBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=lambda data: data.vehicle.connectivity.is_charging,
    ),
    WeaveGridBinarySensorDescription(
        key="plugged_in",
        translation_key="plugged_in",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=lambda data: data.vehicle.connectivity.is_plugged_in,
    ),
    WeaveGridBinarySensorDescription(
        key="home",
        translation_key="home",
        device_class=BinarySensorDeviceClass.PRESENCE,
        is_on_fn=lambda data: data.vehicle.connectivity.is_home,
    ),
    WeaveGridBinarySensorDescription(
        key="peak_avoidance",
        translation_key="peak_avoidance",
        is_on_fn=lambda data: (
            data.settings.peak_avoidance_enabled
            if data.settings
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeaveGridConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WeaveGrid binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        WeaveGridBinarySensorEntity(
            entry=entry,
            coordinator=coordinator,
            description=description,
            vehicle_id=vehicle_id,
        )
        for vehicle_id in coordinator.data
        for description in DESCRIPTIONS
    )


class WeaveGridBinarySensorEntity(
    WeaveGridEntity, BinarySensorEntity
):
    """Defines a WeaveGrid binary sensor entity."""

    entity_description: WeaveGridBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """Return state of the binary sensor."""
        return self.entity_description.is_on_fn(
            self.coordinator.data[self._vehicle_id]
        )
