"""
USHCODEX Android Debugger - Mirror & Controls
Embedded scrcpy screen (via MirrorHost) + collapsible control sidebar.
Every toggle shows its state and can be deactivated with a second click.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from pathlib import Path

from .theme import BRAND, FONTS
from .scrcpy_launcher import ScrcpyLauncher, GnirehtetSession
from .adb_manager import ADBManager
from .icons import IconSet
from .mirror_host import MirrorHost

COLS = 2          # sidebar button columns


class _ToolTip:
    def __init__(self, widget, text):
        self._w = widget
        self._t = text
        self._win = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        x = self._w.winfo_rootx() + 16
        y = self._w.winfo_rooty() + self._w.winfo_height() + 4
        self._win = tw = tk.Toplevel(self._w)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self._t, background=BRAND["ink"], foreground="#ffffff",
                 relief="flat", padx=8, pady=5,
                 font=FONTS["small"]).pack()

    def _hide(self, _=None):
        if self._win:
            self._win.destroy()
            self._win = None


class _Toggle(ttk.Button):
    """Two-state button that displays ON/OFF and restyles itself."""

    def __init__(self, parent, label_on, label_off, cmd, tip=""):
        self._on_txt, self._off_txt = label_on, label_off
        self._cmd = cmd
        self._state = None
        super().__init__(parent, text=label_off, style="TButton",
                         command=self._click)
        if tip:
            _ToolTip(self, tip)

    def _click(self):
        self._cmd(self._state is True)

    def set_state(self, on: bool, note: str = ""):
        self._state = on
        txt = self._on_txt if on else self._off_txt
        if note:
            txt += f"   ·   {note}"
        self.configure(text=txt,
                       style="ToggleOn.TButton" if on else "TButton")


class MirrorPanel(ttk.Frame):
    """Embedded mirror + all device controls in a collapsible sidebar."""

    def __init__(self, parent, launcher: ScrcpyLauncher,
                 adb: ADBManager, icons: IconSet, settings, log_fn):
        super().__init__(parent, style="TFrame")
        self._launcher = launcher
        self._adb = adb
        self._icons = icons
        self._settings = settings
        self._log = log_fn
        self._gnirehtet = GnirehtetSession()
        self._sidebar_open = True
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=0, minsize=0)

        # ── Top bar ───────────────────────────────────────────────────────────
        bar = ttk.Frame(self, style="Card.TFrame")
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        self._sidebar_btn = ttk.Button(bar, text="◀ Hide Panel", width=12,
                                       command=self._toggle_sidebar)
        self._sidebar_btn.pack(side="left", padx=8, pady=6)

        self._start_btn = ttk.Button(bar, text="▶  Start Mirror",
                                     style="Primary.TButton",
                                     command=self._mirror)
        self._start_btn.pack(side="left", padx=(8, 4), pady=6)

        ttk.Button(bar, text="⏹  Stop", style="Danger.TButton",
                   command=self._stop).pack(side="left", padx=2, pady=6)

        self._status_var = tk.StringVar(value="Idle")
        ttk.Label(bar, textvariable=self._status_var, style="Card.TLabel",
                  font=FONTS["small"], foreground=BRAND["muted"]
                  ).pack(side="right", padx=12)

        # ── Mirror host (embedded scrcpy) ─────────────────────────────────────
        self._host = MirrorHost(self, self._launcher, log_fn=self._log)
        self._host.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(8, 8))

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = ttk.Frame(self, style="Sidebar.TFrame")
        self._sidebar.grid(row=1, column=1, sticky="ns", padx=(8, 8), pady=(8, 8))
        self._build_sidebar()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        s = self._sidebar
        s.columnconfigure(0, weight=1)
        s.rowconfigure(0, weight=1)

        canvas = tk.Canvas(s, bg=BRAND["white"], highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(s, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Sidebar.TFrame", padding=10)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        def _wheel(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", _wheel, add="+")

        inner.columnconfigure((0, 1), weight=1, uniform="sb")
        r = 0

        def section(title):
            nonlocal r
            ttk.Separator(inner, orient="horizontal").grid(
                row=r, column=0, columnspan=2, sticky="ew", pady=(8, 4))
            r += 1
            head = ttk.Frame(inner, style="Sidebar.TFrame")
            head.grid(row=r, column=0, columnspan=2, sticky="w", pady=(0, 4))
            dot = tk.Canvas(head, width=7, height=7, bg=BRAND["white"],
                            highlightthickness=0)
            dot.create_oval(0, 0, 6, 6, fill=BRAND["orange"], outline="")
            dot.pack(side="left")
            ttk.Label(head, text=" " + title.upper(), style="PanelSub.TLabel",
                      font=FONTS["tiny"]).pack(side="left")
            r += 1

        def buttons(items):
            nonlocal r
            for i, (txt, cmd, tip, sty) in enumerate(items):
                b = ttk.Button(inner, text=txt, style=sty, command=cmd)
                b.grid(row=r + i // COLS, column=i % COLS, padx=2, pady=2,
                       sticky="ew")
                if tip:
                    _ToolTip(b, tip)
            r += -(-len(items) // COLS)

        def toggle(items):
            """items: list of (Toggle instance, )"""
            nonlocal r
            for t in items:
                t.grid(row=r, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
                r += 1

        # Navigation
        section("Navigation")
        buttons([
            ("◀  Back",      lambda: self._key(4),    "KEYCODE_BACK",  "TButton"),
            ("⌂  Home",      lambda: self._key(3),    "KEYCODE_HOME",  "TButton"),
            ("▭  Recents",   lambda: self._key(187),  "App switcher",  "TButton"),
            ("≡  Menu",      lambda: self._key(82),   "KEYCODE_MENU",  "TButton"),
        ])

        # Power & screen
        section("Power & Screen")
        buttons([
            ("⏻  Power",      lambda: self._key(26),  "Toggle power",    "TButton"),
            ("☀  Wake",       lambda: self._key(224), "Wake screen",     "TButton"),
            ("🌑  Screen Off", self._adb.screen_off,   "Turn display off","TButton"),
            ("📷  Screenshot", self._screenshot,       "Save screenshot", "TButton"),
        ])

        # Volume
        section("Volume")
        buttons([
            ("🔊  Vol +",   self._adb.volume_up,    "Volume up",    "TButton"),
            ("🔉  Vol −",   self._adb.volume_down,  "Volume down",  "TButton"),
            ("🔇  Mute",    self._adb.volume_mute,  "Toggle mute",  "TButton"),
        ])

        # Media
        section("Media")
        buttons([
            ("▶  Play",     lambda: self._key(126), "Media play",  "TButton"),
            ("⏸  Pause",    lambda: self._key(127), "Media pause", "TButton"),
            ("⏮  Prev",     lambda: self._key(88),  "Previous",    "TButton"),
            ("⏭  Next",     lambda: self._key(87),  "Next",        "TButton"),
            ("⏹  Stop",     lambda: self._key(86),  "Stop media",  "TButton"),
        ])

        # Orientation & display
        section("Orientation & Display")
        self._t_landscape = _Toggle(
            inner, "⟲  Force Landscape: ON", "⟲  Force Landscape: OFF",
            self._toggle_landscape,
            "Lock the device to landscape.\nNote: some OEM apps (e.g. Huawei Home)\n"
            "refuse rotation — use 'Rotate PC View' for those.")
        self._t_landscape.set_state(False)
        toggle([self._t_landscape])

        self._t_pc_rot = _Toggle(
            inner, "🖥  Rotate PC View: 90°", "🖥  Rotate PC View: OFF",
            self._toggle_pc_rotation,
            "Rotate the mirrored view on the PC.\nWorks even when the app itself\n"
            "forces portrait. Restarts the mirror.")
        self._t_pc_rot.set_state(False)
        toggle([self._t_pc_rot])

        self._t_ime = _Toggle(
            inner, "⌨  Suppress Keyboard: ON", "⌨  Suppress Keyboard: OFF",
            self._toggle_ime,
            "Stop the on-screen IME keyboard from\npopping up and covering the mirror.\n"
            "Applied on next mirror start.")
        self._t_ime.set_state(bool(self._settings.get("suppress_ime", True)))
        toggle([self._t_ime])

        self._t_tablet = _Toggle(
            inner, "⬛  Tablet Mode: ON", "⬛  Tablet Mode: OFF",
            self._toggle_tablet,
            "Force Desktop/Tablet dual-pane mode\nvia virtual display density (240 dpi).\n"
            "Second click restores your default DPI.")
        toggle([self._t_tablet])
        self.after(600, self._refresh_tablet_state)

        buttons([
            ("🔆  Bright +", lambda: self._key(221), "Brightness up",  "TButton"),
            ("🔅  Bright −", lambda: self._key(220), "Brightness down","TButton"),
        ])

        # Input & text
        section("Input & Text")
        buttons([
            ("📋  Clipboard →", self._push_clipboard, "PC clipboard → phone", "TButton"),
            ("⌨  Type Text",    self._paste_text,     "Type text on phone",   "TButton"),
            ("✕  Kill App",     self._kill_foreground,"Kill foreground app",  "Danger.TButton"),
        ])

        # Advanced
        section("Advanced")
        buttons([
            ("👆  Gesture Auto",  self._gesture_automation, "getevent / sendevent recorder & replayer", "TButton"),
            ("🔗  Port Forward",  self._port_forward_dialog,"adb forward / reverse rules",              "TButton"),
            ("📋  Logcat",        self._open_logcat,        "Live logcat viewer",                       "TButton"),
            ("📊  Density/DPI",   self._density_dialog,     "Read & set screen density / resolution",   "TButton"),
            ("🐛  Bug Report",    self._bug_report,         "Save full bugreport ZIP",                  "TButton"),
            ("📦  Install APK",   self._install_apk,        "Install an APK file",                      "TButton"),
            ("⬆  Push File",      self._push_file,          "Push file to /sdcard/Download",            "TButton"),
            ("🌐  Reverse Tether",self._gnirehtet_toggle,   "Share PC internet via USB (gnirehtet)",    "TButton"),
            ("↺  Reboot…",        self._reboot_dialog,      "Normal / bootloader / recovery / sideload","TButton"),
        ])

    def _toggle_sidebar(self):
        self._sidebar_open = not self._sidebar_open
        if self._sidebar_open:
            self._sidebar.grid(row=1, column=1, sticky="ns",
                               padx=(8, 8), pady=(8, 8))
            self._sidebar_btn.configure(text="◀ Hide Panel")
            self.columnconfigure(1, weight=0, minsize=0)
        else:
            self._sidebar.grid_forget()
            self._sidebar_btn.configure(text="▶ Show Panel")
        self._host._resize()

    # ── Status/log ────────────────────────────────────────────────────────────

    def _status(self, msg: str):
        self._status_var.set(msg)
        self._log(msg)

    # ── Key helper ────────────────────────────────────────────────────────────

    def _key(self, code: int):
        self._adb.run_async(lambda: self._adb.keyevent(code),
            error_cb=lambda e: self._status(f"keyevent error: {e}"))

    # ── Mirror actions ────────────────────────────────────────────────────────

    def _apply_pre_mirror(self):
        """ADB settings applied before each mirror start (IME suppression)."""
        if self._settings.get("suppress_ime", True):
            def _do():
                try:
                    self._adb.shell_raw(
                        "settings put secure show_ime_with_hard_keyboard 0")
                except Exception:
                    pass
            self._adb.run_async(_do)

    def _mirror(self):
        self._apply_pre_mirror()
        cfg = self._settings.scrcpy_cfg
        self._host.start(lambda title: self._build_embed_args(cfg, title))
        self._start_btn.configure(state="disabled")
        self.after(4000, lambda: self._start_btn.configure(state="normal"))

    def _build_embed_args(self, cfg: dict, title: str) -> list:
        args = self._launcher._base_args(cfg, self._adb.serial)
        args += ["--window-borderless", "--window-title", title]
        return args

    def _stop(self):
        self._host.stop()
        self._gnirehtet.stop()
        self._status("Stopped.")

    # ── Orientation toggles ───────────────────────────────────────────────────

    def _toggle_landscape(self, currently_on: bool):
        if currently_on:
            self._adb.run_async(lambda: self._adb.auto_rotation(True),
                callback=lambda _: self._t_landscape.set_state(
                    False, "auto-rotate restored"),
                error_cb=lambda e: self._status(f"Error: {e}"))
        else:
            def _do():
                self._adb.set_rotation(1)   # 1 = landscape
                return True
            self._adb.run_async(_do,
                callback=lambda _: self._t_landscape.set_state(
                    True, "rotate Home itself via PC View"),
                error_cb=lambda e: self._status(f"Error: {e}"))

    def _toggle_pc_rotation(self, currently_on: bool):
        if currently_on:
            self._settings.set("pc_rotation", 0)
            self._t_pc_rot.set_state(False, "view is 1:1")
        else:
            self._settings.set("pc_rotation", 90)
            self._t_pc_rot.set_state(True, "landscape view")
        self._settings.save()
        if self._host._launcher.running:
            self._mirror()   # quick restart with new orientation

    def _toggle_ime(self, currently_on: bool):
        new_state = not currently_on
        self._settings.set("suppress_ime", new_state)
        self._settings.save()
        self._t_ime.set_state(new_state,
            "applied on next mirror start" if new_state else "keyboard will pop up")

    def _toggle_tablet(self, currently_on: bool):
        def _do():
            if currently_on:
                self._adb.reset_density()
                return False
            self._adb.set_density(240)
            return True
        self._adb.run_async(_do,
            callback=lambda on: self._t_tablet.set_state(
                on, "dual-pane 240 dpi" if on else "default density restored"),
            error_cb=lambda e: self._status(f"Density error: {e}"))

    def _refresh_tablet_state(self):
        def _do():
            try:
                return self._adb.get_density()
            except Exception:
                return None
        self._adb.run_async(_do, callback=lambda d: (
            self._t_tablet.set_state(d == 240,
                "active — click to restore" if d == 240 else "not active")
            if d else None))

    # ── Input & text ──────────────────────────────────────────────────────────

    def _push_clipboard(self):
        try:
            text = self.winfo_toplevel().clipboard_get()
        except Exception:
            text = ""
        if not text:
            messagebox.showinfo("Clipboard", "PC clipboard is empty.")
            return
        self._adb.run_async(lambda: self._adb.set_clipboard(text),
            callback=lambda _: self._status("Clipboard pushed to phone."),
            error_cb=lambda e: self._status(f"Clipboard error: {e}"))

    def _paste_text(self):
        win = tk.Toplevel(self)
        win.title("Type on Phone")
        win.configure(bg=BRAND["paper"])
        win.resizable(True, False)
        ttk.Label(win, text="Enter text to type on phone:").pack(padx=10, pady=6)
        txt = ttk.Entry(win, width=50)
        txt.pack(padx=10, pady=4, fill="x")
        txt.focus()
        def _send(_e=None):
            t = txt.get()
            if t:
                self._adb.run_async(lambda: self._adb.text(t))
            win.destroy()
        ttk.Button(win, text="Send", style="Primary.TButton",
                   command=_send).pack(pady=6)
        win.bind("<Return>", _send)

    def _kill_foreground(self):
        def _do():
            raw = self._adb.shell_raw(
                "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
            m = re.search(r'([a-zA-Z][a-zA-Z0-9_.]+)/[a-zA-Z]', raw)
            if m:
                pkg = m.group(1)
                self._adb.force_stop(pkg)
                return f"Killed: {pkg}"
            return "Could not determine foreground app"
        self._adb.run_async(_do, callback=lambda r: self._status(r),
            error_cb=lambda e: self._status(f"Error: {e}"))

    # ── Misc actions ──────────────────────────────────────────────────────────

    def _screenshot(self):
        outdir = self._settings.get("screenshot_path", str(Path.home() / "Pictures"))
        from datetime import datetime
        fname = f"UAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(outdir, fname)
        def _do():
            self._adb.screenshot(path)
            return path
        self._adb.run_async(_do,
            callback=lambda p: self._status(f"Screenshot saved: {p}"),
            error_cb=lambda e: self._status(f"Screenshot error: {e}"))

    def _gnirehtet_toggle(self):
        if self._gnirehtet.running:
            self._gnirehtet.stop()
            self._status("Reverse tether stopped.")
        else:
            self._gnirehtet.start(self._adb.serial, on_output=self._log)
            self._status("Reverse tether started (PC internet → phone).")

    def _reboot_dialog(self):
        win = tk.Toplevel(self)
        win.title("Reboot Device")
        win.configure(bg=BRAND["paper"])
        ttk.Label(win, text="Select reboot mode:").pack(padx=20, pady=10)
        mode_var = tk.StringVar(value="Normal")
        for m in ["Normal", "Bootloader / Fastboot", "Recovery", "Sideload"]:
            ttk.Radiobutton(win, text=m, variable=mode_var, value=m).pack(
                anchor="w", padx=20)
        def _go():
            m = mode_var.get()
            mode_map = {"Normal": "", "Bootloader / Fastboot": "bootloader",
                        "Recovery": "recovery", "Sideload": "sideload"}
            self._adb.run_async(
                lambda: self._adb.reboot(mode_map[m]),
                callback=lambda _: self._status(f"Rebooting: {m}"))
            win.destroy()
        ttk.Button(win, text="Reboot", style="Danger.TButton",
                   command=_go).pack(pady=10)

    def _install_apk(self):
        path = filedialog.askopenfilename(
            filetypes=[("APK", "*.apk"), ("All", "*.*")],
            title="Select APK to Install")
        if not path:
            return
        self._adb.run_async(lambda: self._adb.install_apk(path),
            callback=lambda r: messagebox.showinfo("Install APK", r),
            error_cb=lambda e: messagebox.showerror("Install Error", str(e)))

    def _push_file(self):
        path = filedialog.askopenfilename(title="Select file to push to phone")
        if not path:
            return
        remote = f"/sdcard/Download/{os.path.basename(path)}"
        self._adb.run_async(lambda: self._adb.push(path, remote),
            callback=lambda _: self._status(f"Pushed to {remote}"),
            error_cb=lambda e: messagebox.showerror("Push Error", str(e)))

    # ── Advanced dialogs ──────────────────────────────────────────────────────

    def _gesture_automation(self):
        from .gesture_dialog import GestureDialog
        GestureDialog(self, self._adb)

    def _port_forward_dialog(self):
        from .port_forward_dialog import PortForwardDialog
        PortForwardDialog(self, self._adb)

    def _open_logcat(self):
        from .logcat_viewer import LogcatViewer
        LogcatViewer(self, self._adb)

    def _bug_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP", "*.zip"), ("All", "*.*")],
            title="Save Bug Report As")
        if not path:
            return
        self._adb.run_async(lambda: self._adb.bugreport(path),
            callback=lambda _: messagebox.showinfo("Bug Report", f"Saved: {path}"),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

    def _density_dialog(self):
        win = tk.Toplevel(self)
        win.title("Screen Density & Resolution")
        win.configure(bg=BRAND["paper"])
        win.geometry("380x280")

        density = tk.StringVar(value="…")
        res = tk.StringVar(value="…")
        dpi_var = tk.StringVar(value="420")

        def _refresh():
            def _do():
                try:
                    return self._adb.get_density(), self._adb.get_resolution()
                except Exception:
                    return None, None
            self._adb.run_async(_do, callback=lambda r: (
                density.set(str(r[0]) if r[0] else "?"),
                res.set(r[1] if r[1] else "?")))
        _refresh()

        ttk.Label(win, text="Current DPI:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        ttk.Label(win, textvariable=density).grid(row=0, column=1, sticky="w")
        ttk.Label(win, text="Resolution:").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        ttk.Label(win, textvariable=res).grid(row=1, column=1, sticky="w")

        ttk.Label(win, text="Set DPI:").grid(row=3, column=0, padx=10, pady=4, sticky="w")
        ttk.Entry(win, textvariable=dpi_var, width=8).grid(row=3, column=1, sticky="w")

        self._adb.run_async(lambda: self._adb.get_density(), callback=lambda d: (
            dpi_var.set(str(d)) if d else None))

        ttk.Button(win, text="Apply DPI", style="Primary.TButton",
                   command=lambda: self._adb.run_async(
                       lambda: self._adb.set_density(int(dpi_var.get())),
                       callback=lambda _: _refresh())
                   ).grid(row=4, column=0, padx=10, pady=4)
        ttk.Button(win, text="Reset to Default",
                   command=lambda: self._adb.run_async(
                       lambda: self._adb.reset_density(),
                       callback=lambda _: _refresh())
                   ).grid(row=4, column=1, padx=10, pady=4)
        ttk.Label(win, text="Tablet Mode (sidebar) is a one-click shortcut to 240 dpi.",
                  style="Sub.TLabel", font=FONTS["small"]).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=10, pady=6)
