"""Sensor platform for SonicFlow."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    api: SubsonicApi = hass.data[DOMAIN].get(entry.entry_id)
    if not api:
        return

    async_add_entities([
        SonicFlowNowPlayingSensor(api, entry),
        SonicFlowArtistSensor(api, entry),
        SonicFlowAlbumSensor(api, entry),
    ], update_before_add=True)


class SonicFlowNowPlayingSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Now Playing"
    _attr_icon = "mdi:music-note"

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_now_playing"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
        }
        self._track = {}

    @property
    def native_value(self) -> str | None:
        return self._track.get("title")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "artist": self._track.get("artist", ""),
            "album": self._track.get("album", ""),
            "song_id": self._track.get("id", ""),
            "duration": self._track.get("duration", ""),
        }

    async def async_update(self) -> None:
        try:
            now = await self.api.get_now_playing(hass=self.hass)
            user_tracks = [t for t in now if t.get("userName") == self.api.user]
            self._track = user_tracks[0] if user_tracks else {}
        except Exception as err:
            _LOGGER.debug("Now playing update failed: %s", err)


class SonicFlowArtistSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Current Artist"
    _attr_icon = "mdi:account-music"

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_current_artist"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
        }
        self._track = {}

    @property
    def native_value(self) -> str | None:
        return self._track.get("artist")

    async def async_update(self) -> None:
        try:
            now = await self.api.get_now_playing(hass=self.hass)
            user_tracks = [t for t in now if t.get("userName") == self.api.user]
            self._track = user_tracks[0] if user_tracks else {}
        except Exception as err:
            _LOGGER.debug("Artist update failed: %s", err)


class SonicFlowAlbumSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Current Album"
    _attr_icon = "mdi:album"

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_current_album"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
        }
        self._track = {}

    @property
    def native_value(self) -> str | None:
        return self._track.get("album")

    async def async_update(self) -> None:
        try:
            now = await self.api.get_now_playing(hass=self.hass)
            user_tracks = [t for t in now if t.get("userName") == self.api.user]
            self._track = user_tracks[0] if user_tracks else {}
        except Exception as err:
            _LOGGER.debug("Album update failed: %s", err)
