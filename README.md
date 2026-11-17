<div align="center">

<img src="assets/banner.png" alt="USHCODEX Android Debugger" width="640"/>

# 🤖 USHCODEX Android Debugger (UAD)

**A powerful, open-source Android device control and debugging suite.**

Mirrors, controls and debugs Android devices from your PC — the scrcpy screen is **embedded right inside the app** with a collapsible control sidebar.
Native Tkinter GUI (no Electron), warm light theme matching [ushcodex.tech](https://ushcodex.tech), powered by **ADB** and **scrcpy**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![scrcpy](https://img.shields.io/badge/powered_by-scrcpy-orange)

</div>

---

## ✨ Features

### 🖥 Embedded Mirror + Collapsible Sidebar
The scrcpy screen is **embedded inside the app** — not a floating window. All controls live in a
**collapsible sidebar** beside it: out of the way of the screen, one click away.

| Mode | Description |
|---|---|
| **Mirror Screen** | Full screen mirroring, embedded in the UAD window |
| **Mirror (Screen Off)** | Mirror while the phone display stays off |
| **OTG Mode** | Use your PC keyboard/mouse as a USB HID device — even on locked screens |
| **Camera Source** | Mirror the phone camera instead of the display |
| **Record Screen / Audio / Camera** | Record to MP4 / MKV / Opus files |
| **Reverse Tether** | Share your PC's internet to the phone via USB (gnirehtet) |

Full control over **codec (H.264/H.265/AV1), bitrate, FPS, resolution, audio codec, mouse mode (SDK/UHID/AOAM), orientation, window geometry**, and more — all from the Settings tab, no CLI flags required.

### 🎛 Stateful Controls (everything can be deactivated)
- **⬛ Tablet Mode** — force dual-pane layout via virtual density (240 dpi); click again to restore your default DPI
- **⟲ Force Landscape** — locks the device orientation; click again to restore auto-rotate
- **🖥 Rotate PC View** — rotates the mirrored view on the PC side, bypassing app orientation locks (Huawei Home, the Phone app, etc.)
- **⌨ Suppress Keyboard** — stops the on-screen IME from popping up and covering the mirror
- **👆 Gesture Automation** — record raw `getevent` streams and replay via `sendevent`
- **🔗 Port Forward / Reverse**, **📋 Logcat**, **🐛 Bug Report**, **📊 Density/DPI** (with explicit Reset), **🚫 PowerGenie killer**

### 📁 Files & Shell
- **File manager** — browse the device filesystem, push/pull, rename, delete, mkdir.
- **ADB Shell** — interactive terminal with command history inside the app.

### 📶 Connectivity
- USB devices auto-detected and refreshed every 3 s
- **Wi-Fi ADB** — one-click `tcpip 5555` enable + connect
- **Wireless debugging pairing** (Android 11+ pair-port + code flow)

---

## 📦 Installation

### Requirements
- Windows 10/11 (the app is Windows-first; the Python core is cross-platform)
- Python **3.9+** with Tkinter (bundled with standard CPython)
- ADB and scrcpy (any recent build) — paths configured in-app, defaults to `C:\...\Scrcpy\adb.exe` / `scrcpy.exe`

### Run from source
```bash
git clone https://github.com/ushcodex/ushcodex-android-debugger.git
cd ushcodex-android-debugger
pip install -r requirements.txt
python main.py
```

### On your Android device
Enable **Developer options → USB debugging**, plug in, accept the prompt. UAD auto-detects the device.

---

## 🏗 Project Structure

```
ushcodex-android-debugger/
├── main.py                  # App entry point
├── uad/
│   ├── adb_manager.py       # Thread-safe ADB wrapper (all operations)
│   ├── device_panel.py      # Device list, WiFi connect, device info
│   ├── mirror_panel.py      # Embedded mirror + collapsible control sidebar
│   ├── mirror_host.py       # Embeds the scrcpy window (Win32 SetParent)
│   ├── scrcpy_launcher.py   # Builds scrcpy/gnirehtet subprocesses
│   ├── gesture_dialog.py    # getevent recorder / sendevent replayer
│   ├── file_manager.py      # Device file browser
│   ├── terminal.py          # Interactive ADB shell
│   ├── logcat_viewer.py     # Live logcat with filters
│   ├── port_forward_dialog.py # forward/reverse rule manager
│   ├── settings.py          # JSON-persisted preferences
│   ├── theme.py             # USHCODEX brand colours & Tk theming
│   └── icons.py             # Procedural icon set (Pillow)
└── assets/                  # Logo, icon, brand generator
```

---

## 🤝 Contributing

Contributions are very welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

Good first issues:
- Linux/macOS path handling (the ADB/scrcpy wrappers are currently Windows-oriented)
- Battery/broadcast-based clipboard fallbacks for OEMs that block `clipper`
- Batch gesture scripting UI for `gesture_dialog.py`
- Translations (i18n)

## 🔒 Security Notes
- `adb` runs with your user privileges; nothing in UAD asks for root, but some advanced toggles (`pm disable-user`, `wm density`) can affect device behaviour. Use thoughtfully.
- UAD never phones home. Everything is local.

## 📄 License

MIT — see [LICENSE](LICENSE.md).
scrcpy and ADB are external tools by [Genymobile](https://github.com/Genymobile/scrcpy) and Google respectively, governed by their own licenses; UAD launches them as separate processes and does not redistribute them.

<div align="center">

**Made with 🧡 + 💜 by [Ushcodex Technologies](https://ushcodex.tech)**

</div>
