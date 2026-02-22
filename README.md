# PARE - Play A Random Episode

A universal TV series random episode player with TVDB integration.

## Features

- 🎲 **Random Episode Selection** - Pick a random episode from any TV series
- 📺 **Embedded Video Player** - Watch episodes directly in the app
- 📖 **TVDB Integration** - Fetch episode titles, descriptions, air dates, and ratings
- ⚙️ **Easy Setup** - Configure your series folder and API key through settings menu
- ⏩ **Playback Controls** - Scrub through video with progress slider, Play/Pause, and Volume control
- ⏭️ **Continuous Play** - Skip to "Next Random" episode instantly
- 🎬 **Universal** - Works with any TV series, not just one show

## Installation

1. **Install Python 3.11+**

2. **Install dependencies:**
   ```bash
   pip install requests python-vlc pillow
   ```

3. **Install VLC Media Player** (if not already installed):
   - Download from: https://www.videolan.org/vlc/
   - **Important**: Install the 64-bit version if using 64-bit Python

## Building Standalone Executable

To create a standalone `PARE.exe` that doesn't require Python:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable:**
   ```bash
   python -m PyInstaller PARE.spec
   ```

3. **Find the executable:**
   - Location: `dist/PARE.exe`
   - Size: ~31 MB (includes all dependencies)
   - No Python installation required to run!

**Note**: The executable bundles Python, all libraries, and assets. VLC Media Player must still be installed separately on the target system.

## Setup

1. **Run PARE:**
   ```bash
   python pare.py
   ```

2. **First-time setup:**
   - Click "Settings" button
   - Browse to your TV series folder (e.g., `D:\Videos\TV SERIES\Frasier`)
   - Enter your TVDB API key (get one free at https://thetvdb.com/api-information)
   - Enter the TVDB Series ID (find it on TheTVDB website)
   - Click "Save Settings"

3. **Play a random episode:**
   - Click "Play Random Episode"
   - Enjoy!

## How to Find TVDB Series ID

1. Go to https://thetvdb.com
2. Search for your TV series
3. Look at the URL: `https://thetvdb.com/series/frasier` → Series slug is "frasier"
4. Or use the numeric ID from the API

## File Structure

```
PARE/
├── pare.py           # Main application
├── config.json       # User settings (auto-generated)
└── README.md         # This file
```



## License

MIT License - Feel free to use and modify!

## Contributing

Pull requests welcome! This is a simple project for TV series nerds.

---

Made with ❤️ for binge-watchers everywhere
