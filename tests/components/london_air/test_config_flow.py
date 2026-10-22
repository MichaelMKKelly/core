"""Tests for the London Air config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pylondonair import LondonAirConnectionError, LondonAirData
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.london_air.const import CONF_LOCATIONS, DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component


async def test_user(hass: HomeAssistant, mock_flow_client: MagicMock) -> None:
    """Test the user config flow."""
    mock_flow_client.async_test_connection = AsyncMock()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.london_air.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_LOCATIONS: ["Merton"]}
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "London Air"
        assert result["data"] == {CONF_LOCATIONS: ["Merton"]}
        assert result["result"].unique_id == DOMAIN
        await hass.async_block_till_done()

    assert mock_setup_entry.called


async def test_user_required(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test the user config flow with no locations selected."""
    mock_flow_client.async_test_connection = AsyncMock()
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCATIONS: []}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_LOCATIONS: "required"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCATIONS: ["Merton"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()


async def test_user_cannot_connect(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test the user config flow when the API is unreachable."""
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)
    mock_flow_client.async_test_connection = AsyncMock(
        side_effect=LondonAirConnectionError("Connection error")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCATIONS: ["Merton"]}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_flow_client.async_test_connection = AsyncMock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_LOCATIONS: ["Merton"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()


async def test_user_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the user config flow aborts when already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_import(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test importing from YAML configuration."""
    mock_flow_client.async_test_connection = AsyncMock()
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_LOCATIONS: ["Merton"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "London Air"
    assert result["data"] == {CONF_LOCATIONS: ["Merton"]}
    assert result["result"].unique_id == DOMAIN


async def test_import_cannot_connect(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Test importing from YAML when the API is unreachable."""
    mock_flow_client.async_test_connection = AsyncMock(
        side_effect=LondonAirConnectionError("Connection error")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_LOCATIONS: ["Merton"]},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_import_merges_existing_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_flow_client: MagicMock,
    mock_data_client: MagicMock,
    london_air_data: LondonAirData,
) -> None:
    """Test importing from YAML merges locations into an existing entry."""
    mock_flow_client.async_test_connection = AsyncMock()
    mock_data_client.async_update = AsyncMock(return_value=london_air_data)

    mock_config_entry.add_to_hass(hass)

    assert await async_setup_component(
        hass,
        "sensor",
        {"sensor": {"platform": "london_air", "locations": ["City of London"]}},
    )
    await hass.async_block_till_done()
    assert mock_config_entry.data[CONF_LOCATIONS] == ["Merton", "City of London"]
