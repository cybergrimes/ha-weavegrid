"""Tests for the WeaveGrid API client."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from custom_components.weavegrid.api import WeaveGridClient


class WeaveGridClientTests(unittest.IsolatedAsyncioTestCase):
    """Test parsing of combined dashboard and vehicle data."""

    async def test_get_vehicle_data_parses_combined_query_response(self) -> None:
        """Parse vehicle, charging, settings, and history from one response."""
        client = WeaveGridClient(session=None)
        client._execute = AsyncMock(
            return_value={
                "data": {
                    "viewer": {
                        "vehicles": {
                            "data": [
                                {
                                    "vehicleId": "vehicle-1",
                                    "displayName": "My EV",
                                    "isActive": True,
                                    "isEvse": False,
                                    "oem": {"name": "Example Motors"},
                                    "connectivityDetail": {
                                        "isActive": True,
                                        "isCharging": False,
                                        "isPluggedIn": True,
                                        "isHome": True,
                                    },
                                    "mcPlanStatus": {
                                        "mcStatus": "active",
                                        "planIsActive": True,
                                        "optimization": "optimized",
                                        "readyByDttm": "2026-10-30T23:00:00Z",
                                    },
                                    "mcSettings": {
                                        "chargeByTimes": {
                                            "Mon": "07:00",
                                            "__typename": "ChargeByTimes",
                                        },
                                        "enablePeakAvoidance": True,
                                    },
                                    "chargeEvents": {
                                        "totalAggregates": {
                                            "data": [
                                                {
                                                    "chargeCost": 12.5,
                                                    "energyDeliveredKwh": 40.0,
                                                    "smartScore": 90.0,
                                                    "offPeakChargingCost": 4.0,
                                                    "offPeakEnergyDeliveredKwh": 20.0,
                                                    "totalSmartChargingCost": 3.0,
                                                }
                                            ]
                                        },
                                        "dailyAggregates": {
                                            "data": [
                                                {
                                                    "usageDate": "2026-10-29",
                                                    "energyDeliveredKwh": 10.0,
                                                    "chargeCost": 2.5,
                                                }
                                            ]
                                        },
                                    },
                                    "chargeHistory": {
                                        "aggregates": {
                                            "data": [
                                                {
                                                    "startDttm": "2026-10-29T20:00:00Z",
                                                    "endDttm": "2026-10-29T22:00:00Z",
                                                    "chargeHours": 2.0,
                                                    "energyDeliveredKwh": 10.0,
                                                    "chargeCost": 2.5,
                                                }
                                            ]
                                        },
                                        "chargeSpans": {
                                            "data": [{"electricityRate": 0.25}]
                                        },
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        )

        vehicles = await client.get_vehicle_data("start", "end")

        client._execute.assert_awaited_once()
        self.assertEqual(len(vehicles), 1)
        vehicle_data = vehicles[0]
        self.assertEqual(vehicle_data.vehicle.vehicle_id, "vehicle-1")
        self.assertEqual(vehicle_data.vehicle.display_name, "My EV")
        self.assertTrue(vehicle_data.device_status.mc_plan_status.plan_is_active)
        self.assertEqual(vehicle_data.aggregates.total_energy_kwh, 40.0)
        self.assertEqual(vehicle_data.aggregates.daily[0].usage_date, "2026-10-29")
        self.assertEqual(
            vehicle_data.settings.charge_by_times, {"Mon": "07:00"}
        )
        self.assertEqual(
            vehicle_data.charge_history.latest_electricity_rate, 0.25
        )


if __name__ == "__main__":
    unittest.main()
