"""The WeaveGrid integration."""

from __future__ import annotations

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import WeaveGridAuthError, WeaveGridClient, WeaveGridConnectionError
from .coordinator import WeaveGridConfigEntry, WeaveGridDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: WeaveGridConfigEntry
) -> bool:
    """Set up WeaveGrid from a config entry."""
    session = async_create_clientsession(hass)
    client = WeaveGridClient(session)

    try:
        await client.login(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    except WeaveGridAuthError as err:
        raise ConfigEntryAuthFailed from err
    except WeaveGridConnectionError as err:
        raise ConfigEntryNotReady(
            "Could not connect to WeaveGrid"
        ) from err

    coordinator = WeaveGridDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(
    hass: HomeAssistant, entry: WeaveGridConfigEntry
) -> None:
    """Reload the integration when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: WeaveGridConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
