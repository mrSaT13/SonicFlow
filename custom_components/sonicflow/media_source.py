"""Media source provider for SonicFlow."""
from __future__ import annotations

import logging
from homeassistant.components.media_player import MediaClass, MediaType
from homeassistant.components.media_source.error import Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .subsonicApi import SubsonicApi
from .translation import getTranslation

_LOGGER = logging.getLogger(__name__)


def _cover_art_url(api: SubsonicApi, item: dict) -> str | None:
    art = item.get("coverArt")
    if art:
        return api.get_cover_art_url(art)
    return None


class SubsonicSource(MediaSource):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(DOMAIN)
        self.hass = hass
        self.entry = entry
        self.__api = None
        self.name = self.title

    @property
    def title(self) -> str:
        return "SonicFlow" if self.entry is None else self.entry.title

    @property
    def artists(self) -> bool:
        return self._get_option("artists", True)

    @property
    def albums(self) -> bool:
        return self._get_option("albums", True)

    @property
    def playlists(self) -> bool:
        return self._get_option("playlists", True)

    @property
    def favorites(self) -> bool:
        return self._get_option("favorites", True)

    @property
    def genres(self) -> bool:
        return self._get_option("genres", True)

    @property
    def radio(self) -> bool:
        return self._get_option("radio", False)

    @property
    def songs(self) -> bool:
        return self._get_option("songs", True)

    @property
    def api(self) -> SubsonicApi:
        if self.__api is None:
            self.__api = self.hass.data[DOMAIN][self.entry.entry_id]
        return self.__api

    def _get_option(self, option, default=None):
        if (self.entry is not None
                and self.entry.options is not None
                and option in self.entry.options):
            return self.entry.options[option]
        return default

    def _tr(self, key: str) -> str:
        lang = self.hass.config.language
        return getTranslation(lang, key)

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        if item.identifier is None:
            raise Unresolvable("No media identifier")

        if item.identifier.startswith("radio/"):
            return await self._resolve_radio(item.identifier)

        if item.identifier.startswith("song/"):
            return await self._resolve_song(item.identifier)

        raise Unresolvable(f"Can't resolve media item: {item.identifier}")

    async def _resolve_radio(self, identifier: str) -> PlayMedia:
        radio_id = identifier.removeprefix("radio/")
        radios = await self.api.get_radio_stations(hass=self.hass)
        radio = next((r for r in radios if r["id"] == radio_id), None)
        if radio is None:
            raise Unresolvable(f"Radio {radio_id} not found")
        return PlayMedia(radio["streamUrl"], "audio/mpeg")

    async def _resolve_song(self, identifier: str) -> PlayMedia:
        song_id = identifier.removeprefix("song/")
        song = await self.api.get_song(song_id, hass=self.hass)
        content_type = song.get("contentType", "audio/mpeg")
        stream_url = self.api.get_stream_url(song_id)
        return PlayMedia(stream_url, content_type)

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        identifier = item.identifier or ""

        if identifier.startswith("browser/"):
            return await self._browse_category(identifier.removeprefix("browser/"))
        if identifier.startswith("album/"):
            return await self._browse_album(identifier.removeprefix("album/"))
        if identifier.startswith("playlist/"):
            return await self._browse_playlist(identifier.removeprefix("playlist/"))
        if identifier.startswith("genre/"):
            return await self._browse_genre(identifier.removeprefix("genre/"))
        if identifier.startswith("artist/"):
            return await self._browse_artist(identifier.removeprefix("artist/"))

        return await self._browse_root()

    async def _browse_root(self) -> BrowseMediaSource:
        children = []

        if self.artists:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/artists",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("artists"), can_play=False, can_expand=True,
            ))
        if self.albums:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/albums",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("albums"), can_play=False, can_expand=True,
            ))
        if self.playlists:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/playlists",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("playlists"), can_play=False, can_expand=True,
            ))
        if self.favorites:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/favorites",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("favorites"), can_play=False, can_expand=True,
            ))
        if self.genres:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/genres",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("genres"), can_play=False, can_expand=True,
            ))
        if self.radio:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/radio",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("radios"), can_play=False, can_expand=True,
            ))
        if self.songs:
            children.append(BrowseMediaSource(
                domain=DOMAIN, identifier="browser/recent",
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=self._tr("recently_added"), can_play=False, can_expand=True,
            ))
        children.append(BrowseMediaSource(
            domain=DOMAIN, identifier="browser/random",
            media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
            title=self._tr("random"), can_play=False, can_expand=True,
        ))

        return BrowseMediaSource(
            domain=DOMAIN, identifier=None,
            media_class=MediaClass.CHANNEL, media_content_type=MediaType.MUSIC,
            title=self.title, can_play=False, can_expand=True,
            thumbnail="https://avatars.githubusercontent.com/u/26692192?s=256",
            children_media_class=MediaClass.DIRECTORY, children=children,
        )

    async def _browse_category(self, category: str) -> BrowseMediaSource:
        handlers = {
            "artists": (self._tr("artists"), self._list_artists, MediaClass.ARTIST),
            "albums": (self._tr("albums"), self._list_albums, MediaClass.ALBUM),
            "playlists": (self._tr("playlists"), self._list_playlists, MediaClass.PLAYLIST),
            "favorites": (self._tr("favorites"), self._list_favorites, MediaClass.MUSIC),
            "genres": (self._tr("genres"), self._list_genres, MediaClass.GENRE),
            "radio": (self._tr("radios"), self._list_radios, MediaClass.MUSIC),
            "recent": (self._tr("recently_added"), self._list_recent, MediaClass.MUSIC),
            "random": (self._tr("random"), self._list_random, MediaClass.MUSIC),
        }
        if category not in handlers:
            return BrowseMediaSource(
                domain=DOMAIN, identifier=category,
                media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
                title=category, can_play=False, can_expand=False,
            )
        title, handler, child_type = handlers[category]
        items = await handler()
        return BrowseMediaSource(
            domain=DOMAIN, identifier=f"browser/{category}",
            media_class=MediaClass.DIRECTORY, media_content_type=MediaType.MUSIC,
            title=title, can_play=False, can_expand=True,
            children_media_class=child_type, children=items,
        )

    async def _list_radios(self) -> list[BrowseMediaSource]:
        items = []
        radios = await self.api.get_radio_stations(hass=self.hass)
        for radio in radios:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"radio/{radio['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=radio.get("name", "Radio"), can_play=True, can_expand=False,
            ))
        return items

    async def _list_albums(self) -> list[BrowseMediaSource]:
        items = []
        albums = await self.api.get_albums(hass=self.hass)
        for album in albums:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"album/{album['id']}",
                media_class=MediaClass.ALBUM, media_content_type=MediaType.ALBUM,
                title=album.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, album),
            ))
        return items

    async def _list_playlists(self) -> list[BrowseMediaSource]:
        items = []
        playlists = await self.api.get_playlists(hass=self.hass)
        for pl in playlists:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"playlist/{pl['id']}",
                media_class=MediaClass.PLAYLIST, media_content_type=MediaType.PLAYLIST,
                title=pl.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, pl),
            ))
        return items

    async def _list_genres(self) -> list[BrowseMediaSource]:
        items = []
        genres = await self.api.get_genres(hass=self.hass)
        for genre in genres:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"genre/{genre}",
                media_class=MediaClass.GENRE, media_content_type=MediaType.MUSIC,
                title=genre, can_play=False, can_expand=True,
            ))
        return items

    async def _list_artists(self) -> list[BrowseMediaSource]:
        items = []
        artists = await self.api.get_artists(hass=self.hass)
        for artist in artists:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"artist/{artist['id']}",
                media_class=MediaClass.ARTIST, media_content_type=MediaType.MUSIC,
                title=artist.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, artist),
            ))
        return items

    async def _list_favorites(self) -> list[BrowseMediaSource]:
        starred = await self.api.get_starred(hass=self.hass)
        items = []
        for song in starred.get("songs", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, song),
            ))
        for album in starred.get("albums", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"album/{album['id']}",
                media_class=MediaClass.ALBUM, media_content_type=MediaType.ALBUM,
                title=album.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, album),
            ))
        for artist in starred.get("artists", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"artist/{artist['id']}",
                media_class=MediaClass.ARTIST, media_content_type=MediaType.MUSIC,
                title=artist.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, artist),
            ))
        return items

    async def _list_recent(self) -> list[BrowseMediaSource]:
        songs = await self.api.get_random_songs(50, hass=self.hass)
        items = []
        for song in songs:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, song),
            ))
        return items

    async def _list_random(self) -> list[BrowseMediaSource]:
        songs = await self.api.get_random_songs(30, hass=self.hass)
        items = []
        for song in songs:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, song),
            ))
        return items

    async def _browse_album(self, album_id: str) -> BrowseMediaSource:
        album = await self.api.get_album(album_id, hass=self.hass)
        items = []
        for song in album.get("songs", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, album),
            ))
        return BrowseMediaSource(
            domain=DOMAIN, identifier=f"album/{album_id}",
            media_class=MediaClass.ALBUM, media_content_type=MediaType.ALBUM,
            title=album.get("name", "Unknown"), can_play=False, can_expand=True,
            thumbnail=_cover_art_url(self.api, album),
            children_media_class=MediaClass.MUSIC, children=items,
        )

    async def _browse_playlist(self, playlist_id: str) -> BrowseMediaSource:
        playlist = await self.api.get_playlist(playlist_id, hass=self.hass)
        items = []
        for song in playlist.get("songs", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, playlist),
            ))
        return BrowseMediaSource(
            domain=DOMAIN, identifier=f"playlist/{playlist_id}",
            media_class=MediaClass.PLAYLIST, media_content_type=MediaType.PLAYLIST,
            title=playlist.get("name", "Unknown"), can_play=False, can_expand=True,
            thumbnail=_cover_art_url(self.api, playlist),
            children_media_class=MediaClass.MUSIC, children=items,
        )

    async def _browse_genre(self, genre_id: str) -> BrowseMediaSource:
        songs = await self.api.get_songs_by_genre(genre_id, hass=self.hass)
        items = []
        for song in songs:
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"song/{song['id']}",
                media_class=MediaClass.MUSIC, media_content_type=MediaType.MUSIC,
                title=song.get("title", "Unknown"), can_play=True, can_expand=False,
                thumbnail=_cover_art_url(self.api, song),
            ))
        return BrowseMediaSource(
            domain=DOMAIN, identifier=f"genre/{genre_id}",
            media_class=MediaClass.GENRE, media_content_type=MediaType.MUSIC,
            title=genre_id, can_play=False, can_expand=True,
            children_media_class=MediaClass.MUSIC, children=items,
        )

    async def _browse_artist(self, artist_id: str) -> BrowseMediaSource:
        artist = await self.api.get_artist(artist_id, hass=self.hass)
        items = []
        for album in artist.get("albums", []):
            items.append(BrowseMediaSource(
                domain=DOMAIN, identifier=f"album/{album['id']}",
                media_class=MediaClass.ALBUM, media_content_type=MediaType.ALBUM,
                title=album.get("name", "Unknown"), can_play=False, can_expand=True,
                thumbnail=_cover_art_url(self.api, album),
            ))
        return BrowseMediaSource(
            domain=DOMAIN, identifier=f"artist/{artist_id}",
            media_class=MediaClass.ARTIST, media_content_type=MediaType.MUSIC,
            title=artist.get("name", "Unknown"), can_play=False, can_expand=True,
            thumbnail=_cover_art_url(self.api, artist),
            children_media_class=MediaClass.ALBUM, children=items,
        )


async def async_get_media_source(hass: HomeAssistant) -> SubsonicSource:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return SubsonicSource(hass, None)
    return SubsonicSource(hass, entries[0])
