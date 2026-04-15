"""Media player platform for SonicFlow (Lovelace Browser)."""
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SonicFlowBrowser(api, entry)])

class SonicFlowBrowser(MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = MediaPlayerEntityFeature.BROWSE_MEDIA | MediaPlayerEntityFeature.PLAY_MEDIA
    _attr_state = STATE_IDLE

    def __init__(self, api: SubsonicApi, entry: ConfigEntry):
        self.api = api
        self._attr_unique_id = f"{entry.entry_id}_browser"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "SonicFlow"}

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Полностью дублирует media_source структуру для Lovelace."""
        cid = media_content_id or "root"
        if cid == "root":
            return BrowseMedia(media_class=MediaClass.DIRECTORY, media_content_type="library", media_content_id="root", title="🎵 SonicFlow", can_play=False, can_expand=True, children=[
                BrowseMedia(media_class=MediaClass.ARTIST, media_content_type="artists", media_content_id="artists", title="Artists", can_play=False, can_expand=True),
                BrowseMedia(media_class=MediaClass.ALBUM, media_content_type="playlists", media_content_id="playlists", title="Playlists", can_play=False, can_expand=True),
                BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="genres", media_content_id="genres", title="Genres", can_play=False, can_expand=True),
                BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="radio", media_content_id="radio", title="Radio", can_play=False, can_expand=True),
            ])
        try:
            if cid == "artists":
                items = await self.api.get_artists(self.hass)
                children = [BrowseMedia(media_class=MediaClass.ARTIST, media_content_type="artist", media_content_id=f"artist/{a['id']}", title=a.get("name","?"), can_play=False, can_expand=True) for a in items]
            elif cid.startswith("artist/"):
                artist = await self.api.get_artist(cid.split("/")[1], self.hass)
                children = [BrowseMedia(media_class=MediaClass.ALBUM, media_content_type="album", media_content_id=f"album/{alb['id']}", title=alb.get("title","?"), can_play=False, can_expand=True) for alb in artist.get("albums",[])]
            elif cid.startswith("album/"):
                album = await self.api.get_album(cid.split("/")[1], self.hass)
                children = [BrowseMedia(media_class=MediaClass.MUSIC, media_content_type="track", media_content_id=f"track/{s['id']}", title=f"{s.get('track','?')}. {s.get('title','?')}", can_play=True, can_expand=False) for s in album.get("songs",[])]
            elif cid == "playlists":
                items = await self.api.get_playlists(self.hass)
                children = [BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="playlist", media_content_id=f"playlist/{p['id']}", title=p.get("name","?"), can_play=False, can_expand=True) for p in items]
            elif cid.startswith("playlist/"):
                pl = await self.api.get_playlist(cid.split("/")[1], self.hass)
                children = [BrowseMedia(media_class=MediaClass.MUSIC, media_content_type="track", media_content_id=f"track/{s['id']}", title=s.get("title","?"), can_play=True, can_expand=False) for s in pl.get("songs",[])]
            elif cid == "genres":
                items = await self.api.get_genres(self.hass)
                children = [BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="genre", media_content_id=f"genre/{g}", title=g, can_play=False, can_expand=True) for g in items]
            elif cid.startswith("genre/"):
                songs = await self.api.get_songs_by_genre(cid.split("/")[1], self.hass)
                children = [BrowseMedia(media_class=MediaClass.MUSIC, media_content_type="track", media_content_id=f"track/{s['id']}", title=s.get("title","?"), can_play=True, can_expand=False) for s in songs]
            elif cid == "radio":
                items = await self.api.get_radio_stations(self.hass)
                children = [BrowseMedia(media_class=MediaClass.PLAYLIST, media_content_type="track", media_content_id=f"track/{s.get('streamUrl','')}", title=s.get("name","?"), can_play=True, can_expand=False) for s in items]
            else: children = []
            return BrowseMedia(media_class=MediaClass.DIRECTORY, media_content_type=cid, media_content_id=cid, title=cid.replace("_"," ").title(), can_play=False, can_expand=True, children=children)
        except Exception as e:
            _LOGGER.error("Browse failed: %s", e)
            return BrowseMedia(media_class=MediaClass.DIRECTORY, media_content_type="", media_content_id="", title="Error", can_play=False, can_expand=False)

    async def async_play_media(self, media_type: str, media_id: str, **kwargs):
        _LOGGER.info("🎵 Stream requested: %s", media_id[:50])
        self._attr_state = STATE_IDLE
        self.async_write_ha_state()
