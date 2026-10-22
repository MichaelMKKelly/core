"""The London Air integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .data import LondonAirConfigEntry, LondonAirDataUpdater

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: LondonAirConfigEntry) -> bool:
    """Set up London Air from a config entry."""
    data_updater = LondonAirDataUpdater(hass, entry)
    await data_updater.async_update()
    entry.runtime_data = data_updater

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LondonAirConfigEntry) -> bool:
    """Unload a London Air config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
