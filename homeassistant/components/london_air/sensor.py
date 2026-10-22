"""Sensor platform for the London Air integration."""

from collections.abc import Callable
from datetime import datetime
from typing import Any, override

import probatio
from pylondonair import NO_SPECIES_DATA, Site

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import AUTHORITIES, CONF_LOCATIONS, DOMAIN, SCAN_INTERVAL
from .data import LondonAirConfigEntry, LondonAirDataUpdater

PARALLEL_UPDATES = 0

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        probatio.Optional(CONF_LOCATIONS, default=AUTHORITIES): probatio.All(
            probatio.EnsureList(), [probatio.In(AUTHORITIES)]
        )
    }
)


def _merge_import_locations(hass: HomeAssistant, config: ConfigType) -> None:
    """Merge imported locations into the existing entry, if any."""
    entry = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, DOMAIN)
    if entry is None:
        return
    locations = list(entry.data[CONF_LOCATIONS])
    for location in config[CONF_LOCATIONS]:
        if location not in locations:
            locations.append(location)
    if locations != entry.data[CONF_LOCATIONS]:
        hass.config_entries.async_update_entry(entry, data={CONF_LOCATIONS: locations})
        hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the London Air sensor platform from YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=config
    )
    _merge_import_locations(hass, config)
    if result.get("type") is FlowResultType.ABORT and result.get("reason") not in {
        "already_configured",
        "single_instance_allowed",
    }:
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"deprecated_yaml_import_issue_{result.get('reason')}",
            breaks_in_ha_version="2027.5.0",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.ERROR,
            translation_key="deprecated_yaml_import_issue",
            translation_placeholders={
                "domain": DOMAIN,
                "integration_title": "London Air",
            },
        )
        return

    ir.async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        breaks_in_ha_version="2027.5.0",
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={
            "domain": DOMAIN,
            "integration_title": "London Air",
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LondonAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up London Air sensors from a config entry."""
    data_updater = entry.runtime_data
    async_add_entities(
        LondonAirSensor(data_updater, authority)
        for authority in entry.data[CONF_LOCATIONS]
    )


def _site_to_dict(site: Site) -> dict[str, Any]:
    """Serialize a site to the legacy attribute shape."""
    pollutants: list[dict[str, str] | str] = [
        {
            "description": pollutant.description,
            "code": pollutant.code,
            "quality": pollutant.quality,
            "index": pollutant.index,
            "summary": pollutant.summary,
        }
        for pollutant in site.pollutants
    ]
    if not pollutants:
        pollutants = [NO_SPECIES_DATA]
    return {
        "updated": site.updated.strftime("%Y-%m-%d %H:%M:%S"),
        "latitude": site.latitude,
        "longitude": site.longitude,
        "site_code": site.site_code,
        "site_name": site.site_name,
        "site_type": site.site_type,
        "pollutants": pollutants,
        "pollutants_status": site.status,
        "number_of_pollutants": site.number_of_pollutants,
    }


class LondonAirSensor(SensorEntity):
    """Sensor reporting the air quality band for a London authority."""

    _attr_name: str
    _attr_icon = "mdi:cloud-outline"

    def __init__(
        self,
        data_updater: LondonAirDataUpdater,
        authority: str,
    ) -> None:
        """Initialize the sensor."""
        self._data_updater = data_updater
        self._authority = authority
        self._attr_name = authority
        self._attr_unique_id = authority
        self._unsub_refresh: Callable[[], None] | None = None
        self._update_attributes()

    @override
    @property
    def available(self) -> bool:
        """Return True if the data layer has data."""
        return self._data_updater.data is not None

    @override
    async def async_added_to_hass(self) -> None:
        """Start the 30-minute refresh timer."""
        await super().async_added_to_hass()
        self._unsub_refresh = async_track_time_interval(
            self.hass, self._async_refresh, SCAN_INTERVAL
        )

    @override
    async def async_will_remove_from_hass(self) -> None:
        """Stop the refresh timer."""
        if self._unsub_refresh is not None:
            self._unsub_refresh()
            self._unsub_refresh = None

    async def _async_refresh(self, _now: datetime) -> None:
        """Refresh the sensor from the data layer."""
        await self._data_updater.async_update()
        self._update_attributes()
        self.async_write_ha_state()

    def _update_attributes(self) -> None:
        """Set the sensor attributes from the data layer."""
        data = self._data_updater.data
        authority = data.authorities.get(self._authority) if data else None
        if authority is None:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return
        self._attr_native_value = authority.status
        self._attr_extra_state_attributes = {
            "sites": len(authority.sites),
            "updated": (
                authority.sites[0].updated.strftime("%Y-%m-%d %H:%M:%S")
                if authority.sites
                else None
            ),
            "data": [_site_to_dict(site) for site in authority.sites],
        }
