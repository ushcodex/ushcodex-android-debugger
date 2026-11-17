#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
 USHCODEX Android Debugger (UAD)
 A powerful, open-source Android device control and debugging suite.

 Mirrors, controls and debugs Android devices from your PC using ADB + scrcpy.

 Entry point:  python main.py        (or launch UAD.exe shortcut)
═══════════════════════════════════════════════════════════════════════════════
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Per-monitor DPI awareness BEFORE Tk starts (fixes Win32 child-window scaling)
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uad import __version__ as APP_VERSION
from uad.theme import apply_theme, BRAND, FONTS
from uad.settings import Settings
from uad.adb_manager import ADBManager
import uad.adb_manager as adb_mod
import uad.scrcpy_launcher as launch_mod
from uad.device_panel import DevicePanel
from uad.mirror_panel import MirrorPanel
from uad.file_manager import FileManagerTab
from uad.terminal import TerminalTab
from uad.icons import IconSet

APP_NAME  = "USHCODEX Android Debugger"
REPO_URL  = "https://github.com/ushcodex/ushcodex-android-debugger"
ASSETS    = ROOT / "assets"

try:
    from PIL import Image, ImageTk
    _PIL = True
except ImportError:
    _PIL = False


class UADApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(960, 620)
        self.configure(bg=BRAND["paper"])

        # ── Settings & backend objects ────────────────────────────────────────
        self.settings = Settings()
        self._apply_paths_from_settings()

        self.adb      = ADBManager()
        self.launcher = launch_mod.ScrcpyLauncher()
        self.icons    = IconSet()
        self.icons.preload(18)

        # Window icon
        self._set_window_icon()

        # ── Layout ────────────────────────────────────────────────────────────
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_sidebar()
        self._build_tabs()
        self._build_statusbar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Debug/testing hook: UAD_AUTOSTART=1 starts the mirror automatically
        if os.environ.get("UAD_AUTOSTART") == "1":
            self.after(1200, self.mirror_panel._mirror)

    # ── Paths ─────────────────────────────────────────────────────────────────

    def _apply_paths_from_settings(self):
        """Sync module-level ADB / scrcpy paths with saved settings."""
        adb_path = self.settings.get("adb_path")
        if adb_path and Path(adb_path).exists():
            adb_mod.ADB_PATH = adb_path
        scrcpy = self.settings.get("scrcpy_path")
        if scrcpy and Path(scrcpy).exists():
            launch_mod.SCRCPY_PATH = scrcpy

    def _set_window_icon(self):
        ico = ASSETS / "icons" / "uad.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except tk.TclError:
                pass
        elif _PIL and (ASSETS / "icons" / "uad_512.png").exists():
            img = ImageTk.PhotoImage(Image.open(ASSETS / "icons" / "uad_512.png"))
            self.iconphoto(True, img)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        header = ttk.Frame(self, style="Panel.TFrame", height=64)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)

        banner = ASSETS / "banner.png"
        if _PIL and banner.exists():
            img = Image.open(banner).convert("RGBA")
            ratio = 48 / img.height
            img = img.resize((int(img.width * ratio), 48), Image.LANCZOS)
            self._banner_img = ImageTk.PhotoImage(img)
            tk.Label(header, image=self._banner_img, bg=BRAND["bg2"]
                     ).pack(side="left", padx=10, pady=8)
        else:
            ttk.Label(header, text="USHCODEX", style="Panel.TLabel",
                      font=FONTS["h1"]).pack(side="left", padx=12)

        ttk.Label(header, text="Android Debugger",
                  style="Panel.TLabel", font=FONTS["h3"],
                  foreground=BRAND["accent"]).pack(side="left", padx=(0, 8))

        ver = ttk.Label(header, text=f"v{APP_VERSION}", style="Panel.TLabel",
                        font=FONTS["small"], foreground=BRAND["fg2"])
        ver.pack(side="right", padx=12)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = DevicePanel(
            self, self.adb, self.icons,
            on_device_selected=self._on_device_selected,
            settings=self.settings)
        self.sidebar.grid(row=1, column=0, sticky="ns", padx=(0, 2))

    def _on_device_selected(self, device: dict):
        self.status(f"Selected: {device['model']} ({device['serial']})")

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _build_tabs(self):
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(2, 4))
        self._nb = nb

        # 1. Mirror & Controls
        self.mirror_panel = MirrorPanel(
            nb, self.launcher, self.adb, self.icons,
            self.settings, log_fn=self.status)
        nb.add(self.mirror_panel, text="  🖥 Mirror & Controls  ")

        # 2. Files
        self.files_tab = FileManagerTab(nb, self.adb)
        nb.add(self.files_tab, text="  📁 Files  ")

        # 3. ADB Shell
        self.terminal_tab = TerminalTab(nb, self.adb)
        nb.add(self.terminal_tab, text="  ⌨ ADB Shell  ")

        # 4. Settings
        self.settings_tab = self._build_settings_tab(nb)
        nb.add(self.settings_tab, text="  ⚙ Settings  ")

        # 5. About
        self.about_tab = self._build_about_tab(nb)
        nb.add(self.about_tab, text="  ℹ About  ")

    # ── Settings tab ──────────────────────────────────────────────────────────

    def _build_settings_tab(self, parent):
        tab = ttk.Frame(parent)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        canvas = tk.Canvas(tab, bg=BRAND["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Card.TFrame")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        inner.columnconfigure(1, weight=1)
        row = 0

        ttk.Label(inner, text="Paths", style="Title.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 4))
        row += 1

        path_rows = [
            ("adb_path",     "ADB executable path"),
            ("scrcpy_path",  "scrcpy executable path"),
            ("record_path",  "Recording save folder"),
            ("screenshot_path", "Screenshot save folder"),
        ]
        self._path_vars = {}
        for key, label in path_rows:
            ttk.Label(inner, text=label).grid(row=row, column=0,
                                              sticky="w", padx=16, pady=3)
            var = tk.StringVar(value=self.settings.get(key, ""))
            self._path_vars[key] = var
            ttk.Entry(inner, textvariable=var, width=60
                      ).grid(row=row, column=1, sticky="ew", padx=12, pady=3)
            row += 1

        ttk.Label(inner, text="Video", style="Title.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))
        row += 1

        self._opt_vars = {}
        options = [
            ("codec",       "Video codec",  ["H.264", "H.265", "AV1"], False),
            ("audio_codec", "Audio codec",  ["opus", "aac", "flac"],   False),
            ("mouse_mode",  "Mouse mode",   list(launch_mod.ScrcpyLauncher.MOUSE_MODES), False),
            ("lock_orientation", "Lock orientation",
             ["Auto", "Portrait", "Landscape", "Rev. Portrait", "Rev. Landscape"], False),
            ("fps",         "Max FPS",      ["30", "60", "120"], True),
            ("resolution",  "Max resolution (0=native)",
             ["0", "720", "1080", "1440", "1920"], True),
            ("bitrate",     "Bitrate",      ["4M", "8M", "12M", "16M", "20M"], True),
        ]
        for key, label, values, is_text in options:
            ttk.Label(inner, text=label).grid(row=row, column=0,
                                              sticky="w", padx=16, pady=3)
            var = tk.StringVar(value=str(self.settings.get(key, values[0])))
            self._opt_vars[key] = (var, values, is_text)
            cb = ttk.Combobox(inner, textvariable=var, values=values,
                              width=22)
            if not is_text:
                cb.state(["readonly"])
            cb.grid(row=row, column=1, sticky="w", padx=12, pady=3)
            row += 1

        ttk.Label(inner, text="Behaviour", style="Title.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))
        row += 1

        self._bool_vars = {}
        bools = [
            ("audio",              "Forward audio"),
            ("stay_awake",         "Keep device awake while mirroring"),
            ("borderless",         "Borderless scrcpy window"),
            ("always_on_top",      "Always on top"),
            ("fullscreen",         "Start fullscreen"),
            ("show_touches",       "Show touches on device"),
            ("disable_screensaver","Disable screensaver while mirroring"),
            ("clipboard_autosync", "Clipboard autosync"),
            ("power_off_on_close", "Power off device screen on close"),
        ]
        for key, label in bools:
            var = tk.BooleanVar(value=bool(self.settings.get(key, False)))
            self._bool_vars[key] = var
            ttk.Checkbutton(inner, text=label, variable=var,
                            style="TCheckbutton").grid(
                row=row, column=0, columnspan=2, sticky="w", padx=16, pady=2)
            row += 1

        btns = ttk.Frame(inner, style="Card.TFrame")
        btns.grid(row=row, column=0, columnspan=2, sticky="ew",
                  padx=16, pady=14)
        ttk.Button(btns, text="💾 Save Settings", style="Primary.TButton",
                   command=self._save_settings).pack(side="left", padx=4)
        ttk.Button(btns, text="↺ Reset to Defaults",
                   command=self._reset_settings).pack(side="left", padx=4)
        return tab

    def _save_settings(self):
        mapping = {k: v.get() for k, v in self._path_vars.items()}
        mapping.update({k: v[0].get() for k, v in self._opt_vars.items()})
        for key, var in self._opt_vars.items():
            _, values, is_text = var
            if not is_text:
                mapping[key] = var[0].get()
        mapping.update({k: v.get() for k, v in self._bool_vars.items()})
        # fps / resolution numerics
        for numkey in ("fps", "resolution"):
            try:
                mapping[numkey] = int(mapping[numkey])
            except (TypeError, ValueError):
                pass
        self.settings.update(mapping)
        self.settings.save()
        self._apply_paths_from_settings()
        self.status("Settings saved.")
        messagebox.showinfo(APP_NAME, "Settings saved.")

    def _reset_settings(self):
        self.settings.reset_to_defaults()
        messagebox.showinfo(APP_NAME, "Settings reset. Restart UAD to fully apply.")
        self.status("Settings reset to defaults.")

    # ── About tab ─────────────────────────────────────────────────────────────

    def _build_about_tab(self, parent):
        tab = ttk.Frame(parent)
        tab.columnconfigure(0, weight=1)

        card = ttk.Frame(tab, style="Card.TFrame")
        card.grid(row=0, column=0, sticky="ew", padx=24, pady=24)
        card.columnconfigure(0, weight=1)

        banner = ASSETS / "banner.png"
        if _PIL and banner.exists():
            img = Image.open(banner).convert("RGBA")
            ratio = 96 / img.height
            img = img.resize((int(img.width * ratio), 96), Image.LANCZOS)
            self._about_img = ImageTk.PhotoImage(img)
            tk.Label(card, image=self._about_img, bg=BRAND["bg3"]).grid(
                row=0, column=0, pady=(20, 8))

        ttk.Label(card, text=f"{APP_NAME}  v{APP_VERSION}",
                  style="Card.TLabel", font=FONTS["h1"]).grid(row=1, column=0)
        ttk.Label(card, text="A powerful, open-source Android device "
                             "control and debugging suite.\nMirroring, "
                             "input control, file management, gesture "
                             "automation and more — powered by ADB & scrcpy.",
                  style="Card.TLabel", justify="center").grid(row=2, column=0,
                                                              pady=10)
        ttk.Label(card, text="© Ushcodex Technologies · MIT License",
                  style="Card.TLabel", font=FONTS["small"],
                  foreground=BRAND["fg2"]).grid(row=3, column=0)

        ttk.Button(card, text=f"🌐  {REPO_URL}", style="TButton",
                   command=lambda: self._open_url(REPO_URL)).grid(
            row=4, column=0, pady=(10, 6))
        ttk.Button(card, text="🐛  Report an Issue", style="TButton",
                   command=lambda: self._open_url(REPO_URL + "/issues")).grid(
            row=5, column=0, pady=4)
        ttk.Button(card, text="★  Star on GitHub", style="TButton",
                   command=lambda: self._open_url(REPO_URL + "/stargazers")).grid(
            row=6, column=0, pady=(4, 20))

        credits = (
            "Built with:  Python · Tkinter · ADB (Google) · scrcpy (Genymobile)\n"
            "scrcpy is used as an external binary under Apache-2.0 — not bundled "
            "in this repo; UAD will use the path configured in Settings."
        )
        ttk.Label(card, text=credits, style="Card.TLabel",
                  font=FONTS["small"], justify="center",
                  foreground=BRAND["fg2"]).grid(row=7, column=0,
                                                pady=(0, 20))
        return tab

    @staticmethod
    def _open_url(url: str):
        import webbrowser
        webbrowser.open(url)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = ttk.Frame(self, style="Panel.TFrame", height=26)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        self._status_var = tk.StringVar(value="Ready.")
        ttk.Label(bar, textvariable=self._status_var, style="Panel.TLabel",
                  font=FONTS["small"]).pack(side="left", padx=10)
        ttk.Label(bar, text=f"UAD v{APP_VERSION}", style="Panel.TLabel",
                  font=FONTS["small"], foreground=BRAND["fg2"]
                  ).pack(side="right", padx=10)

    def status(self, msg: str):
        self._status_var.set(msg)

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def _on_close(self):
        if self.launcher.running:
            if not messagebox.askyesno(
                    APP_NAME, "A mirror session is running.\nStop it and quit?"):
                return
        self.launcher.stop()
        self.settings.save()
        self.destroy()


def main():
    app = UADApp()
    apply_theme(app)
    app.mainloop()


if __name__ == "__main__":
    main()
