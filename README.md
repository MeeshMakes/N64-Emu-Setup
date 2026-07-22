# 🎮 N64 Emu Setup

**One-click N64 emulator installer & launcher** — gets you playing
*The Legend of Zelda: Ocarina of Time* and *Super Smash Bros.* (N64)
as fast as possible.

![App Screenshot](screenshot.png)

## What It Does

- ✅ **Downloads & installs** the [Simple64](https://github.com/simple64/simple64) emulator
  (the gold-standard Mupen64Plus-based N64 emulator)
- ✅ **Creates ROM folders** for your games
- ✅ **Live console log** shows every step
- ✅ **Launch games** directly from the app
- ✅ **Cross-platform** — Windows, macOS, Linux

## 🚀 One-Click Install (Windows)

**Open CMD and paste this single line:**

```cmd
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/MeeshMakes/N64-Emu-Setup/master/setup_windows.ps1' -OutFile '%TEMP%\n64_setup.ps1'; Powershell -ExecutionPolicy Bypass -File '%TEMP%\n64_setup.ps1'}"
```

That's it. This one command:
1. ✅ **Checks/installs Python** automatically
2. ✅ **Downloads** the full app
3. ✅ **Generates a custom N64 desktop icon** 🎨
4. ✅ **Creates a desktop shortcut** with the icon
5. ✅ **Launches the app** for you

## Manual Setup

### 1. Install Python 3.8+

[Download Python](https://www.python.org/downloads/) — make sure to check
**"Add Python to PATH"** during installation.

### 2. Run the app

```bash
cd N64-Emu-Setup
python n64_emu_setup.py
```

### 3. Click "Install Emulator"

The app will automatically download the latest Simple64 release and
set everything up.

### 4. Add your ROMs

Place your legally obtained N64 ROM files in the `roms/` folder:

```
roms/
├── n64/
│   ├── zelda_ocarina_of_time/   ← Zelda: Ocarina of Time
│   └── super_smash_bros/        ← Super Smash Bros.
└── other/                       ← Any other N64 games
```

Supported formats: `.z64`, `.n64`, `.v64`, `.rom`

### 5. Play!

Use **"Select ROM"** to pick a game and launch it, or open the ROMs
folder and drag a ROM onto the emulator.

## Obtaining ROMs — The Legal Way

To play these games, you need a **ROM file** of the original game.
Here are the legitimate ways to get one:

### Option A: Dump Your Own Cartridge (Recommended)

If you own the original N64 cartridge, you can dump it legally:

1. **EverDrive flash cart** — Insert your cartridge into a
   [Krikzz EverDrive](https://krikzz.com/), then copy the ROM off the SD card.
2. **Retrode** — A USB device that reads original cartridges.
3. **Game Backup devices** — Devices like the *Doctor V64* or *Mr. Backup Z64*
   can dump cartridges.

### Option B: Virtual Console

Nintendo has released these games on the **Wii U Virtual Console**.
If you buy them there, you can extract the ROM from your console
(homebrew required — research this yourself).

### Option C: iQue Player (Zelda OoT)

In China, *Ocarina of Time* was released digitally on the
**iQue Player**. The ROM can be extracted from a purchased iQue unit.

### What NOT to do

Downloading ROMs from random websites is **copyright infringement**
and often comes with malware risks. Always create your own backup
from a game you own.

## Buttons Reference

| Button | What it does |
|--------|-------------|
| ⬇ **Install Emulator** | Downloads + installs Simple64 |
| ▶ **Launch Emulator** | Opens the emulator directly |
| 📁 **Select ROM** | Pick a ROM file to play |
| 📂 **ROMs Folder** | Opens the ROMs folder |
| 🧹 **Clear Log** | Clears the console output |

## Manual Installation

If the auto-installer has trouble, you can install Simple64 yourself:

1. Go to [Simple64 Releases](https://github.com/simple64/simple64/releases)
2. Download the file for your OS
3. Extract it into the `emulator/simple64/` folder
4. Restart the app — it will detect the installation automatically

## Troubleshooting

**"GitHub API rate limited"**
GitHub allows 60 anonymous API requests/hour. Wait a bit, or download
the emulator manually (see above).

**App doesn't open on macOS**
Run `chmod +x n64_emu_setup.py && python3 n64_emu_setup.py`

**Emulator won't launch**
Make sure you've installed it first. Check the `emulator/simple64/`
folder for the executable.

## License

MIT — do whatever you want with this tool.
Game ROMs are not included and must be obtained legally by you.
