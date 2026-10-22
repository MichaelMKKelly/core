"""Tests for the London Air data layer."""

from unittest.mock import AsyncMock, MagicMock

from freezegun.api import FrozenDateTimeFactory
from pylondonair import LondonAirConnectionError, LondonAirData
import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.london_air.const import SCAN_INTERVAL
from homeassistant.components.london_air.data import LondonAirDataUpdater
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.core import HomeAssistant


async def test_first_refresh_failure_raises(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
) -> None:
    """Test the first refresh failure raises ConfigEntryNotReady."""
    mock_data_client.async_update = AsyncMock(
        side_effect=LondonAirConnectionError("test")
    )

    updater = LondonAirDataUpdater(hass, mock_config_entry)

    with pytest.raises(ConfigEntryNotReady):
        await updater.async_update()


async def test_subsequent_failure_clears_data(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test a subsequent refresh failure clears the cached data."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    updater = LondonAirDataUpdater(hass, mock_config_entry)
    await updater.async_update()
    assert updater.data is london_air_data

    freezer.tick(SCAN_INTERVAL)
    mock_data_client.async_update.side_effect = LondonAirConnectionError("test")
    await updater.async_update()
    assert updater.data is None


async def test_throttle(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test refreshes are throttled to the scan interval."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    updater = LondonAirDataUpdater(hass, mock_config_entry)
    await updater.async_update()
    await updater.async_update()

    assert mock_data_client.async_update.call_count == 1


async def test_success_caching(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test a successful refresh caches the data."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    updater = LondonAirDataUpdater(hass, mock_config_entry)
    await updater.async_update()

    assert updater.data is london_air_data
