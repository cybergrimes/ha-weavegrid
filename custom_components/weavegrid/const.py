"""Constants for the WeaveGrid integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "weavegrid"
CONF_POLL_INTERVAL: Final = "poll_interval"
DEFAULT_POLL_INTERVAL: Final = 15
POLL_INTERVAL_OPTIONS: Final = (
    {"value": "5", "label": "5 minutes"},
    {"value": "15", "label": "15 minutes"},
    {"value": "30", "label": "30 minutes"},
)
LOGGER = logging.getLogger(__package__)

API_URL: Final = "https://charge.weavegrid.com/graphql"

QUERY_LOGIN: Final = """
mutation LoginDriver($email: String!, $password: String, $useMagicLink: Boolean) {
  login(emailAddress: $email, password: $password, useMagicLink: $useMagicLink) {
    isLoggedIn
    status
    user {
      userId
      utility {
        acronym
      }
    }
  }
}
"""

QUERY_VEHICLE_DATA: Final = """
query DashboardData(
  $startDttm: DateTime!,
  $endDttm: DateTime!,
  $limit: Int,
  $chargeEventsLimit: Int,
  $locationRelationshipTypes: [RelationshipTypeEnum]
) {
  viewer {
    id
    vehicles(includeArchivedRegistrations: true) {
      data {
        vehicleId
        displayName
        isActive
        isEvse
        oem {
          name
        }
        connectivityDetail {
          isActive
          isCharging
          isPluggedIn
          isHome
        }
        mcPlanStatus {
          mcStatus
          planIsActive
          optimization
          readyByDttm
        }
        mcSettings {
          chargeByTimes {
            Mon
            Tue
            Wed
            Thu
            Fri
            Sat
            Sun
          }
          enablePeakAvoidance
        }
        chargeEvents(
          inclusiveStartDttm: $startDttm
          inclusiveEndDttm: $endDttm
          locationRelationshipTypes: [home_primary]
          limit: $limit
        ) {
          totalAggregates: aggregates(
            aggregateUnit: total
            exclusiveStartDttm: $startDttm
            exclusiveEndDttm: $endDttm
          ) {
            data {
              chargeCost
              offPeakChargingCost
              offPeakEnergyDeliveredKwh
              totalSmartChargingCost
              energyDeliveredKwh
              smartScore
            }
          }
          dailyAggregates: aggregates(
            aggregateUnit: day
            exclusiveStartDttm: $startDttm
            exclusiveEndDttm: $endDttm
            limit: $limit
          ) {
            data {
              usageDate
              chargeCost
              energyDeliveredKwh
            }
          }
        }
        chargeHistory: chargeEvents(
          first: $chargeEventsLimit
          locationRelationshipTypes: $locationRelationshipTypes
        ) {
          aggregates(aggregateUnit: day) {
            data {
              startDttm
              endDttm
              chargeHours
              energyDeliveredKwh
              chargeCost
            }
          }
          chargeSpans {
            data {
              startDttm
              endDttm
              electricityRate
              electricityRateUnit
            }
          }
        }
      }
    }
  }
}
"""
