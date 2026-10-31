"""WeaveGrid GraphQL API client."""

from __future__ import annotations

from time import perf_counter

import aiohttp

from .const import (
    API_URL,
    LOGGER,
    QUERY_LOGIN,
    QUERY_VEHICLE_DATA,
)
from .models import (
    ChargeAggregates,
    ChargeHistory,
    DeviceStatus,
    LoginResult,
    ManagedChargeSettings,
    Vehicle,
    WeaveGridData,
)


class WeaveGridAuthError(Exception):
    """Raised when authentication fails."""


class WeaveGridConnectionError(Exception):
    """Raised when a connection error occurs."""


class WeaveGridClient:
    """Client for the WeaveGrid GraphQL API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client."""
        self._session = session
        self._utility_acronym: str | None = None

    async def login(self, email: str, password: str) -> LoginResult:
        """Authenticate with the WeaveGrid API."""
        data = await self._execute(
            query=QUERY_LOGIN,
            variables={
                "email": email,
                "password": password,
                "useMagicLink": False,
            },
            operation_name="LoginDriver",
        )
        result = LoginResult.from_dict(data["data"])
        if not result.is_logged_in:
            raise WeaveGridAuthError(
                f"Login failed with status: {result.status}"
            )
        self._utility_acronym = result.utility_acronym
        return result

    async def get_vehicle_data(
        self, start_dttm: str, end_dttm: str
    ) -> list[WeaveGridData]:
        """Fetch dashboard and vehicle details in one GraphQL operation."""
        data = await self._execute(
            query=QUERY_VEHICLE_DATA,
            variables={
                "startDttm": start_dttm,
                "endDttm": end_dttm,
                "limit": 100,
                "chargeEventsLimit": 5,
                "locationRelationshipTypes": ["home_primary"],
            },
            operation_name="DashboardData",
        )
        vehicles = data["data"]["viewer"]["vehicles"]["data"]
        return [
            WeaveGridData(
                vehicle=Vehicle.from_dict(vehicle),
                device_status=DeviceStatus.from_dict(vehicle),
                aggregates=ChargeAggregates.from_dict(
                    vehicle["chargeEvents"]
                ),
                settings=(
                    ManagedChargeSettings.from_dict(vehicle)
                    if vehicle.get("mcSettings")
                    else None
                ),
                charge_history=(
                    ChargeHistory.from_dict(vehicle["chargeHistory"])
                    if vehicle.get("chargeHistory")
                    else None
                ),
            )
            for vehicle in vehicles
        ]

    async def _execute(
        self,
        query: str,
        variables: dict,
        operation_name: str | None = None,
    ) -> dict:
        """Execute a GraphQL operation."""
        payload: dict = {
            "query": query,
            "variables": variables,
        }
        if operation_name:
            payload["operationName"] = operation_name

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._utility_acronym:
            headers["x-wg-utility-acronym"] = self._utility_acronym

        operation = operation_name or "unknown"
        request_started = perf_counter()
        try:
            async with self._session.post(
                API_URL, json=[payload], headers=headers
            ) as resp:
                LOGGER.debug(
                    "WeaveGrid API request completed "
                    "(operation=%s, status=%s, duration_ms=%.0f)",
                    operation,
                    resp.status,
                    (perf_counter() - request_started) * 1000,
                )
                if resp.status == 401:
                    raise WeaveGridAuthError("Authentication failed (HTTP 401)")
                if resp.status != 200:
                    raise WeaveGridConnectionError(
                        f"Unexpected status code: {resp.status}"
                    )
                result = await resp.json(content_type=None)
        except WeaveGridAuthError:
            raise
        except WeaveGridConnectionError:
            raise
        except aiohttp.ClientError as err:
            LOGGER.debug(
                "WeaveGrid API request failed "
                "(operation=%s, error_type=%s, duration_ms=%.0f)",
                operation,
                type(err).__name__,
                (perf_counter() - request_started) * 1000,
            )
            raise WeaveGridConnectionError(
                "Error communicating with WeaveGrid"
            ) from err
        except Exception as err:
            LOGGER.debug(
                "WeaveGrid API request failed "
                "(operation=%s, error_type=%s, duration_ms=%.0f)",
                operation,
                type(err).__name__,
                (perf_counter() - request_started) * 1000,
            )
            raise WeaveGridConnectionError(
                "Unexpected error communicating with WeaveGrid"
            ) from err

        # API returns arrays - unwrap first element
        if isinstance(result, list):
            result = result[0]

        if errors := result.get("errors"):
            first_error = errors[0].get("message", "Unknown error")
            LOGGER.debug(
                "WeaveGrid GraphQL operation failed "
                "(operation=%s, error_count=%s)",
                operation,
                len(errors),
            )
            if "auth" in first_error.lower() or "credentials" in first_error.lower():
                raise WeaveGridAuthError("Authentication failed")
            raise WeaveGridConnectionError("GraphQL operation failed")

        return result
