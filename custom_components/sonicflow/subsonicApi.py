"""Subsonic API client for SonicFlow."""
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
    getAttributes,
    getTagAttributes,
    getTagsAttributesToList,
    getTagsTexts,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class SubsonicApi:
    """Subsonic/Navidrome API client."""
    
    userAgent: str
    config: dict
    session: aiohttp.ClientSession | None = None
    requestTimeout: float = 8.0
    apiVersion: str = "1.16.1"
    _close_session: bool = field(default=False, init=False, repr=False)
    
    @property
    def url(self) -> str:
        return self.__getProperty("url")
    
    @property
    def user(self) -> str:
        return self.__getProperty("user")
    
    @property
    def password(self) -> str:
        return self.__getProperty("password")

    @property
    def salt(self) -> str:
        return secrets.token_hex(5)
    
    def __getProperty(self, property_name: str, default_value=None):
        if self.config is None:
            return default_value
        return self.config.get(property_name, default_value)

    def __generate_token(self, password: str, salt: str) -> str:
        return hashlib.md5((password + salt).encode()).hexdigest()

    def _get_session(self, hass: HomeAssistant | None = None):
        """Get or create aiohttp session."""
        if self.session is None:
            if hass is not None:
                from homeassistant.helpers.aiohttp_client import async_get_clientsession
                self.session = async_get_clientsession(hass)
            else:
                self.session = aiohttp.ClientSession()
                self._close_session = True
        return self.session
    
    def __get_request_params(self, params: dict | None = None) -> dict:
        salt = self.salt
        p = {
            "u": self.user,
            "t": self.__generate_token(self.password, salt),
            "s": salt,
            "v": self.apiVersion,
            "c": self.userAgent
        }
        if params:
            p.update(params)
        return p

    async def __request(self, method: str, path: str, params: dict | None = None, hass: HomeAssistant | None = None):
        """Make API request."""
        url = f"{self.url}/rest/{path}.view"
        p = self.__get_request_params(params)
        headers = {hdrs.USER_AGENT: self.userAgent}
        session = self._get_session(hass)

        try:
            async with asyncio.timeout(self.requestTimeout):
                response = await session.request(
                    method, url, headers=headers, params=p, raise_for_status=True
                )
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                return await response.text()
                
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout error: %s", err)
            raise
        except (aiohttp.ClientError, socket.gaierror) as err:
            _LOGGER.error("Connection error: %s", err)
            raise

    async def close(self) -> None:
        """Close session if we created it."""
        if self.session and self._close_session:
            await self.session.close()
            self._close_session = False
    
    async def ping(self, hass: HomeAssistant | None = None) -> bool:
        """Test connection."""
        try:
            response = await self.__request("GET", "ping", hass=hass)
            attrs = getAttributes(response)
            return attrs.get("status") == "ok"
        except Exception as err:
            _LOGGER.error("Ping failed: %s", err)
            return False
    
    async def get_radio_stations(self, hass: HomeAssistant | None = None) -> list:
        response = await self.__request("GET", "getInternetRadioStations", hass=hass)
        return getTagsAttributesToList(response, "internetRadioStation")
    
    async def get_albums(self, hass: HomeAssistant | None = None) -> list:
        response = await self.__request("GET", "getAlbumList2", {"type": "alphabeticalByName"}, hass=hass)
        return getTagsAttributesToList(response, "album")
    
    async def get_album(self, album_id: str, hass: HomeAssistant | None = None) -> dict:
        response = await self.__request("GET", "getAlbum", {"id": album_id}, hass=hass)
        album = getTagAttributes(response, "album")
        album["songs"] = getTagsAttributesToList(response, "song")
        return album

    async def get_playlists(self, hass: HomeAssistant | None = None) -> list:
        response = await self.__request("GET", "getPlaylists", hass=hass)
        return getTagsAttributesToList(response, "playlist")
    
    async def get_playlist(self, playlist_id: str, hass: HomeAssistant | None = None) -> dict:
        response = await self.__request("GET", "getPlaylist", {"id": playlist_id}, hass=hass)
        playlist = getTagAttributes(response, "playlist")
        playlist["songs"] = getTagsAttributesToList(response, "entry")
        return playlist

    async def get_genres(self, hass: HomeAssistant | None = None) -> list[str]:
        response = await self.__request("GET", "getGenres", hass=hass)
        return getTagsTexts(response, "genre")
    
    async def get_songs_by_genre(self, genre: str, hass: HomeAssistant | None = None) -> list:
        response = await self.__request("GET", "getSongsByGenre", {"genre": genre}, hass=hass)
        return getTagsAttributesToList(response, "song")
    
    async def get_artists(self, hass: HomeAssistant | None = None) -> list:
        response = await self.__request("GET", "getArtists", hass=hass)
        return getTagsAttributesToList(response, "artist")
    
    async def get_artist(self, artist_id: str, hass: HomeAssistant | None = None) -> dict:
        response = await self.__request("GET", "getArtist", {"id": artist_id}, hass=hass)
        artist = getTagAttributes(response, "artist")
        artist["albums"] = getTagsAttributesToList(response, "album")
        return artist

    async def get_song(self, song_id: str, hass: HomeAssistant | None = None) -> dict:
        response = await self.__request("GET", "getSong", {"id": song_id}, hass=hass)
        return getTagAttributes(response, "song")

    async def get_starred(self, hass: HomeAssistant | None = None) -> dict:
        """Get starred items."""
        response = await self.__request("GET", "getStarred2", hass=hass)
        return {
            "artists": getTagsAttributesToList(response, "artist"),
            "albums": getTagsAttributesToList(response, "album"),
            "songs": getTagsAttributesToList(response, "song"),
        }

    async def get_random_songs(self, size: int = 50, hass: HomeAssistant | None = None) -> list:
        """Get random songs."""
        response = await self.__request("GET", "getRandomSongs", {"size": size}, hass=hass)
        return getTagsAttributesToList(response, "song")

    async def search(self, query: str, hass: HomeAssistant | None = None) -> dict:
        """Search for artists, albums, songs."""
        response = await self.__request("GET", "search3", {"query": query, "songCount": 50}, hass=hass)
        return {
            "artists": getTagsAttributesToList(response, "artist"),
            "albums": getTagsAttributesToList(response, "album"),
            "songs": getTagsAttributesToList(response, "song"),
        }

    async def star(self, item_id: str, hass: HomeAssistant | None = None) -> bool:
        """Star an item."""
        try:
            await self.__request("GET", "star", {"id": item_id}, hass=hass)
            return True
        except Exception as err:
            _LOGGER.error("Failed to star %s: %s", item_id, err)
            return False

    async def unstar(self, item_id: str, hass: HomeAssistant | None = None) -> bool:
        """Unstar an item."""
        try:
            await self.__request("GET", "unstar", {"id": item_id}, hass=hass)
            return True
        except Exception as err:
            _LOGGER.error("Failed to unstar %s: %s", item_id, err)
            return False

    def get_cover_art_url(self, art_id: str) -> str:
        """Get cover art URL."""
        params = self.__get_request_params({"id": art_id})
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.url}/rest/getCoverArt.view?{query}"

    def get_stream_url(self, song_id: str) -> str:
        """Get stream URL for a song."""
        params = self.__get_request_params({"id": song_id})
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.url}/rest/stream.view?{query}"

    async def __aenter__(self) -> SubsonicApi:
        return self
    
    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()