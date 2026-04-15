"""Media player platform for SonicFlow (Library/Browser only)."""
from __future__ import annotations

import logging
from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SonicFlow as a media library browser."""
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("SonicFlow API not found in hass.data. Check __init__.py")
        return
        
    api: SubsonicApi = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SonicFlowLibrary(api, entry)])


class SonicFlowLibrary(MediaPlayerEntity):
    """SonicFlow library browser. Does not play audio itself."""
    
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
    )
    _attr_state = STATE_IDLE

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_library"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
            "model": entry.data.get("app", "Subsonic"),
        }

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Build media browser tree. ✅ NO 'domain' parameter."""
        _LOGGER.debug("Browse: %s / %s", media_content_type, media_content_id)

        # 🌳 Root level
        if not media_content_type or media_content_type == "library":
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_type="library",
                media_content_id="root",
                title="🎵 SonicFlow Library",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(media_class=MediaClass.ARTIST, media_content_type="artists", media_content_id="artists", title="Artists", can_play=False, can_expand=True),
                    BrowseMedia(media_class=MediaClass.ALBUM, media_content_type="albums", media_content_id="albums", title="Albums", can_play=False, can_expand=True),
                    BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="playlists", media_content_id="playlists", title="Playlists", can_play=False, can_expand=True),
                ]
            )

        # 🔍 Dynamic branches
        try:
            if media_content_type == "artists":
                items = await self.api.get_artists(hass=self.hass)
                children = [
                    BrowseMedia(media_class=MediaClass.ARTIST, media_content_type="artist", media_content_id=a["id"], title=a.get("name", "?"), can_play=False, can_expand=True)
                    for a in items
                ]
            elif media_content_type == "artist" and media_content_id:
                artist = await self.api.get_artist(media_content_id, hass=self.hass)
                children = [
                    BrowseMedia(media_class=MediaClass.ALBUM, media_content_type="album", media_content_id=alb["id"], title=alb.get("title", "?"), can_play=False, can_expand=True, thumbnail=self.api.get_cover_art_url(alb.get("coverArt", "")))
                    for alb in artist.get("albums", [])
                ]
            elif media_content_type == "album" and media_content_id:
                album = await self.api.get_album(media_content_id, hass=self.hass)
                children = []
                for song in album.get("songs", []):
                    # 🔑 CRITICAL: return DIRECT STREAM URL so HA can send it to ANY target player
                    stream_url = self.api.get_stream_url(song["id"])
                    children.append(BrowseMedia(
                        media_class=MediaClass.MUSIC,
                        media_content_type=MediaType.MUSIC,
                        media_content_id=stream_url,
                        title=f"{song.get('track', '?')}. {song.get('title', '?')}",
                        can_play=True,
                        can_expand=False
                    ))
            elif media_content_type == "playlists":
                items = await self.api.get_playlists(hass=self.hass)
                children = [
                    BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="playlist", media_content_id=p["id"], title=p.get("name", "?"), can_play=False, can_expand=True)
                    for p in items
                ]
            elif media_content_type == "playlist" and media_content_id:
                playlist = await self.api.get_playlist(media_content_id, hass=self.hass)
                children = []
                for song in playlist.get("songs", []):
                    stream_url = self.api.get_stream_url(song["id"])
                    children.append(BrowseMedia(
                        media_class=MediaClass.MUSIC,
                        media_content_type=MediaType.MUSIC,
                        media_content_id=stream_url,
                        title=song.get("title", "?"),
                        can_play=True,
                        can_expand=False
                    ))
            else:
                children = []

            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_type=media_content_type,
                media_content_id=media_content_id,
                title=f"📁 {media_content_type.title()}",
                can_play=False,
                can_expand=True,
                children=children
            )
        except Exception as err:
            _LOGGER.error("Browse failed: %s", err)
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY, media_content_type="", media_content_id="", title="Error", can_play=False, can_expand=False
            )

    async def async_play_media(self, media_type: str, media_id: str, **kwargs):
        """Called when HA sends the stream URL to a target player."""
        _LOGGER.info("🎵 Stream URL requested by HA: %s...", media_id[:50])
        # This entity is a library, it doesn't play audio itself.
        # HA automatically routes media_content_id to the player you selected in the UI.
        self._attr_state = STATE_IDLE
        self.async_write_ha_state()
