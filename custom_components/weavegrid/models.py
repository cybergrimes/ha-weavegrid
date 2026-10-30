"""Data models for the WeaveGrid integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectivityDetail:
    """Connectivity status for a vehicle or EVSE."""

    is_active: bool
    is_charging: bool
    is_plugged_in: bool
    is_home: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectivityDetail:
        """Create from API response dict."""
        return cls(
            is_active=data["isActive"],
            is_charging=data["isCharging"],
            is_plugged_in=data["isPluggedIn"],
            is_home=data["isHome"],
        )


@dataclass
class Vehicle:
    """A vehicle or EVSE from the dashboard."""

    vehicle_id: str
    display_name: str
    is_active: bool
    is_evse: bool
    oem_name: str
    connectivity: ConnectivityDetail

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vehicle:
        """Create from API response dict."""
        return cls(
            vehicle_id=data["vehicleId"],
            display_name=data["displayName"],
            is_active=data["isActive"],
            is_evse=data["isEvse"],
            oem_name=data["oem"]["name"],
            connectivity=ConnectivityDetail.from_dict(data["connectivityDetail"]),
        )


@dataclass
class McPlanStatus:
    """Managed charge plan status."""

    mc_status: str
    plan_is_active: bool
    optimization: str
    ready_by_dttm: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> McPlanStatus:
        """Create from API response dict."""
        return cls(
            mc_status=data["mcStatus"],
            plan_is_active=data["planIsActive"],
            optimization=data["optimization"],
            ready_by_dttm=data.get("readyByDttm"),
        )


@dataclass
class DeviceStatus:
    """Device status from vehicle data."""

    mc_plan_status: McPlanStatus | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceStatus:
        """Create from API vehicle data dict."""
        return cls(
            mc_plan_status=(
                McPlanStatus.from_dict(data["mcPlanStatus"])
                if data.get("mcPlanStatus")
                else None
            ),
        )


@dataclass
class DailyAggregate:
    """Daily charge aggregate."""

    usage_date: str
    energy_kwh: float
    charge_cost: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DailyAggregate:
        """Create from API response dict."""
        return cls(
            usage_date=data["usageDate"],
            energy_kwh=data["energyDeliveredKwh"],
            charge_cost=data["chargeCost"],
        )


@dataclass
class ChargeAggregates:
    """Charge event aggregates."""

    total_charge_cost: float
    total_energy_kwh: float
    smart_score: float
    off_peak_charge_cost: float
    off_peak_energy_kwh: float
    smart_charging_cost: float
    daily: list[DailyAggregate] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChargeAggregates:
        """Create from API response dict."""
        totals = data["totalAggregates"]["data"][0]
        return cls(
            total_charge_cost=totals["chargeCost"],
            total_energy_kwh=totals["energyDeliveredKwh"],
            smart_score=totals["smartScore"],
            off_peak_charge_cost=totals.get("offPeakChargingCost", 0.0),
            off_peak_energy_kwh=totals.get("offPeakEnergyDeliveredKwh", 0.0),
            smart_charging_cost=totals.get("totalSmartChargingCost", 0.0),
            daily=[
                DailyAggregate.from_dict(d)
                for d in data.get("dailyAggregates", {}).get("data", [])
            ],
        )


@dataclass
class ManagedChargeSettings:
    """Managed charge settings for a vehicle."""

    charge_by_times: dict[str, str]
    peak_avoidance_enabled: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManagedChargeSettings:
        """Create from API response dict."""
        settings = data["mcSettings"]
        charge_by_times = settings["chargeByTimes"]
        return cls(
            charge_by_times={
                k: v
                for k, v in charge_by_times.items()
                if k != "__typename"
            },
            peak_avoidance_enabled=settings["enablePeakAvoidance"],
        )


@dataclass
class ChargeSession:
    """A daily charge session aggregate."""

    start_dttm: str
    end_dttm: str
    charge_hours: float
    energy_kwh: float
    charge_cost: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChargeSession:
        """Create from API response dict."""
        return cls(
            start_dttm=data["startDttm"],
            end_dttm=data["endDttm"],
            charge_hours=data["chargeHours"],
            energy_kwh=data["energyDeliveredKwh"],
            charge_cost=data["chargeCost"],
        )


@dataclass
class ChargeHistory:
    """Charge history with sessions and rate info."""

    sessions: list[ChargeSession]
    latest_electricity_rate: float | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChargeHistory:
        """Create from API charge events dict."""
        sessions = [
            ChargeSession.from_dict(d)
            for d in data.get("aggregates", {}).get("data", [])
        ]
        spans = data.get("chargeSpans", {}).get("data", [])
        latest_rate = spans[0]["electricityRate"] if spans else None
        return cls(
            sessions=sessions,
            latest_electricity_rate=latest_rate,
        )


@dataclass
class LoginResult:
    """Login response data."""

    user_id: str
    utility_acronym: str
    is_logged_in: bool
    status: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoginResult:
        """Create from API response dict."""
        login = data["login"]
        user = login["user"]
        return cls(
            user_id=user["userId"],
            utility_acronym=user["utility"]["acronym"],
            is_logged_in=login["isLoggedIn"],
            status=login["status"],
        )


@dataclass
class WeaveGridData:
    """Combined data from all API calls for one vehicle."""

    vehicle: Vehicle
    device_status: DeviceStatus
    aggregates: ChargeAggregates
    settings: ManagedChargeSettings | None
    charge_history: ChargeHistory | None
