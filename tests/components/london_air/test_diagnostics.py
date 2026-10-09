"""Tests for the London Air diagnostics."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.london_air.const import CONF_LOCATIONS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_session: MagicMock,
    api_payload: dict[str, Any],
) -> None:
    """Test the config entry diagnostics."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value=api_payload)
    mock_session.get.return_value = response

    mock_config_entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry
    )
    assert diagnostics["entry"]["data"][CONF_LOCATIONS] == ["Merton"]
    assert len(diagnostics["data"]["Merton"]) == 2
    assert diagnostics["data"]["Merton"][0]["site_code"] == "ME2"
