"""Support for WeaveGrid sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import WeaveGridConfigEntry, WeaveGridDataUpdateCoordinator
from .entity import WeaveGridEntity
from .models import WeaveGridData

PARALLEL_UPDATES = 0

MC_STATUS_OPTIONS = [
    "charging",
    "complete",
    "active",
    "inactive",
    "pending",
    "unknown",
]

DAY_ABBR_MAP = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp string to a datetime object."""
    if value is None:
        return None
    return dt_util.parse_datetime(value)


def _get_todays_charge_by_time(data: WeaveGridData) -> str | None:
    """Get today's scheduled charge-by time."""
    if data.settings is None:
        return None
    today_abbr = DAY_ABBR_MAP[dt_util.now().weekday()]
    return data.settings.charge_by_times.get(today_abbr)


@dataclass(frozen=True, kw_only=True)
class WeaveGridSensorDescription(SensorEntityDescription):
    """Describe a WeaveGrid sensor."""

    value_fn: Callable[[WeaveGridData], float | str | datetime | None]


DESCRIPTIONS: tuple[WeaveGridSensorDescription, ...] = (
    WeaveGridSensorDescription(
        key="weekly_energy",
        translation_key="weekly_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
        value_fn=lambda data: data.aggregates.total_energy_kwh,
    ),
    WeaveGridSensorDescription(
        key="weekly_cost",
        translation_key="weekly_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.aggregates.total_charge_cost,
    ),
    WeaveGridSensorDescription(
        key="smart_score",
        translation_key="smart_score",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.aggregates.smart_score * 100,
    ),
    WeaveGridSensorDescription(
        key="last_charge_energy",
        translation_key="last_charge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.aggregates.daily[0].energy_kwh
            if data.aggregates.daily
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="last_charge_cost",
        translation_key="last_charge_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        suggested_display_precision=2,
        value_fn=lambda data: (
            data.aggregates.daily[0].charge_cost
            if data.aggregates.daily
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="managed_charge_status",
        translation_key="managed_charge_status",
        device_class=SensorDeviceClass.ENUM,
        options=MC_STATUS_OPTIONS,
        value_fn=lambda data: (
            data.device_status.mc_plan_status.mc_status.lower()
            if data.device_status.mc_plan_status
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="ready_by_time",
        translation_key="ready_by_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            _parse_timestamp(data.device_status.mc_plan_status.ready_by_dttm)
            if data.device_status.mc_plan_status
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="off_peak_energy",
        translation_key="off_peak_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
        value_fn=lambda data: data.aggregates.off_peak_energy_kwh,
    ),
    WeaveGridSensorDescription(
        key="off_peak_cost",
        translation_key="off_peak_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.aggregates.off_peak_charge_cost,
    ),
    WeaveGridSensorDescription(
        key="smart_charging_cost",
        translation_key="smart_charging_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        value_fn=lambda data: data.aggregates.smart_charging_cost,
    ),
    WeaveGridSensorDescription(
        key="charge_by_time",
        translation_key="charge_by_time",
        value_fn=_get_todays_charge_by_time,
    ),
    WeaveGridSensorDescription(
        key="last_session_start",
        translation_key="last_session_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            _parse_timestamp(data.charge_history.sessions[0].start_dttm)
            if data.charge_history and data.charge_history.sessions
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="last_session_end",
        translation_key="last_session_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            _parse_timestamp(data.charge_history.sessions[0].end_dttm)
            if data.charge_history and data.charge_history.sessions
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="last_session_duration",
        translation_key="last_session_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement="h",
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.charge_history.sessions[0].charge_hours
            if data.charge_history and data.charge_history.sessions
            else None
        ),
    ),
    WeaveGridSensorDescription(
        key="electricity_rate",
        translation_key="electricity_rate",
        native_unit_of_measurement="USD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=lambda data: (
            data.charge_history.latest_electricity_rate
            if data.charge_history
            else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeaveGridConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WeaveGrid sensors based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        WeaveGridSensorEntity(
            entry=entry,
            coordinator=coordinator,
            description=description,
            vehicle_id=vehicle_id,
        )
        for vehicle_id in coordinator.data
        for description in DESCRIPTIONS
    )


class WeaveGridSensorEntity(
    WeaveGridEntity, SensorEntity
):
    """Defines a WeaveGrid sensor."""

    entity_description: WeaveGridSensorDescription

    @property
    def native_value(self) -> float | str | datetime | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(
            self.coordinator.data[self._vehicle_id]
        )
