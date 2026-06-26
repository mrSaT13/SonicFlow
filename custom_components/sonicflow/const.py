"""Constants for SonicFlow integration."""
from __future__ import annotations
import logging
from typing import Final

DOMAIN: Final = "sonicflow"
LOGGER = logging.getLogger(__package__)

# Configuration keys
CONF_URL: Final = "url"
CONF_USER: Final = "user"
CONF_PASSWORD: Final = "password"
CONF_APP: Final = "app"
CONF_ARTISTS: Final = "artists"
CONF_ALBUMS: Final = "albums"
CONF_PLAYLISTS: Final = "playlists"
CONF_GENRES: Final = "genres"
CONF_RADIO: Final = "radio"
CONF_FAVORITES: Final = "favorites"
CONF_SONGS: Final = "songs"

# Defaults
DEFAULT_APP: Final = "navidrome"
DEFAULT_OPTIONS: Final = {
    CONF_ARTISTS: True, CONF_ALBUMS: True, CONF_PLAYLISTS: True,
    CONF_GENRES: True, CONF_RADIO: False, CONF_FAVORITES: True, CONF_SONGS: True,
}

# Translation keys
TITLE: Final = {"subsonic": "Subsonic", "navidrome": "Navidrome"}

# Service constants
SERVICE_PLAY_FAVORITE: Final = "play_favorite"
SERVICE_PLAY_RANDOM: Final = "play_random"
SERVICE_SEARCH_AND_PLAY: Final = "search_and_play"
SERVICE_STAR: Final = "star"
SERVICE_UNSTAR: Final = "unstar"

ATTR_SONG_ID: Final = "song_id"
ATTR_QUERY: Final = "query"
ATTR_ITEM_ID: Final = "item_id"
