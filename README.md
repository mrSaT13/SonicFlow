# SonicFlow - Music Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## About

**SonicFlow** is a custom integration for Home Assistant that allows you to control and stream music from your Subsonic/Navidrome music server directly from Home Assistant.

### Features

- 🎵 Browse your music library (Artists, Albums, Playlists, Genres)
- 🎧 Stream music through Home Assistant media players
- ⭐ Access your favorite tracks, albums, and artists
- 📻 Internet radio support
- 🎼 Smart playlists and recommendations
- 🔄 Real-time scrobbling to Last.fm
- 🎨 Beautiful cover art integration

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository: `https://github.com/your-github-username/sonicflow`
6. Select category: "Integration"
7. Click "Add"
8. Find "SonicFlow" in the list and click "Download"
9. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release from [GitHub](https://github.com/your-github-username/sonicflow/releases)
2. Copy the `custom_components/sonicflow` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **SonicFlow**
4. Fill in the required information:
   - **URL**: Your Subsonic/Navidrome server URL (e.g., `http://192.168.1.100:4533`)
   - **Username**: Your Subsonic username
   - **Password**: Your Subsonic password
   - **App Type**: Choose between Subsonic or Navidrome
   - **Title**: Custom name (optional)

5. Select what to display:
   - ✅ Artists
   - ✅ Albums
   - ✅ Playlists
   - ✅ Genres
   - ✅ Radio
   - ✅ Favorites
   - ✅ Songs

### YAML Configuration

```yaml
# Example configuration.yaml entry
sonicflow:
  - url: http://192.168.1.100:4533
    user: your_username
    password: your_password
    app: navidrome
    title: My Music Server
```

### Usage

### Media Browser
After setup, you can browse your music library through the Home Assistant Media Browser:
Go to Media in the sidebar
Select your SonicFlow media player
Browse by:
Artists
Albums
Playlists
Genres
Favorites
Songs
Media Player Controls
The integration creates a media player entity that you can control:

### Example automation
```yaml
automation:
  - alias: "Play morning playlist"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: media_player.play_media
      target:
        entity_id: media_player.sonicflow
      data:
        media_content_id: "playlist:123"
        media_content_type: "playlist"
```
###  Entities
Media Player
Entity ID: media_player.sonicflow
Features:
Play/Pause/Stop
Next/Previous track
Volume control
Shuffle/Repeat modes
###  Media Source
Access your music library through Home Assistant's media source system.
###  API Compatibility
SonicFlow is compatible with:
✅ Subsonic API v1.16.1+
✅ Navidrome
✅ Airsonic
✅ Libresonic
✅ Other Subsonic-compatible servers
###  Troubleshooting
### Connection Issues
Make sure your Subsonic server is accessible from Home Assistant
Check the URL (must include http:// or https://)
Verify username and password
Check firewall settings
### No Music Appearing
Ensure your music library is scanned
Check that you've enabled the desired categories in configuration
Verify user permissions on the Subsonic server

###  Credits
Original work based on ha-subsonic by @tiorac
###  License
This project is licensed under the MIT License - see the LICENSE file for details.
