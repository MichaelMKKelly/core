"""Tests for the London Air integration setup."""

from unittest.mock import AsyncMock, MagicMock

from pylondonair import LondonAirConnectionError, LondonAirData
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.london_air.data import LondonAirDataUpdater
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test setting up the integration from a config entry."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert entry is not None
    assert isinstance(entry.runtime_data, LondonAirDataUpdater)
    assert hass.states.get("sensor.merton") is not None


async def test_setup_retry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
) -> None:
    """Test setup retries when the first refresh fails."""
    mock_data_client.async_update = AsyncMock(
        side_effect=LondonAirConnectionError("test")
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test unloading the integration."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.merton") is not None

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    state = hass.states.get("sensor.merton")
    assert state is not None
    assert state.state == "unavailable"
