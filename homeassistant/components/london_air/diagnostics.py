"""Diagnostics support for the London Air integration."""

from typing import Any

from homeassistant.core import HomeAssistant

from .const import CONF_LOCATIONS
from .coordinator import LondonAirConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LondonAirConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry": entry.as_dict(),
        "data": {
            authority: coordinator.data[authority]
            for authority in entry.data[CONF_LOCATIONS]
        },
    }
