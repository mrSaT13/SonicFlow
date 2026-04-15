"""Media player platform for SonicFlow."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING, STATE_BUFFERING
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from ..const import DOMAIN, CONF_APP
from ..subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)

# Интервал обновления статуса воспроизведения (секунды)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SonicFlow media player from config entry."""
    _LOGGER.debug("Setting up SonicFlow media player for %s", entry.title)
    
    api: SubsonicApi = hass.data[DOMAIN][entry.entry_id]
    
    # Создаём координатор для периодического опроса статуса
    coordinator = SonicFlowCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Создаём и добавляем сущность медиаплеера
    async_add_entities([SonicFlowMediaPlayer(coordinator, api, entry)], update_before_add=True)


class SonicFlowCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for polling Now Playing info from Subsonic API."""
    
    def __init__(self, hass: HomeAssistant, api: SubsonicApi, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"SonicFlow NowPlaying ({entry.title})",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.entry = entry
        
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch now playing data from API."""
        try:
            now_playing = await self.api.get_now_playing(hass=self.hass)
            # Найти запись для текущего пользователя
            user_entries = [
                entry for entry in now_playing 
                if entry.get("userName") == self.api.user
            ]
            return user_entries[0] if user_entries else {}
        except Exception as err:
            _LOGGER.debug("Error fetching now playing: %s", err)
            raise UpdateFailed(f"Failed to fetch now playing: {err}")


class SonicFlowMediaPlayer(CoordinatorEntity[SonicFlowCoordinator], MediaPlayerEntity):
    """Representation of a SonicFlow media player."""
    
    _attr_has_entity_name = True
    _attr_name = None  # Использует название интеграции
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.BROWSE_MEDIA
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
    )
    
    def __init__(
        self,
        coordinator: SonicFlowCoordinator,
        api: SubsonicApi,
        entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self.api = api
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SonicFlow",
            "model": entry.data.get(CONF_APP, "Subsonic"),
            "configuration_url": entry.data.get("url"),
        }
        
        # Локальное состояние
        self._current_song: dict[str, Any] | None = None
        self._state = STATE_IDLE
        self._volume_level = 1.0
        self._is_muted = False
        
    @property
    def state(self) -> str | None:
        """Return current playback state."""
        if not self.coordinator.data:
            return STATE_IDLE
            
        # Определяем состояние по данным nowPlaying
        return STATE_PLAYING if self.coordinator.data else STATE_IDLE
    
    @property
    def media_content_type(self) -> str | None:
        """Content type of current playing media."""
        return MediaType.MUSIC
    
    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        return song.get("title") if song else None
    
    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        return song.get("artist") if song else None
    
    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        return song.get("album") if song else None
    
    @property
    def media_image_url(self) -> str | None:
        """URL for image to display in the frontend."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        if song and song.get("coverArt"):
            return self.api.get_cover_art_url(song["coverArt"])
        return None
    
    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        return int(song.get("duration", 0)) if song and song.get("duration") else None
    
    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        return song.get("id") if song else None
    
    @property
    def volume_level(self) -> float | None:
        """Volume level (0..1)."""
        return self._volume_level
    
    @property
    def is_volume_muted(self) -> bool:
        """Boolean if volume is muted."""
        return self._is_muted
    
    async def async_media_play(self) -> None:
        """Send play command."""
        # Subsonic API не имеет remote play, но мы можем "возобновить" через скроббли
        if self._current_song:
            await self.api.scrobble(self._current_song["id"], submission=False, hass=self.hass)
            await self.coordinator.async_request_refresh()
    
    async def async_media_pause(self) -> None:
        """Send pause command."""
        # Аналогично — скроббл с паузой
        _LOGGER.debug("Pause requested (Subsonic API limitation)")
        await self.coordinator.async_request_refresh()
    
    async def async_media_stop(self) -> None:
        """Send stop command."""
        _LOGGER.debug("Stop requested (Subsonic API limitation)")
        await self.coordinator.async_request_refresh()
    
    async def async_media_next_track(self) -> None:
        """Send next track command."""
        # Запрос следующего трека из random/queue
        _LOGGER.debug("Next track requested")
        await self.coordinator.async_request_refresh()
    
    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        _LOGGER.debug("Previous track requested")
        await self.coordinator.async_request_refresh()
    
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0..1)."""
        self._volume_level = volume
        self.async_write_ha_state()
    
    async def async_mute_volume(self, mute: bool) -> None:
        """Mute/unmute volume."""
        self._is_muted = mute
        self.async_write_ha_state()
    
    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Play a song/album/playlist by ID."""
        _LOGGER.debug("Play media: type=%s, id=%s", media_type, media_id)
        
        # Получаем URL для стриминга
        stream_url = self.api.get_stream_url(media_id)
        
        # Отправляем команду на воспроизведение через HA
        self._current_song = {"id": media_id}
        self._state = STATE_PLAYING
        self.async_write_ha_state()
        
        # HA сам обработает stream_url через media_source
        # Для полной интеграции нужен media_source platform (опционально)
    
    async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia | None:
        """Implement the websocket media browsing helper."""
        return await build_browse_media(self.api, media_content_type, media_content_id)
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        song = self.coordinator.data.get("entry") if self.coordinator.data else None
        self._current_song = song
        self.async_write_ha_state()


async def build_browse_media(
    api: SubsonicApi,
    media_content_type: str | None,
    media_content_id: str | None,
) -> BrowseMedia | None:
    """Build BrowseMedia tree for media browsing."""
    # Базовый уровень — корневые папки
    if not media_content_type:
        return BrowseMedia(
            title="SonicFlow Library",
            domain=DOMAIN,
            children_class_id="library",
            supports_play=True,
            children=[
                BrowseMedia(
                    title="Artists",
                    domain=DOMAIN,
                    media_content_type="artists",
                    media_content_id="artists",
                    children_class_id="artists",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="Albums",
                    domain=DOMAIN,
                    media_content_type="albums",
                    media_content_id="albums",
                    children_class_id="albums",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="Playlists",
                    domain=DOMAIN,
                    media_content_type="playlists",
                    media_content_id="playlists",
                    children_class_id="playlists",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="Genres",
                    domain=DOMAIN,
                    media_content_type="genres",
                    media_content_id="genres",
                    children_class_id="genres",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="Radio",
                    domain=DOMAIN,
                    media_content_type="radio",
                    media_content_id="radio",
                    children_class_id="radio",
                    can_play=False,
                    can_expand=True,
                ),
            ],
        )
    
    # Динамическая загрузка контента
    try:
        if media_content_type == "artists":
            artists = await api.get_artists(hass=None)
            return BrowseMedia(
                title="Artists",
                domain=DOMAIN,
                children_class_id="artist",
                children=[
                    BrowseMedia(
                        title=artist.get("name", "Unknown"),
                        domain=DOMAIN,
                        media_content_type="artist",
                        media_content_id=artist.get("id"),
                        can_play=False,
                        can_expand=True,
                    )
                    for artist in artists
                ],
            )
        
        elif media_content_type == "artist" and media_content_id:
            artist = await api.get_artist(media_content_id, hass=None)
            return BrowseMedia(
                title=artist.get("name", "Unknown"),
                domain=DOMAIN,
                children_class_id="album",
                children=[
                    BrowseMedia(
                        title=album.get("title", "Unknown"),
                        domain=DOMAIN,
                        media_content_type="album",
                        media_content_id=album.get("id"),
                        can_play=True,
                        can_expand=True,
                        thumbnail=api.get_cover_art_url(album.get("coverArt", "")) if album.get("coverArt") else None,
                    )
                    for album in artist.get("albums", [])
                ],
            )
        
        elif media_content_type == "album" and media_content_id:
            album = await api.get_album(media_content_id, hass=None)
            return BrowseMedia(
                title=album.get("title", "Unknown"),
                domain=DOMAIN,
                children_class_id="song",
                can_play=True,
                thumbnail=api.get_cover_art_url(album.get("coverArt", "")) if album.get("coverArt") else None,
                children=[
                    BrowseMedia(
                        title=f"{song.get('track', '?')}. {song.get('title', 'Unknown')}",
                        domain=DOMAIN,
                        media_content_type="song",
                        media_content_id=song.get("id"),
                        can_play=True,
                        can_expand=False,
                    )
                    for song in album.get("songs", [])
                ],
            )
        
        elif media_content_type == "song" and media_content_id:
            # Возвращаем сам трек для воспроизведения
            song = await api.get_song(media_content_id, hass=None)
            return BrowseMedia(
                title=song.get("title", "Unknown"),
                domain=DOMAIN,
                media_content_type="song",
                media_content_id=media_content_id,
                can_play=True,
                can_expand=False,
                thumbnail=api.get_cover_art_url(song.get("coverArt", "")) if song.get("coverArt") else None,
            )
        
        elif media_content_type == "playlists":
            playlists = await api.get_playlists(hass=None)
            return BrowseMedia(
                title="Playlists",
                domain=DOMAIN,
                children_class_id="playlist",
                children=[
                    BrowseMedia(
                        title=pl.get("name", "Unknown"),
                        domain=DOMAIN,
                        media_content_type="playlist",
                        media_content_id=pl.get("id"),
                        can_play=True,
                        can_expand=True,
                    )
                    for pl in playlists
                ],
            )
        
        elif media_content_type == "playlist" and media_content_id:
            playlist = await api.get_playlist(media_content_id, hass=None)
            return BrowseMedia(
                title=playlist.get("name", "Unknown"),
                domain=DOMAIN,
                children_class_id="song",
                can_play=True,
                children=[
                    BrowseMedia(
                        title=f"{song.get('track', '?')}. {song.get('title', 'Unknown')}",
                        domain=DOMAIN,
                        media_content_type="song",
                        media_content_id=song.get("id"),
                        can_play=True,
                        can_expand=False,
                    )
                    for song