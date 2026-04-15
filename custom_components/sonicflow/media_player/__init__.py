"""Media player platform for SonicFlow."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("Setting up media_player for entry %s", entry.entry_id)
    
    if DOMAIN not in hass.data:
        _LOGGER.error("DOMAIN '%s' not in hass.data!", DOMAIN)
        return
    if entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("entry_id '%s' missing in hass.data[%s]!", entry.entry_id, DOMAIN)
        return
        
    api: SubsonicApi = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.info("✅ API retrieved successfully for %s", entry.title)
    
    entity = SonicFlowMediaPlayer(api, entry)
    async_add_entities([entity], update_before_add=True)


class SonicFlowMediaPlayer(MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY |
        MediaPlayerEntityFeature.PAUSE |
        MediaPlayerEntityFeature.STOP |
        MediaPlayerEntityFeature.NEXT_TRACK |
        MediaPlayerEntityFeature.PREVIOUS_TRACK |
        MediaPlayerEntityFeature.VOLUME_SET |
        MediaPlayerEntityFeature.VOLUME_MUTE |
        MediaPlayerEntityFeature.BROWSE_MEDIA |
        MediaPlayerEntityFeature.PLAY_MEDIA
    )

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
            "model": entry.data.get("app", "Subsonic"),
            "configuration_url": entry.data.get("url"),
        }
        self._state = STATE_IDLE
        self._media = {}

    @property
    def state(self) -> str:
        return self._state

    @property
    def media_content_type(self) -> str:
        return MediaType.MUSIC

    @property
    def media_title(self) -> str | None:
        return self._media.get("title")

    @property
    def media_artist(self) -> str | None:
        return self._media.get("artist")

    @property
    def media_album_name(self) -> str | None:
        return self._media.get("album")

    @property
    def media_image_url(self) -> str | None:
        cover = self._media.get("coverArt")
        return self.api.get_cover_art_url(cover) if cover else None

    @property
    def media_duration(self) -> int | None:
        d = self._media.get("duration")
        return int(d) if d else None

    async def async_update(self) -> None:
        try:
            if hasattr(self.api, 'get_now_playing'):
                now = await self.api.get_now_playing(hass=self.hass)
                user_tracks = [t for t in now if t.get("userName") == self.api.user]
                if user_tracks:
                    self._media = user_tracks[0]
                    self._state = STATE_PLAYING
                else:
                    self._media = {}
                    self._state = STATE_IDLE
        except Exception as err:
            _LOGGER.debug("Update skipped: %s", err)

    async def async_media_play(self) -> None:
        self._state = STATE_PLAYING
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        self._state = STATE_IDLE
        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        self._state = STATE_IDLE
        self.async_write_ha_state()

    async def async_media_next_track(self) -> None: pass
    async def async_media_previous_track(self) -> None: pass
    async def async_set_volume_level(self, volume: float) -> None: pass
    async def async_mute_volume(self, mute: bool) -> None: pass

    async def async_play_media(self, media_type: str, media_id: str, **kwargs) -> None:
        _LOGGER.info("▶️ Play requested: %s (type: %s)", media_id, media_type)
        # Формируем авторизованную ссылку на поток
        stream_url = self.api.get_stream_url(media_id)
        self._media = {"id": media_id, "title": media_id, "coverArt": ""}
        self._attr_media_content_id = stream_url
        self._state = STATE_PLAYING
        self.async_write_ha_state()

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Возвращает дерево медиа-библиотеки (исправленная сигнатура HA)."""
        if media_content_type is None or media_content_type == "library":
            return BrowseMedia(
                media_class="directory",
                media_content_type="library",
                media_content_id="",
                title="SonicFlow Library",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        media_class="artist",
                        media_content_type="artists",
                        media_content_id="artists",
                        title="Artists",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        media_class="album",
                        media_content_type="albums",
                        media_content_id="albums",
                        title="Albums",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        media_class="playlist",
                        media_content_type="playlists",
                        media_content_id="playlists",
                        title="Playlists",
                        can_play=False,
                        can_expand=True,
                    ),
                ]
            )
        # Заглушка для вложенных папок (чтобы не падало при клике)
        return BrowseMedia(
            media_class="directory",
            media_content_type=media_content_type or "",
            media_content_id=media_content_id or "",
            title="Loading...",
            can_play=False,
            can_expand=False,
        )
