"""Media source provider for SonicFlow."""
from __future__ import annotations

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


async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    """Set up SonicFlow media source."""
    return SonicFlowMediaSource(hass)


class SonicFlowMediaSource(MediaSource):
    """Provide SonicFlow as media source."""
    
    domain = DOMAIN
    name = "SonicFlow"
    
    def __init__(self, hass: HomeAssistant):
        super().__init__(DOMAIN)
        self.hass = hass
    
    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Return media."""
        # Можно переиспользовать build_browse_media из media_player
        from .media_player import build_browse_media
        # ... реализация ...
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=item.identifier,
            title="SonicFlow",
            can_play=False,
            can_expand=True,
        )
    
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a URL."""
        # item.identifier = song_id
        # Вернуть стрим-ссылку с авторизацией
        return PlayMedia(
            url=f"https://.../rest/stream.view?id={item.identifier}&...",
            mime_type="audio/mpeg",
        )