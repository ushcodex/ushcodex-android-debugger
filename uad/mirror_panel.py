"""
USHCODEX Android Debugger - Mirror & Launch Panel
All scrcpy launch modes with quick-action buttons.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
from pathlib import Path

from .theme import BRAND, FONTS
from .scrcpy_launcher import ScrcpyLauncher, GnirehtetSession
from .adb_manager import ADBManager, ADBError
from .icons import IconSet


def _btn(parent, text, cmd, style="TButton", tip=""):
    b = ttk.Button(parent, text=text, style=style, command=cmd)
    if tip:
        _ToolTip(b, tip)
    return b


class _ToolTip:
    def __init__(self, widget, text):
        self._w = widget
        self._t = text
        self._win = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _=None):
        x = self._w.winfo_rootx() + 20
        y = self._w.winfo_rooty() + self._w.winfo_height() + 4
        self._win = tw = tk.Toplevel(self._w)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self._t, background=BRAND["bg2"], foreground=BRAND["fg"],
                 relief="flat", padx=6, pady=4,
                 font=FONTS["small"]).pack()

    def _hide(self, _=None):
        if self._win:
            self._win.destroy()
            self._win = None


class MirrorPanel(ttk.Frame):
    """Main mirror/launch panel with ALL scrcpy launch modes."""

    def __init__(self, parent, launcher: ScrcpyLauncher,
                 adb: ADBManager, icons: IconSet, settings, log_fn):
        super().__init__(parent, style="TFrame")
        self._launcher = launcher
        self._adb = adb
        self._icons = icons
        self._settings = settings
        self._log = log_fn
        self._gnirehtet = GnirehtetSession()
        self._build()

    # ── Status bar helper ─────────────────────────────────────────────────────

    def _status(self, msg: str):
        self._status_var.set(msg)
        self._log(msg)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        row = 0

        # ── Status bar ────────────────────────────────────────────────────────
        status_bar = ttk.Frame(self, style="Panel.TFrame")
        status_bar.grid(row=row, column=0, sticky="ew", padx=0, pady=0)
        self._status_var = tk.StringVar(value="Idle")
        ttk.Label(status_bar, textvariable=self._status_var, style="Panel.TLabel",
                  font=FONTS["small"]).pack(side="left", padx=10)
        self._stop_btn = ttk.Button(status_bar, text="⏹ Stop Mirror",
                                    style="Danger.TButton",
                                    command=self._stop)
        self._stop_btn.pack(side="right", padx=6, pady=3)
        row += 1

        # ── Mirror modes ──────────────────────────────────────────────────────
        modes = ttk.LabelFrame(self, text=" Mirror Modes ", style="TLabelframe")
        modes.grid(row=row, column=0, sticky="ew", padx=10, pady=(8, 4))
        modes.columnconfigure((0,1,2), weight=1)
        row += 1

        mode_btns = [
            ("📺  Mirror Screen",         "Primary.TButton", self._mirror,
             "Start screen mirroring on PC"),
            ("🌑  Mirror (Screen Off)",   "Accent.TButton",  self._mirror_off,
             "Mirror but keep phone screen off"),
            ("🖱  OTG Mode",              "TButton",         self._otg,
             "Use PC as USB HID (keyboard/mouse)"),
            ("📹  Camera Source",          "TButton",         self._camera,
             "Mirror phone camera to PC"),
            ("⏺  Record Screen",          "Danger.TButton",  self._record,
             "Record screen to file on PC"),
            ("🎵  Record Audio Only",     "TButton",         self._record_audio,
             "Record phone audio to file"),
            ("🎬  Record Camera",         "TButton",         self._record_camera,
             "Record from phone camera"),
            ("🌐  Reverse Tether",        "Success.TButton", self._gnirehtet_toggle,
             "Share PC internet to phone via USB (Gnirehtet)"),
        ]
        for i, (txt, sty, cmd, tip) in enumerate(mode_btns):
            b = ttk.Button(modes, text=txt, style=sty, command=cmd)
            b.grid(row=i//3, column=i%3, padx=4, pady=4, sticky="ew")
            _ToolTip(b, tip)

        # ── Quick Controls ────────────────────────────────────────────────────
        ctrl = ttk.LabelFrame(self, text=" Quick Device Controls ", style="TLabelframe")
        ctrl.grid(row=row, column=0, sticky="ew", padx=10, pady=4)
        ctrl.columnconfigure(tuple(range(6)), weight=1)
        row += 1

        quick = [
            # (text, cmd, tooltip, style)
            ("◀ Back",        lambda: self._key(4),   "KEYCODE_BACK",  "TButton"),
            ("⌂ Home",        lambda: self._key(3),   "KEYCODE_HOME",  "TButton"),
            ("▭ Recents",     lambda: self._key(187), "App Switcher",  "TButton"),
            ("≡ Menu",        lambda: self._key(82),  "KEYCODE_MENU",  "TButton"),
            ("⏻ Power",       lambda: self._key(26),  "Toggle power",  "TButton"),
            ("📷 Screenshot",  self._screenshot,       "Take screenshot","TButton"),

            ("🔊 Vol+",        self._adb.volume_up,   "Volume Up",     "TButton"),
            ("🔉 Vol-",        self._adb.volume_down, "Volume Down",   "TButton"),
            ("🔇 Mute",        self._adb.volume_mute, "Mute",          "TButton"),
            ("☀ Screen On",   lambda: self._key(224), "Wake screen",   "TButton"),
            ("◑ Screen Off",  self._adb.screen_off,  "Screen off",    "TButton"),
            ("🔒 Lock",        lambda: self._key(26),  "Power/lock",    "TButton"),

            ("↻ Rotate ▶",    lambda: self._rotate(1),"Landscape",     "TButton"),
            ("↻ Rotate ▲",    lambda: self._rotate(0),"Portrait",      "TButton"),
            ("🔆 Bright+",    lambda: self._key(221), "Brightness up", "TButton"),
            ("🔅 Bright-",    lambda: self._key(220), "Brightness dn", "TButton"),
            ("🔔 Notif Bar",  lambda: self._key(83),  "Expand notifs", "TButton"),
            ("▤ Quick Set",   self._expand_qs,         "Expand Quick Settings","TButton"),

            ("▶ Play",        lambda: self._key(126), "Media Play",    "TButton"),
            ("⏸ Pause",       lambda: self._key(127), "Media Pause",   "TButton"),
            ("⏮ Prev",        lambda: self._key(88),  "Media Prev",    "TButton"),
            ("⏭ Next",        lambda: self._key(87),  "Media Next",    "TButton"),
            ("⏹ Stop Media",  lambda: self._key(86),  "Media Stop",    "TButton"),
            ("📋 Clipboard ⬆",self._push_clipboard,   "PC→Phone clip", "TButton"),

            ("⌨ Show KB",     lambda: self._key(281), "Show keyboard", "TButton"),
            ("✕ Kill App",    self._kill_foreground,  "Kill fg app",   "Danger.TButton"),
            ("↺ Reboot",      self._reboot_dialog,    "Reboot phone",  "TButton"),
            ("📦 Install APK", self._install_apk,      "Install APK",   "TButton"),
            ("⬆ Push File",   self._push_file,         "Push to phone", "TButton"),
            ("📋 Paste Text", self._paste_text,        "Type text on phone","TButton"),
        ]
        COLS = 6
        for i, (txt, cmd, tip, sty) in enumerate(quick):
            b = ttk.Button(ctrl, text=txt, style=sty, command=cmd)
            b.grid(row=i//COLS, column=i%COLS, padx=3, pady=3, sticky="ew")
            _ToolTip(b, tip)

        # ── Advanced ──────────────────────────────────────────────────────────
        adv = ttk.LabelFrame(self, text=" Advanced Features ", style="TLabelframe")
        adv.grid(row=row, column=0, sticky="ew", padx=10, pady=4)
        adv.columnconfigure((0,1,2,3), weight=1)
        row += 1

        advanced = [
            ("⬛  Desktop/Tablet Mode",  "Accent.TButton",   self._toggle_tablet,
             "Force Dual-Pane tablet mode (virtual DPI)\ntoggles between 240 dpi and device default"),
            ("👆  Gesture Automation",   "Accent.TButton",   self._gesture_automation,
             "Record & replay getevent/sendevent gestures"),
            ("🚫  Disable PowerGenie",   "TButton",          self._disable_powergenie,
             "Stop Huawei background app killer\nadb pm disable-user com.huawei.powergenie"),
            ("🔗  Port Forward",         "TButton",          self._port_forward_dialog,
             "ADB port forwarding / reverse tunnel"),
            ("📋  Logcat Viewer",        "TButton",          self._open_logcat,
             "View device logcat in real-time"),
            ("🐛  Bug Report",           "TButton",          self._bug_report,
             "Save full bugreport ZIP from device"),
            ("📊  Device Density",       "TButton",          self._density_dialog,
             "Read/set screen DPI & resolution"),
            ("📡  Wireless Debug Info",  "TButton",          self._wireless_info,
             "Show wireless debugging instructions"),
        ]
        for i, (txt, sty, cmd, tip) in enumerate(advanced):
            b = ttk.Button(adv, text=txt, style=sty, command=cmd)
            b.grid(row=i//4, column=i%4, padx=4, pady=4, sticky="ew")
            _ToolTip(b, tip)

        # ── Scrcpy output log ─────────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self, text=" Mirror Output ", style="TLabelframe")
        log_frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=(4,8))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)
        row += 1

        self._log_text = tk.Text(log_frame, height=6, state="disabled",
                                  bg=BRAND["bg"], fg=BRAND["fg2"],
                                  font=FONTS["mono_sm"], relief="flat",
                                  selectbackground=BRAND["sel"])
        self._log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        sb = ttk.Scrollbar(log_frame, command=self._log_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._log_text.configure(yscrollcommand=sb.set)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _append_log(self, line: str):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", line + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _key(self, code: int):
        def _do():
            self._adb.keyevent(code)
        self._adb.run_async(_do,
            error_cb=lambda e: self._append_log(f"keyevent error: {e}"))

    def _rotate(self, r: int):
        self._adb.run_async(lambda: self._adb.set_rotation(r))

    def _expand_qs(self):
        # Pull down twice to reach Quick Settings
        def _do():
            self._adb.keyevent(83)
            import time; time.sleep(0.3)
            self._adb.keyevent(83)
        self._adb.run_async(_do)

    def _push_clipboard(self):
        try:
            import tkinter as tk
            root = self.winfo_toplevel()
            text = root.clipboard_get()
        except Exception:
            text = ""
        if not text:
            messagebox.showinfo("Clipboard", "PC clipboard is empty.")
            return
        def _do():
            self._adb.set_clipboard(text)
        self._adb.run_async(_do,
            callback=lambda _: self._append_log("Clipboard pushed to phone."),
            error_cb=lambda e: self._append_log(f"Clipboard error: {e}"))

    def _paste_text(self):
        win = tk.Toplevel(self)
        win.title("Type on Phone")
        win.configure(bg=BRAND["bg"])
        win.resizable(True, False)
        ttk.Label(win, text="Enter text to type on phone:").pack(padx=10, pady=6)
        txt = ttk.Entry(win, width=50)
        txt.pack(padx=10, pady=4, fill="x")
        txt.focus()
        def _send():
            t = txt.get()
            if t:
                self._adb.run_async(lambda: self._adb.text(t))
            win.destroy()
        ttk.Button(win, text="Send", style="Primary.TButton",
                   command=_send).pack(pady=6)
        win.bind("<Return>", lambda _: _send())

    def _kill_foreground(self):
        def _do():
            # Get current focused package
            raw = self._adb.shell_raw(
                "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
            import re
            m = re.search(r'([a-zA-Z][a-zA-Z0-9_.]+)/[a-zA-Z]', raw)
            if m:
                pkg = m.group(1)
                self._adb.force_stop(pkg)
                return f"Killed: {pkg}"
            return "Could not determine foreground app"
        self._adb.run_async(_do,
            callback=lambda r: self._append_log(r),
            error_cb=lambda e: self._append_log(f"Error: {e}"))

    # ── Mirror actions ────────────────────────────────────────────────────────

    def _launch(self, fn):
        try:
            fn()
            self._status("Mirroring…")
            self._append_log("scrcpy started.")
        except Exception as e:
            self._append_log(f"Launch error: {e}")

    def _on_exit(self, code):
        self._status_var.set(f"Mirror ended (exit {code})")

    def _mirror(self):
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.mirror(
            cfg, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _mirror_off(self):
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.mirror_screen_off(
            cfg, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _otg(self):
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.otg(
            cfg, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _camera(self):
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.camera(
            cfg, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _record(self):
        outdir = self._settings.get("record_path", str(Path.home()/"Videos"))
        path = filedialog.asksaveasfilename(
            initialdir=outdir, defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("MKV", "*.mkv"), ("All", "*.*")],
            title="Save Recording As")
        if not path:
            return
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.record(
            cfg, path, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _record_audio(self):
        outdir = self._settings.get("record_path", str(Path.home()/"Music"))
        path = filedialog.asksaveasfilename(
            initialdir=outdir, defaultextension=".opus",
            filetypes=[("Opus", "*.opus"), ("MP3", "*.mp3"), ("All", "*.*")],
            title="Save Audio Recording As")
        if not path:
            return
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.record_audio(
            cfg, path, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _record_camera(self):
        outdir = self._settings.get("record_path", str(Path.home()/"Videos"))
        path = filedialog.asksaveasfilename(
            initialdir=outdir, defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("All", "*.*")],
            title="Save Camera Recording As")
        if not path:
            return
        cfg = self._settings.scrcpy_cfg
        self._launch(lambda: self._launcher.record_camera(
            cfg, path, self._adb.serial, on_exit=self._on_exit,
            on_output=self._append_log))

    def _stop(self):
        self._launcher.stop()
        self._gnirehtet.stop()
        self._status("Stopped.")

    # ── Gnirehtet ─────────────────────────────────────────────────────────────

    def _gnirehtet_toggle(self):
        if self._gnirehtet.running:
            self._gnirehtet.stop()
            self._append_log("Gnirehtet stopped.")
        else:
            self._gnirehtet.start(
                self._adb.serial, on_output=self._append_log)
            self._append_log("Gnirehtet started — sharing PC internet to phone.")

    # ── Screenshot ────────────────────────────────────────────────────────────

    def _screenshot(self):
        outdir = self._settings.get("screenshot_path", str(Path.home()/"Pictures"))
        from datetime import datetime
        fname = f"UAD_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(outdir, fname)
        def _do():
            self._adb.screenshot(path)
            return path
        self._adb.run_async(_do,
            callback=lambda p: self._append_log(f"Screenshot saved: {p}"),
            error_cb=lambda e: self._append_log(f"Screenshot error: {e}"))

    # ── Reboot ────────────────────────────────────────────────────────────────

    def _reboot_dialog(self):
        win = tk.Toplevel(self)
        win.title("Reboot Device")
        win.configure(bg=BRAND["bg"])
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
                callback=lambda _: self._append_log(f"Rebooting: {m}"))
            win.destroy()
        ttk.Button(win, text="Reboot", style="Danger.TButton",
                   command=_go).pack(pady=10)

    # ── Install / Push ────────────────────────────────────────────────────────

    def _install_apk(self):
        path = filedialog.askopenfilename(
            filetypes=[("APK", "*.apk"), ("All", "*.*")],
            title="Select APK to Install")
        if not path:
            return
        def _do():
            return self._adb.install_apk(path)
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo("Install APK", r),
            error_cb=lambda e: messagebox.showerror("Install Error", str(e)))

    def _push_file(self):
        path = filedialog.askopenfilename(title="Select file to push to phone")
        if not path:
            return
        fname = os.path.basename(path)
        remote = f"/sdcard/Download/{fname}"
        def _do():
            return self._adb.push(path, remote)
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo("Push File",
                                                    f"Pushed to {remote}"),
            error_cb=lambda e: messagebox.showerror("Push Error", str(e)))

    # ── Advanced ─────────────────────────────────────────────────────────────

    def _toggle_tablet(self):
        """Force desktop/tablet dual-pane mode via virtual DPI."""
        def _do():
            current = self._adb.get_density()
            if current == 240:
                self._adb.reset_density()
                return f"Density reset to default (was 240)"
            else:
                self._adb.set_density(240)
                return f"Density set to 240 dpi (tablet mode). Was: {current}"
        self._adb.run_async(_do,
            callback=lambda r: self._append_log(r),
            error_cb=lambda e: self._append_log(f"Density error: {e}"))

    def _gesture_automation(self):
        """Hardware-Level Gesture Automation via getevent/sendevent."""
        from .gesture_dialog import GestureDialog
        GestureDialog(self, self._adb)

    def _disable_powergenie(self):
        def _do():
            return self._adb.disable_package("com.huawei.powergenie")
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo(
                "PowerGenie", f"Disabled: {r}\nBackground apps should stay alive now."),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

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
        def _do():
            return self._adb.bugreport(path)
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo("Bug Report", f"Saved: {path}"),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

    def _density_dialog(self):
        win = tk.Toplevel(self)
        win.title("Screen Density & Resolution")
        win.configure(bg=BRAND["bg"])
        win.geometry("360x260")

        def _refresh():
            density.set(str(self._adb.get_density()))
            res.set(self._adb.get_resolution())

        ttk.Label(win, text="Current DPI:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        density = tk.StringVar(value="…")
        ttk.Label(win, textvariable=density).grid(row=0, column=1, sticky="w")

        ttk.Label(win, text="Resolution:").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        res = tk.StringVar(value="…")
        ttk.Label(win, textvariable=res).grid(row=1, column=1, sticky="w")

        ttk.Button(win, text="Refresh", command=lambda: self._adb.run_async(
            lambda: (self._adb.get_density(), self._adb.get_resolution()),
            callback=lambda r: (density.set(str(r[0])), res.set(r[1]))
        )).grid(row=2, column=0, columnspan=2, padx=10, pady=4)

        ttk.Label(win, text="Set DPI:").grid(row=3, column=0, padx=10, pady=4, sticky="w")
        dpi_var = tk.StringVar(value="420")
        ttk.Entry(win, textvariable=dpi_var, width=8).grid(row=3, column=1, sticky="w")

        def _set_dpi():
            dpi = int(dpi_var.get())
            self._adb.run_async(lambda: self._adb.set_density(dpi),
                callback=lambda _: _refresh())
        def _reset_dpi():
            self._adb.run_async(lambda: self._adb.reset_density(),
                callback=lambda _: _refresh())

        ttk.Button(win, text="Apply DPI", style="Primary.TButton",
                   command=_set_dpi).grid(row=4, column=0, padx=10, pady=4)
        ttk.Button(win, text="Reset DPI",
                   command=_reset_dpi).grid(row=4, column=1, padx=10, pady=4)

        self._adb.run_async(_refresh)

    def _wireless_info(self):
        info = (
            "How to enable Wireless ADB (Android 11+):\n\n"
            "1. Phone → Settings → Developer Options → Wireless debugging\n"
            "2. Toggle ON\n"
            "3. Tap 'Pair device with pairing code'\n"
            "4. Note IP, pair port, and 6-digit code\n"
            "5. In UAD → Device panel → enter IP, pair port, code → Pair\n"
            "6. After pairing, enter IP + connect port → Connect\n\n"
            "For Android 10 (like Huawei EMUI):\n"
            "1. Connect via USB first\n"
            "2. Click 'Enable WiFi ADB (tcpip 5555)'\n"
            "3. Disconnect USB, enter phone IP, click Connect"
        )
        messagebox.showinfo("Wireless ADB Guide", info)
