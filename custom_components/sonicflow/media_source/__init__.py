"""Media Source platform for SonicFlow (HA Sidebar Media)."""
from __future__ import annotations

import logging
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from ..const import DOMAIN
from ..subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)

async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    return SonicFlowMediaSource(hass)

class SonicFlowMediaSource(MediaSource):
    domain = DOMAIN
    name = "SonicFlow Music"

    def __init__(self, hass: HomeAssistant):
        super().__init__(DOMAIN)
        self.hass = hass
        self.api: SubsonicApi | None = None

    async def _get_api(self) -> SubsonicApi:
        if not self.api:
            entries = self.hass.config_entries.async_entries(DOMAIN)
            if entries:
                self.api = self.hass.data[DOMAIN][entries[0].entry_id]
        return self.api

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        api = await self._get_api()
        if not api: return BrowseMediaSource(domain=DOMAIN, identifier="", title="Not Configured")

        content_id = item.identifier or "root"
        
        if content_id == "root":
            return BrowseMediaSource(
                domain=DOMAIN, identifier="root", title="🎵 SonicFlow", can_play=False, can_expand=True,
                children=[
                    BrowseMediaSource(domain=DOMAIN, identifier="artists", title="🎤 Artists", can_play=False, can_expand=True),
                    BrowseMediaSource(domain=DOMAIN, identifier="albums", title="💿 Albums", can_play=False, can_expand=True),
                    BrowseMediaSource(domain=DOMAIN, identifier="playlists", title="📋 Playlists", can_play=False, can_expand=True),
                    BrowseMediaSource(domain=DOMAIN, identifier="genres", title="🏷️ Genres", can_play=False, can_expand=True),
                    BrowseMediaSource(domain=DOMAIN, identifier="radio", title="📻 Radio", can_play=False, can_expand=True),
                    BrowseMediaSource(domain=DOMAIN, identifier="random", title="🎲 Random Songs", can_play=False, can_expand=True),
                ]
            )

        try:
            if content_id == "artists":
                items = await api.get_artists(self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier="artists", title="Artists", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"artist/{a['id']}", title=a.get("name","?"), can_play=False, can_expand=True) for a in items])
            elif content_id.startswith("artist/"):
                artist_id = content_id.split("/")[1]
                artist = await api.get_artist(artist_id, self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title=artist.get("name","Artist"), can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"album/{alb['id']}", title=alb.get("title","?"), can_play=False, can_expand=True) for alb in artist.get("albums",[])])
            elif content_id == "albums":
                # Navidrome не имеет getAlbumsList2 по умолчанию, используем random/альбомы из артистов или search
                return BrowseMediaSource(domain=DOMAIN, identifier="albums", title="Albums", can_play=False, can_expand=True, children=[])
            elif content_id.startswith("album/"):
                album_id = content_id.split("/")[1]
                album = await api.get_album(album_id, self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title=album.get("title","Album"), can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"track/{s['id']}", title=f"{s.get('track','?')}. {s.get('title','?')}", can_play=True, can_expand=False) for s in album.get("songs",[])])
            elif content_id == "playlists":
                pl = await api.get_playlists(self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier="playlists", title="Playlists", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"playlist/{p['id']}", title=p.get("name","?"), can_play=False, can_expand=True) for p in pl])
            elif content_id.startswith("playlist/"):
                pid = content_id.split("/")[1]
                pl = await api.get_playlist(pid, self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title=pl.get("name","Playlist"), can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"track/{s['id']}", title=s.get("title","?"), can_play=True, can_expand=False) for s in pl.get("songs",[])])
            elif content_id == "genres":
                genres = await api.get_genres(self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier="genres", title="Genres", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"genre/{g}", title=g, can_play=False, can_expand=True) for g in genres])
            elif content_id.startswith("genre/"):
                genre = content_id.split("/")[1]
                songs = await api.get_songs_by_genre(genre, self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title=f"Genre: {genre}", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"track/{s['id']}", title=s.get("title","?"), can_play=True, can_expand=False) for s in songs])
            elif content_id == "radio":
                stations = await api.get_radio_stations(self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier="radio", title="Radio", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"track/{s.get('streamUrl','')}", title=s.get("name","Station"), can_play=True, can_expand=False) for s in stations])
            elif content_id == "random":
                songs = await api.get_random_songs(50, self.hass)
                return BrowseMediaSource(domain=DOMAIN, identifier="random", title="Random", can_play=False, can_expand=True,
                    children=[BrowseMediaSource(domain=DOMAIN, identifier=f"track/{s['id']}", title=f"{s.get('artist','?')} - {s.get('title','?')}", can_play=True, can_expand=False) for s in songs])
            elif content_id.startswith("track/"):
                song_id = content_id.split("/")[1]
                return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title="Track", can_play=True, can_expand=False)
        except Exception as e:
            _LOGGER.error("Browse failed: %s", e)
            
        return BrowseMediaSource(domain=DOMAIN, identifier=content_id, title="Loading...", can_play=False, can_expand=False)

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        api = await self._get_api()
        if not api: raise ValueError("API not ready")
        
        content_id = item.identifier
        if content_id.startswith("track/"):
            # Для радио streamUrl уже полный URL
            raw_id = content_id.split("/")[1]
            if raw_id.startswith("http"):
                return PlayMedia(url=raw_id, mime_type="audio/mpeg")
            return PlayMedia(url=api.get_stream_url(raw_id), mime_type="audio/mpeg")
        raise ValueError(f"Unknown media: {content_id}")
