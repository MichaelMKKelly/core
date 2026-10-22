"""The London Air data layer.

Fetches and caches the parsed London Air data via the ``pylondonair``
library, throttled to a 30-minute interval. This is a plain shared object
(not a ``DataUpdateCoordinator``); sensors read :attr:`data` and trigger
refreshes through :meth:`async_update`.
"""

from datetime import datetime
import logging

from pylondonair import (
    LondonAirClient,
    LondonAirConnectionError,
    LondonAirData,
    LondonAirUpdateError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LondonAirDataUpdater:
    """Fetch and cache London Air data, throttled to a 30-minute interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data updater."""
        self._client = LondonAirClient(session=async_get_clientsession(hass))
        self.data: LondonAirData | None = None
        self._last_update: datetime | None = None
        self._first_refresh = True

    async def async_update(self) -> None:
        """Fetch the latest data, throttled to SCAN_INTERVAL.

        Raises ConfigEntryNotReady on the first refresh if the fetch fails,
        so the config entry setup is retried. Subsequent failures log a
        warning and clear the cached data (sensors become unavailable).
        """
        now = dt_util.utcnow()
        if self._last_update is not None and now - self._last_update < SCAN_INTERVAL:
            return
        self._last_update = now
        try:
            self.data = await self._client.async_update()
        except (LondonAirConnectionError, LondonAirUpdateError) as err:
            if self._first_refresh:
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="config_entry_not_ready",
                ) from err
            self.data = None
            _LOGGER.warning("Error fetching London Air data: %s", err)
        finally:
            self._first_refresh = False


type LondonAirConfigEntry = ConfigEntry[LondonAirDataUpdater]
