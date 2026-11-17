"""
USHCODEX Android Debugger - Scrcpy Launcher
Builds and launches scrcpy.exe with full option support.
"""
import subprocess
import threading
import os
from typing import Optional, Callable

SCRCPY_PATH  = r"C:\Users\PC\Projects\Scrcpy\scrcpy.exe"
ADB_PATH      = r"C:\Users\PC\Projects\Scrcpy\adb.exe"
GNIREHTET    = r"C:\Users\PC\Projects\Scrcpy\Escrcpy\resources\extra\win\gnirehtet\gnirehtet.exe"


class ScrcpySession:
    """Manages a running scrcpy subprocess."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._on_exit: Optional[Callable] = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def launch(self, args: list[str], on_exit: Callable = None,
               on_output: Callable = None) -> None:
        if self.running:
            self.stop()
        self._on_exit = on_exit
        self._proc = subprocess.Popen(
            [SCRCPY_PATH] + args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self._thread = threading.Thread(
            target=self._reader, args=(on_output,), daemon=True)
        self._thread.start()

    def _reader(self, on_output: Callable):
        try:
            for line in self._proc.stdout:
                if on_output:
                    on_output(line.rstrip())
        except Exception:
            pass
        retcode = self._proc.wait()
        if self._on_exit:
            self._on_exit(retcode)

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def pid(self) -> Optional[int]:
        if self._proc:
            return self._proc.pid
        return None


class ScrcpyLauncher:
    """
    Builds scrcpy argument lists from UAD settings and launches them.
    One session at a time (stops previous before new launch).
    """

    # ── Video codec map ───────────────────────────────────────────────────────
    CODECS = {"H.264": "h264", "H.265": "h265", "AV1": "av1"}

    # ── Mouse mode map ────────────────────────────────────────────────────────
    MOUSE_MODES = {
        "SDK (default)": "sdk",
        "UHID (true mouse)": "uhid",
        "AOAM": "aoam",
        "Disabled": "disabled",
    }

    def __init__(self):
        self._session = ScrcpySession()

    @property
    def running(self) -> bool:
        return self._session.running

    def pid(self) -> Optional[int]:
        return self._session.pid()

    # ── Argument builders ─────────────────────────────────────────────────────

    def _base_args(self, cfg: dict, serial: Optional[str] = None) -> list[str]:
        args = []

        if serial:
            args += ["-s", serial]

        # Video
        codec = self.CODECS.get(cfg.get("codec", "H.264"), "h264")
        args += ["--video-codec", codec]

        bitrate = cfg.get("bitrate", "8M")
        args += ["--video-bit-rate", bitrate]

        fps = cfg.get("fps", "60")
        args += ["--max-fps", str(fps)]

        resolution = cfg.get("resolution", "0")
        if resolution and resolution != "0" and resolution != "Native":
            args += ["--max-size", str(resolution)]

        # Audio
        if not cfg.get("audio", True):
            args += ["--no-audio"]
        else:
            audio_codec = cfg.get("audio_codec", "opus")
            args += ["--audio-codec", audio_codec]

        # Mouse
        mouse_mode = self.MOUSE_MODES.get(
            cfg.get("mouse_mode", "UHID (true mouse)"), "uhid")
        args += ["--mouse", mouse_mode]

        # Display
        if cfg.get("borderless", False):
            args += ["--window-borderless"]
        if cfg.get("always_on_top", False):
            args += ["--always-on-top"]
        if cfg.get("fullscreen", False):
            args += ["-f"]

        # Window title
        args += ["--window-title", "USHCODEX Android Debugger"]

        # Stay awake
        if cfg.get("stay_awake", True):
            args += ["--stay-awake"]

        # Power off on close
        if cfg.get("power_off_on_close", False):
            args += ["--power-off-on-close"]

        # Show touches
        if cfg.get("show_touches", False):
            args += ["--show-touches"]

        # Disable screensaver
        if cfg.get("disable_screensaver", False):
            args += ["--disable-screensaver"]

        # No clipboard autosync
        if not cfg.get("clipboard_autosync", True):
            args += ["--no-clipboard-autosync"]

        # Window position
        wx = cfg.get("window_x")
        wy = cfg.get("window_y")
        ww = cfg.get("window_w")
        wh = cfg.get("window_h")
        if wx is not None: args += ["--window-x", str(wx)]
        if wy is not None: args += ["--window-y", str(wy)]
        if ww is not None: args += ["--window-width",  str(ww)]
        if wh is not None: args += ["--window-height", str(wh)]

        # Lock video orientation
        orient = cfg.get("lock_orientation")
        if orient is not None and orient != "Auto":
            map_ = {"Portrait": "0", "Landscape": "1",
                    "Rev. Portrait": "2", "Rev. Landscape": "3"}
            if orient in map_:
                args += ["--lock-video-orientation", map_[orient]]

        # Rotation
        rotation = cfg.get("rotation")
        if rotation:
            args += ["--rotation", str(rotation)]

        return args

    # ── Launch modes ──────────────────────────────────────────────────────────

    def mirror(self, cfg: dict, serial: str = None,
               on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial)
        self._session.launch(args, on_exit, on_output)

    def mirror_screen_off(self, cfg: dict, serial: str = None,
                          on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + ["--turn-screen-off"]
        self._session.launch(args, on_exit, on_output)

    def otg(self, cfg: dict, serial: str = None,
            on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + ["--otg"]
        self._session.launch(args, on_exit, on_output)

    def camera(self, cfg: dict, serial: str = None,
               on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + ["--video-source=camera"]
        self._session.launch(args, on_exit, on_output)

    def record(self, cfg: dict, output_path: str, serial: str = None,
               on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + ["-r", output_path, "--no-display"]
        self._session.launch(args, on_exit, on_output)

    def record_audio(self, cfg: dict, output_path: str, serial: str = None,
                     on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + [
            "--no-video", "-r", output_path, "--no-display"]
        self._session.launch(args, on_exit, on_output)

    def record_camera(self, cfg: dict, output_path: str, serial: str = None,
                      on_exit: Callable = None, on_output: Callable = None) -> None:
        args = self._base_args(cfg, serial) + [
            "--video-source=camera", "-r", output_path, "--no-display"]
        self._session.launch(args, on_exit, on_output)

    def custom(self, raw_args: list[str], serial: str = None,
               on_exit: Callable = None, on_output: Callable = None) -> None:
        pre = ["-s", serial] if serial else []
        self._session.launch(pre + raw_args, on_exit, on_output)

    def stop(self) -> None:
        self._session.stop()


class GnirehtetSession:
    """Manages gnirehtet (reverse tethering) process."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, serial: str = None, on_output: Callable = None) -> None:
        if self.running:
            self.stop()
        args = [GNIREHTET, "run"]
        if serial:
            args.append(serial)
        self._proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if on_output:
            threading.Thread(
                target=self._reader, args=(on_output,), daemon=True).start()

    def _reader(self, cb: Callable):
        for line in self._proc.stdout:
            cb(line.rstrip())

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
