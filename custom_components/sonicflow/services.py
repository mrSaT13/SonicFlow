"""Services for SonicFlow."""
from __future__ import annotations

import logging
import random

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_PLAY_FAVORITE,
    SERVICE_PLAY_RANDOM,
    SERVICE_SEARCH_AND_PLAY,
    SERVICE_STAR,
    SERVICE_UNSTAR,
    ATTR_SONG_ID,
    ATTR_QUERY,
    ATTR_ITEM_ID,
)

_LOGGER = logging.getLogger(__name__)


def _get_api(hass: HomeAssistant):
    """Get the first API instance."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None
    return hass.data[DOMAIN].get(entries[0].entry_id)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register SonicFlow services."""

    async def handle_play_favorite(call: ServiceCall) -> None:
        api = _get_api(hass)
        if not api:
            _LOGGER.error("No SonicFlow API available")
            return

        starred = await api.get_starred(hass=hass)
        songs = starred.get("songs", [])
        if not songs:
            _LOGGER.warning("No favorite songs found")
            return

        song = random.choice(songs)
        song_id = song.get("id")
        if not song_id:
            return

        players = hass.states.async_entity_ids("media_player")
        for player_id in players:
            state = hass.states.get(player_id)
            if state and state.state in ("playing", "paused", "idle"):
                stream_url = api.get_stream_url(song_id)
                await hass.services.async_call(
                    "media_player", "play_media",
                    {"entity_id": player_id, "media_content_id": stream_url, "media_content_type": "music"},
                    blocking=True,
                )
                break

    async def handle_play_random(call: ServiceCall) -> None:
        api = _get_api(hass)
        if not api:
            return

        count = call.data.get("count", 30)
        songs = await api.get_random_songs(count, hass=hass)
        if not songs:
            _LOGGER.warning("No random songs found")
            return

        song = random.choice(songs)
        song_id = song.get("id")
        if not song_id:
            return

        players = hass.states.async_entity_ids("media_player")
        for player_id in players:
            state = hass.states.get(player_id)
            if state and state.state in ("playing", "paused", "idle"):
                stream_url = api.get_stream_url(song_id)
                await hass.services.async_call(
                    "media_player", "play_media",
                    {"entity_id": player_id, "media_content_id": stream_url, "media_content_type": "music"},
                    blocking=True,
                )
                break

    async def handle_search_and_play(call: ServiceCall) -> None:
        api = _get_api(hass)
        if not api:
            return

        query = call.data.get(ATTR_QUERY, "")
        if not query:
            return

        results = await api.search(query, hass=hass)
        songs = results.get("songs", [])
        if not songs:
            _LOGGER.warning("No results for query: %s", query)
            return

        song = songs[0]
        song_id = song.get("id")
        if not song_id:
            return

        players = hass.states.async_entity_ids("media_player")
        for player_id in players:
            state = hass.states.get(player_id)
            if state and state.state in ("playing", "paused", "idle"):
                stream_url = api.get_stream_url(song_id)
                await hass.services.async_call(
                    "media_player", "play_media",
                    {"entity_id": player_id, "media_content_id": stream_url, "media_content_type": "music"},
                    blocking=True,
                )
                break

    async def handle_star(call: ServiceCall) -> None:
        api = _get_api(hass)
        if not api:
            return
        item_id = call.data.get(ATTR_ITEM_ID, "")
        if item_id:
            await api.star(item_id, hass=hass)

    async def handle_unstar(call: ServiceCall) -> None:
        api = _get_api(hass)
        if not api:
            return
        item_id = call.data.get(ATTR_ITEM_ID, "")
        if item_id:
            await api.unstar(item_id, hass=hass)

    hass.services.async_register(DOMAIN, SERVICE_PLAY_FAVORITE, handle_play_favorite)
    hass.services.async_register(DOMAIN, SERVICE_PLAY_RANDOM, handle_play_random)
    hass.services.async_register(DOMAIN, SERVICE_SEARCH_AND_PLAY, handle_search_and_play)
    hass.services.async_register(DOMAIN, SERVICE_STAR, handle_star)
    hass.services.async_register(DOMAIN, SERVICE_UNSTAR, handle_unstar)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload SonicFlow services."""
    for service in [SERVICE_PLAY_FAVORITE, SERVICE_PLAY_RANDOM, SERVICE_SEARCH_AND_PLAY, SERVICE_STAR, SERVICE_UNSTAR]:
        hass.services.async_remove(DOMAIN, service)
