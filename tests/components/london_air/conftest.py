"""Fixtures for the London Air integration tests."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from pylondonair import NO_SPECIES_DATA, Authority, LondonAirData, Pollutant, Site
import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.london_air.const import CONF_LOCATIONS, DOMAIN

UPDATED = datetime(2017, 8, 3, 3, 0, 0, tzinfo=ZoneInfo("Europe/London"))


def make_pollutant(
    code: str,
    description: str,
    quality: str,
    index: str,
    index_source: str | None = None,
) -> Pollutant:
    """Build a pollutant."""
    return Pollutant(
        code=code,
        description=description,
        quality=quality,
        index=index,
        summary=f"{code} is {quality}",
        index_source=index_source,
    )


def make_site(
    site_code: str,
    site_name: str,
    pollutants: tuple[Pollutant, ...],
    site_type: str = "Roadside",
    latitude: str = "51.4",
    longitude: str = "-0.1",
    updated: datetime | None = None,
) -> Site:
    """Build a monitoring site."""
    if updated is None:
        updated = UPDATED
    status = pollutants[0].quality if pollutants else NO_SPECIES_DATA
    return Site(
        site_code=site_code,
        site_name=site_name,
        site_type=site_type,
        latitude=latitude,
        longitude=longitude,
        updated=updated,
        pollutants=pollutants,
        status=status,
        number_of_pollutants=len(pollutants),
    )


def make_authority(
    name: str,
    code: str,
    sites: tuple[Site, ...],
    status: str | None,
) -> Authority:
    """Build a local authority."""
    return Authority(
        name=name,
        code=code,
        centre_latitude="51.4",
        centre_longitude="-0.1",
        sites=sites,
        status=status,
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="London Air",
        unique_id=DOMAIN,
        data={CONF_LOCATIONS: ["Merton"]},
    )


@pytest.fixture
def london_air_data() -> LondonAirData:
    """Return LondonAirData matching the london_air.json fixture."""
    merton = make_authority(
        "Merton",
        "24",
        (
            make_site(
                "ME2",
                "Merton Road",
                (
                    make_pollutant(
                        "PM10",
                        "PM10 Particulate",
                        "Low",
                        "2",
                        "Trigger",
                    ),
                ),
                latitude="51.4161384794862",
                longitude="-0.192230805042824",
            ),
            make_site(
                "ME9",
                "Morden Civic Centre 2",
                (
                    make_pollutant(
                        "NO2",
                        "Nitrogen Dioxide",
                        "Low",
                        "1",
                        "Measurement",
                    ),
                ),
                latitude="51.40162",
                longitude="-0.19589212",
            ),
        ),
        "Low",
    )
    city_of_london = make_authority("City of London", "7", (), None)
    return LondonAirData(
        group_name="London",
        time_to_live=38,
        authorities={
            "Merton": merton,
            "City of London": city_of_london,
        },
    )


@pytest.fixture
def no_species_data() -> LondonAirData:
    """Return LondonAirData with a site that has no species data."""
    site = make_site("ME1", "Test Site", ())
    merton = make_authority("Merton", "24", (site,), None)
    return LondonAirData(
        group_name="London",
        time_to_live=38,
        authorities={"Merton": merton},
    )


@pytest.fixture
def mock_flow_client():
    """Patch the config flow's LondonAirClient, yielding the instance mock."""
    with patch(
        "homeassistant.components.london_air.config_flow.LondonAirClient"
    ) as mock_client_cls:
        yield mock_client_cls.return_value


@pytest.fixture
def mock_data_client():
    """Patch the data layer's LondonAirClient, yielding the instance mock."""
    with patch(
        "homeassistant.components.london_air.data.LondonAirClient"
    ) as mock_client_cls:
        yield mock_client_cls.return_value
