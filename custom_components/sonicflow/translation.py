"""Translation helper for SonicFlow."""
from __future__ import annotations

LANGUAGES = {
    "en": {
        "artists": "Artists",
        "albums": "Albums",
        "tracks": "Tracks",
        "playlists": "Playlists",
        "radios": "Radios",
        "genres": "Genres",
        "favorites": "Favorites",
        "songs": "Songs",
        "recently_added": "Recently Added",
        "random": "Random",
        "recommendations": "Recommendations",
    },
    "ru": {
        "artists": "Исполнители",
        "albums": "Альбомы",
        "tracks": "Треки",
        "playlists": "Плейлисты",
        "radios": "Радио",
        "genres": "Жанры",
        "favorites": "Избранное",
        "songs": "Песни",
        "recently_added": "Недавно добавленные",
        "random": "Случайные",
        "recommendations": "Рекомендации",
    },
    "pt-BR": {
        "artists": "Artistas",
        "albums": "Álbuns",
        "tracks": "Músicas",
        "playlists": "Playlists",
        "radios": "Rádios",
        "genres": "Gêneros",
        "favorites": "Favoritos",
        "songs": "Músicas",
        "recently_added": "Adicionados Recentemente",
        "random": "Aleatório",
        "recommendations": "Recomendações",
    },
    "de": {
        "artists": "Künstler",
        "albums": "Alben",
        "tracks": "Titel",
        "playlists": "Playlists",
        "radios": "Radios",
        "genres": "Genres",
        "favorites": "Favoriten",
        "songs": "Lieder",
        "recently_added": "Kürzlich hinzugefügt",
        "random": "Zufällig",
        "recommendations": "Empfehlungen",
    },
}


def getTranslation(language: str, key: str) -> str:
    """Get translation for given language and key."""
    if language not in LANGUAGES:
        language = "en"
    if key not in LANGUAGES[language]:
        return LANGUAGES.get("en", {}).get(key, key)
    return LANGUAGES[language][key]
