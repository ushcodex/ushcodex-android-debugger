"""
USHCODEX Android Debugger - Settings Manager
Loads / saves user preferences to a JSON config file.
"""
import json
import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".ushcodex" / "uad"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS = {
    # Scrcpy - Video
    "codec":               "H.264",
    "bitrate":             "8M",
    "fps":                 60,
    "resolution":          "0",          # 0 = native
    "lock_orientation":    "Auto",
    "rotation":            None,

    # Scrcpy - Audio
    "audio":               True,
    "audio_codec":         "opus",

    # Scrcpy - Mouse / Input
    "mouse_mode":          "UHID (true mouse)",
    "keyboard_mode":       "uhid",
    "gamepad":             False,

    # Scrcpy - Window
    "borderless":          False,
    "always_on_top":       False,
    "fullscreen":          False,
    "window_x":            None,
    "window_y":            None,
    "window_w":            None,
    "window_h":            None,

    # Scrcpy - Behaviour
    "stay_awake":          True,
    "show_touches":        False,
    "disable_screensaver": False,
    "clipboard_autosync":  True,
    "power_off_on_close":  False,
    "suppress_ime":        True,     # stop the on-screen keyboard covering the mirror
    "pc_rotation":         0,        # 0 / 90 / 180 / 270 — PC-side view rotation

    # ADB
    "adb_path":            r"C:\Users\PC\Projects\Scrcpy\adb.exe",
    "scrcpy_path":         r"C:\Users\PC\Projects\Scrcpy\scrcpy.exe",

    # UAD UI
    "theme":               "dark",
    "log_level":           "INFO",
    "last_device":         None,
    "record_path":         str(Path.home() / "Videos"),
    "screenshot_path":     str(Path.home() / "Pictures"),
}


class Settings:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._data: dict = {**DEFAULTS}
        self.load()

    def load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except Exception:
                pass   # corrupt file → use defaults

    def save(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"[Settings] Save failed: {e}")

    def get(self, key: str, default=None):
        return self._data.get(key, default if default is not None else DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def update(self, mapping: dict) -> None:
        self._data.update(mapping)

    def as_dict(self) -> dict:
        return dict(self._data)

    def reset_to_defaults(self) -> None:
        self._data = {**DEFAULTS}
        self.save()

    # Convenience properties for Scrcpy cfg dict
    @property
    def scrcpy_cfg(self) -> dict:
        keys = [
            "codec", "bitrate", "fps", "resolution", "lock_orientation",
            "rotation", "audio", "audio_codec", "mouse_mode", "keyboard_mode",
            "gamepad", "borderless", "always_on_top", "fullscreen",
            "window_x", "window_y", "window_w", "window_h",
            "stay_awake", "show_touches", "disable_screensaver",
            "clipboard_autosync", "power_off_on_close", "pc_rotation",
        ]
        return {k: self._data.get(k, DEFAULTS.get(k)) for k in keys}
