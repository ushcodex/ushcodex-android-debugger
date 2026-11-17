<div align="center">

<img src="assets/banner.png" alt="USHCODEX Android Debugger" width="640"/>

# 🤖 USHCODEX Android Debugger (UAD)

**A powerful, open-source Android device control and debugging suite.**

Mirror, control, and debug your Android device from your PC — with every control at the click of a button.
Native Tkinter GUI (no Electron), powered by **ADB** and **scrcpy**.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![scrcpy](https://img.shields.io/badge/powered_by-scrcpy-orange)

</div>

---

## ✨ Features

### 🖥 Mirror & Launch
| Mode | Description |
|---|---|
| **Mirror Screen** | Full screen mirroring on your PC (scrcpy) |
| **Mirror (Screen Off)** | Mirror while the phone display stays off |
| **OTG Mode** | Use your PC keyboard/mouse as a USB HID device — even on locked screens |
| **Camera Source** | Mirror the phone camera instead of the display |
| **Record Screen / Audio / Camera** | Record to MP4 / MKV / Opus files |
| **Reverse Tether** | Share your PC's internet to the phone via USB (gnirehtet) |

Full control over **codec (H.264/H.265/AV1), bitrate, FPS, resolution, audio codec, mouse mode (SDK/UHID/AOAM), orientation, window geometry**, and more — all from the Settings tab, no CLI flags required.

### 🎛 Quick Device Controls
Every input control at your fingertips: **Back, Home, Recents, Menu, Power/Lock, Volume ±/Mute, Screen On/Off, Rotation lock (portrait/landscape), Brightness ±, Notification bar, Quick Settings, Media transport (Play/Pause/Prev/Next/Stop), Clipboard push, Type-on-phone, Kill foreground app, Screenshot, Reboot (normal/bootloader/recovery/sideload), Install APK, Push file**.

### 🚀 Advanced Features
- **⬛ Desktop / Tablet Dual-Pane Mode** — force dual-pane tablet layout via a virtual display density (`wm density 240`), with automatic detection and one-click reset.
- **👆 Hardware-Level Gesture Automation** — record raw `getevent` streams from any `/dev/input` device and replay them with `sendevent`, plus tap/swipe macro builder. Works even when Android's `input` injection fails.
- **🔗 Port Forward / Reverse tunneling** — full `adb forward` / `adb reverse` rule manager.
- **📋 Logcat Viewer** — real-time streamed logcat with level filter (V→E), text filter, case sensitivity, and export.
- **🐛 Bug Report** — capture a full device bugreport ZIP.
- **📊 Device Density/Resolution** — read & override `wm density` / `wm size` live.
- **🚫 PowerGenie killer** — one-click disable of Huawei's aggressive background app manager.

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
│   ├── mirror_panel.py      # All scrcpy launch modes + quick controls
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
