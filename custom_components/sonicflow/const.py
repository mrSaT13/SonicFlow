"""Constants for SonicFlow integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "sonicflow"

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
    CONF_ARTISTS: True,
    CONF_ALBUMS: True,
    CONF_PLAYLISTS: True,
    CONF_GENRES: True,
    CONF_RADIO: False,
    CONF_FAVORITES: True,
    CONF_SONGS: True,
}

# Translation keys
TITLE: Final = {
    "subsonic": "Subsonic",
    "navidrome": "Navidrome",
}