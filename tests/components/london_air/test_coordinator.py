"""Tests for the London Air coordinator parsing helpers."""

from typing import Any

import pytest

from homeassistant.components.london_air.coordinator import NO_SPECIES_DATA, data_status


@pytest.mark.parametrize(
    ("site_data", "expected"),
    [
        pytest.param([], "no_sites", id="no_sites"),
        pytest.param([{"pollutants_status": "Low"}], "ok", id="ok"),
        pytest.param(
            [{"pollutants_status": NO_SPECIES_DATA}],
            "no_readings",
            id="no_readings",
        ),
        pytest.param(
            [
                {"pollutants_status": NO_SPECIES_DATA},
                {"pollutants_status": "Low"},
            ],
            "ok",
            id="mixed",
        ),
    ],
)
def test_data_status(site_data: list[dict[str, Any]], expected: str) -> None:
    """Test data_status reflects the availability of authority data."""
    assert data_status(site_data) == expected
