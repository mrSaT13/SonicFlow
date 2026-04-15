"""Complete Subsonic/Navidrome API Client."""
from __future__ import annotations

import socket
import aiohttp
import asyncio
import hashlib
import secrets
import logging
from typing import TYPE_CHECKING
from aiohttp import hdrs
from dataclasses import dataclass, field

from .xmlHelper import (
    get_root_attrs,
    elements_to_dicts,
    element_to_dict,
    elements_to_texts,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class SubsonicApi:
    userAgent: str
    config: dict
    session: aiohttp.ClientSession | None = None
    requestTimeout: float = 10.0
    apiVersion: str = "1.16.1"
    _close_session: bool = field(default=False, init=False, repr=False)

    @property
    def url(self) -> str: return self.config.get("url", "")
    @property
    def user(self) -> str: return self.config.get("user", "")
    @property
    def password(self) -> str: return self.config.get("password", "")

    @property
    def salt(self) -> str: return secrets.token_hex(6)

    def _token(self, salt: str) -> str:
        return hashlib.md5((self.password + salt).encode()).hexdigest()

    def _get_session(self, hass: HomeAssistant | None = None):
        if self.session is None:
            if hass:
                from homeassistant.helpers.aiohttp_client import async_get_clientsession
                self.session = async_get_clientsession(hass)
            else:
                self.session = aiohttp.ClientSession()
                self._close_session = True
        return self.session

    def _auth_params(self) -> dict:
        s = self.salt
        return {"u": self.user, "t": self._token(s), "s": s, "v": self.apiVersion, "c": self.userAgent}

    async def _request(self, method: str, path: str, params: dict | None = None, hass: HomeAssistant | None = None):
        url = f"{self.url}/rest/{path}.view"
        p = self._auth_params()
        if params: p.update(params)
        
        session = self._get_session(hass)
        try:
            async with asyncio.timeout(self.requestTimeout):
                async with session.request(method, url, params=p, headers={hdrs.USER_AGENT: self.userAgent}) as resp:
                    resp.raise_for_status()
                    return await resp.text()
        except asyncio.TimeoutError as e:
            _LOGGER.error("Timeout on %s: %s", path, e)
            raise
        except Exception as e:
            _LOGGER.error("Request failed on %s: %s", path, e)
            raise

    async def close(self):
        if self.session and self._close_session:
            await self.session.close()
            self._close_session = False

    async def ping(self, hass: HomeAssistant | None = None) -> bool:
        try:
            xml = await self._request("GET", "ping", hass=hass)
            return get_root_attrs(xml).get("status") == "ok"
        except Exception as e:
            _LOGGER.error("Ping failed: %s", e)
            return False

    # 🎵 Stream & Cover URLs (генерируются свежими при каждом вызове!)
    def get_stream_url(self, song_id: str) -> str:
        p = self._auth_params()
        p["id"] = song_id
        query = "&".join(f"{k}={v}" for k, v in p.items())
        return f"{self.url}/rest/stream.view?{query}"

    def get_cover_art_url(self, cover_id: str) -> str | None:
        if not cover_id: return None
        p = self._auth_params()
        p["id"] = cover_id
        query = "&".join(f"{k}={v}" for k, v in p.items())
        return f"{self.url}/rest/getCoverArt.view?{query}"

    # 📚 Library Endpoints
    async def get_artists(self, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getArtists", hass=hass)
        # Subsonic возвращает <artists><artist>...</artist>...</artists>
        return elements_to_dicts(xml, "artist")

    async def get_artist(self, artist_id: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getArtist", {"id": artist_id}, hass=hass)
        data = element_to_dict(xml, "artist")
        data["albums"] = elements_to_dicts(xml, "album")
        return data

    async def get_album(self, album_id: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getAlbum", {"id": album_id}, hass=hass)
        data = element_to_dict(xml, "album")
        data["songs"] = elements_to_dicts(xml, "song")
        return data

    async def get_song(self, song_id: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getSong", {"id": song_id}, hass=hass)
        return element_to_dict(xml, "song")

    async def get_playlists(self, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getPlaylists", hass=hass)
        return elements_to_dicts(xml, "playlist")

    async def get_playlist(self, playlist_id: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getPlaylist", {"id": playlist_id}, hass=hass)
        data = element_to_dict(xml, "playlist")
        data["songs"] = elements_to_dicts(xml, "entry")
        return data

    async def get_genres(self, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getGenres", hass=hass)
        return elements_to_texts(xml, "genre")

    async def get_songs_by_genre(self, genre: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getSongsByGenre", {"genre": genre}, hass=hass)
        return elements_to_dicts(xml, "song")

    async def get_radio_stations(self, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getInternetRadioStations", hass=hass)
        return elements_to_dicts(xml, "internetRadioStation")

    async def get_random_songs(self, size: int = 50, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getRandomSongs", {"size": size}, hass=hass)
        return elements_to_dicts(xml, "song")

    async def search(self, query: str, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "search3", {"query": query, "artistCount": 20, "albumCount": 20, "songCount": 50}, hass=hass)
        return {
            "artists": elements_to_dicts(xml, "artist"),
            "albums": elements_to_dicts(xml, "album"),
            "songs": elements_to_dicts(xml, "song")
        }

    async def get_now_playing(self, hass: HomeAssistant | None = None):
        xml = await self._request("GET", "getNowPlaying", hass=hass)
        return elements_to_dicts(xml, "entry")

    async def scrobble(self, song_id: str, submission: bool = True, hass: HomeAssistant | None = None) -> bool:
        try:
            await self._request("GET", "scrobble", {"id": song_id, "submission": "true" if submission else "false"}, hass=hass)
            return True
        except Exception as e:
            _LOGGER.error("Scrobble failed: %s", e)
            return False
