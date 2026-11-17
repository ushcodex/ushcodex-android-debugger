# Contributing to USHCODEX Android Debugger

Thanks for your interest in contributing! 🧡💜

## How to contribute

1. **Fork** the repository and create your branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. **Set up** your environment:
   ```bash
   pip install -r requirements.txt
   python main.py   # smoke test
   ```
3. **Keep the code style**: PEP 8, module docstrings at the top of every file,
   private members prefixed with `_`, and the dark theme values from
   `uad/theme.py` (never hardcode colours).
4. **Commit** with clear messages (`feat:`, `fix:`, `docs:`, `refactor:`…).
5. **Open a Pull Request** describing what & why.

## Areas that especially need help

| Area | Notes |
|---|---|
| Cross-platform paths | `adb_manager.py` / `scrcpy_launcher.py` hardcode Windows paths — make them detect OS and use settings. |
| Clipboard fallbacks | `set_clipboard` relies on `clipper`; add Android 10+ `am broadcast` and OEM-safe fallbacks. |
| Gesture scripting | Extend `gesture_dialog.py` with saved-macro files + timeline editing. |
| Virtual display mode | Add a true multi-display dual-pane mode (`scrcpy --new-display`) as an alternative to DPI forcing. |
| Packaging | PyInstaller spec, winget/scoop manifests. |

## Reporting bugs

Open an issue with:
- UAD version, Python version, Windows version
- Device model + Android version
- Steps to reproduce + the "Mirror Output" log if relevant

## Code of Conduct

Be kind. Assume good faith. No spam, no harassment.

By contributing, you agree your contributions are licensed under the MIT License.
