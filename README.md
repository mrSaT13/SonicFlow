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
