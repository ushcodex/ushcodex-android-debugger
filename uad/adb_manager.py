"""
USHCODEX Android Debugger - ADB Manager
Wraps all ADB operations in a clean async-friendly interface.
"""
import subprocess
import threading
import shlex
import os
import re
from pathlib import Path
from typing import Callable, Optional

ADB_PATH = r"C:\Users\PC\Projects\Scrcpy\adb.exe"


class ADBError(Exception):
    pass


def _run(args: list[str], timeout: int = 20, shell: bool = False) -> str:
    """Run ADB synchronously; returns stdout or raises ADBError."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, shell=shell,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            raise ADBError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise ADBError("ADB command timed out")
    except FileNotFoundError:
        raise ADBError(f"ADB not found: {ADB_PATH}")


class ADBManager:
    """Thread-safe ADB manager. All blocking operations run in daemon threads."""

    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self._lock = threading.Lock()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _base(self) -> list[str]:
        cmd = [ADB_PATH]
        if self.serial:
            cmd += ["-s", self.serial]
        return cmd

    def _shell(self, *args) -> str:
        return _run(self._base() + ["shell"] + list(args))

    def _adb(self, *args, timeout: int = 20) -> str:
        return _run(self._base() + list(args), timeout=timeout)

    def run_async(self, fn: Callable, callback: Callable = None,
                  error_cb: Callable = None) -> threading.Thread:
        """Run fn() in a daemon thread; call callback(result) or error_cb(exc)."""
        def _worker():
            try:
                res = fn()
                if callback:
                    callback(res)
            except Exception as exc:
                if error_cb:
                    error_cb(exc)
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    # ── Device Discovery ──────────────────────────────────────────────────────

    def list_devices(self) -> list[dict]:
        """Return list of {serial, state, model} dicts."""
        raw = _run([ADB_PATH, "devices", "-l"])
        devices = []
        for line in raw.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]
            model_match = re.search(r'model:(\S+)', line)
            model = model_match.group(1).replace("_", " ") if model_match else "Unknown"
            transport = "USB"
            if re.match(r'\d+\.\d+\.\d+\.\d+', serial):
                transport = "WiFi"
            devices.append({"serial": serial, "state": state,
                            "model": model, "transport": transport})
        return devices

    def select(self, serial: str):
        self.serial = serial

    # ── Connectivity ──────────────────────────────────────────────────────────

    def connect(self, host: str, port: int = 5555) -> str:
        return _run([ADB_PATH, "connect", f"{host}:{port}"])

    def disconnect(self, host: Optional[str] = None) -> str:
        if host:
            return _run([ADB_PATH, "disconnect", host])
        return _run([ADB_PATH, "disconnect"])

    def tcpip(self, port: int = 5555) -> str:
        return self._adb("tcpip", str(port))

    def pair(self, host: str, port: int, code: str) -> str:
        return _run([ADB_PATH, "pair", f"{host}:{port}", code])

    # ── Device Info ───────────────────────────────────────────────────────────

    def device_info(self) -> dict:
        props = {}
        try:
            raw = self._shell("getprop")
            for m in re.finditer(r'\[(.+?)\]:\s*\[(.+?)\]', raw):
                props[m.group(1)] = m.group(2)
        except ADBError:
            pass
        info = {
            "model":       props.get("ro.product.model", "Unknown"),
            "brand":       props.get("ro.product.brand", "Unknown"),
            "android":     props.get("ro.build.version.release", "?"),
            "sdk":         props.get("ro.build.version.sdk", "?"),
            "serial":      props.get("ro.serialno", self.serial or "?"),
            "cpu":         props.get("ro.hardware", "?"),
            "density":     self._safe_shell("wm density"),
            "resolution":  self._safe_shell("wm size"),
            "battery":     self._battery(),
            "storage":     self._storage(),
        }
        return info

    def _safe_shell(self, *args) -> str:
        try:
            return self._shell(*args)
        except ADBError:
            return "?"

    def _battery(self) -> str:
        try:
            raw = self._shell("dumpsys", "battery")
            level = re.search(r'level:\s*(\d+)', raw)
            status = re.search(r'status:\s*(\d+)', raw)
            stat_map = {"1": "Unknown", "2": "Charging", "3": "Discharging",
                        "4": "Not Charging", "5": "Full"}
            lvl = level.group(1) if level else "?"
            stat = stat_map.get(status.group(1) if status else "", "?")
            return f"{lvl}% ({stat})"
        except ADBError:
            return "?"

    def _storage(self) -> str:
        try:
            raw = self._shell("df", "/sdcard")
            parts = raw.splitlines()[-1].split()
            if len(parts) >= 4:
                return f"{parts[3]} free / {parts[1]} total"
        except ADBError:
            pass
        return "?"

    # ── Keyevents ─────────────────────────────────────────────────────────────

    def keyevent(self, code: int | str) -> None:
        self._shell("input", "keyevent", str(code))

    def tap(self, x: int, y: int) -> None:
        self._shell("input", "tap", str(x), str(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 300) -> None:
        self._shell("input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms))

    def text(self, txt: str) -> None:
        # Escape for shell
        txt = txt.replace("'", "\\'").replace(" ", "%s")
        self._shell("input", "text", txt)

    # ── Screen ────────────────────────────────────────────────────────────────

    def screenshot(self, local_path: str) -> str:
        self._adb("exec-out", "screencap", "-p", timeout=15)
        subprocess.run(
            self._base() + ["exec-out", "screencap", "-p"],
            stdout=open(local_path, "wb"), timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return local_path

    def screen_off(self) -> None:
        self._shell("input", "keyevent", "26")

    def screen_on(self) -> None:
        self._shell("input", "keyevent", "224")

    def set_rotation(self, r: int) -> None:
        """r: 0=portrait, 1=landscape, 2=reverse-portrait, 3=reverse-landscape"""
        self._shell("settings", "put", "system", "user_rotation", str(r))
        self._shell("settings", "put", "system", "accelerometer_rotation", "0")

    def auto_rotation(self, enabled: bool) -> None:
        self._shell("settings", "put", "system", "accelerometer_rotation",
                    "1" if enabled else "0")

    # ── Volume ────────────────────────────────────────────────────────────────

    def volume_up(self)   -> None: self.keyevent(24)
    def volume_down(self) -> None: self.keyevent(25)
    def volume_mute(self) -> None: self.keyevent(164)

    # ── Clipboard ─────────────────────────────────────────────────────────────

    def set_clipboard(self, text: str) -> None:
        """Push text to Android clipboard via ADB."""
        # Use am broadcast with an intent (works on Android 7+)
        escaped = text.replace("'", "'\\''")
        self._shell(f"am broadcast -a clipper.set -e text '{escaped}'")

    def get_clipboard(self) -> str:
        """Attempt to retrieve Android clipboard text."""
        try:
            return self._shell("am broadcast -a clipper.get").strip()
        except ADBError:
            return ""

    # ── App Management ────────────────────────────────────────────────────────

    def install_apk(self, local_path: str, replace: bool = True) -> str:
        args = ["-r"] if replace else []
        return self._adb("install", *args, local_path, timeout=120)

    def list_packages(self, filter_: str = "") -> list[str]:
        raw = self._shell("pm", "list", "packages")
        pkgs = [l.replace("package:", "").strip() for l in raw.splitlines()]
        if filter_:
            pkgs = [p for p in pkgs if filter_.lower() in p.lower()]
        return pkgs

    def force_stop(self, pkg: str) -> None:
        self._shell("am", "force-stop", pkg)

    def launch_app(self, pkg: str) -> None:
        self._shell("monkey", "-p", pkg, "-c",
                    "android.intent.category.LAUNCHER", "1")

    def clear_app_data(self, pkg: str) -> str:
        return self._shell("pm", "clear", pkg)

    def disable_package(self, pkg: str) -> str:
        return self._shell("pm", "disable-user", "--user", "0", pkg)

    def enable_package(self, pkg: str) -> str:
        return self._shell("pm", "enable", pkg)

    def uninstall_package(self, pkg: str) -> str:
        return self._adb("uninstall", pkg)

    # ── File System ───────────────────────────────────────────────────────────

    def ls(self, path: str) -> list[dict]:
        raw = self._shell("ls", "-lA", "--color=never", path)
        entries = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("total"):
                continue
            m = re.match(
                r'^([d\-lrwxst]+)\s+\S+\s+\S+\s+(\S+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)$',
                line
            )
            if m:
                is_dir = m.group(1).startswith("d")
                is_link = m.group(1).startswith("l")
                name = m.group(5)
                if " -> " in name:
                    name = name.split(" -> ")[0]
                entries.append({
                    "perms": m.group(1),
                    "size":  m.group(2),
                    "date":  f"{m.group(3)} {m.group(4)}",
                    "name":  name,
                    "is_dir": is_dir,
                    "is_link": is_link,
                })
        return entries

    def pull(self, remote: str, local: str, progress_cb: Callable = None) -> str:
        return self._adb("pull", remote, local, timeout=600)

    def push(self, local: str, remote: str) -> str:
        return self._adb("push", local, remote, timeout=600)

    def delete(self, remote: str, recursive: bool = False) -> str:
        if recursive:
            return self._shell("rm", "-rf", remote)
        return self._shell("rm", "-f", remote)

    def mkdir(self, remote: str) -> str:
        return self._shell("mkdir", "-p", remote)

    def rename(self, src: str, dst: str) -> str:
        return self._shell("mv", src, dst)

    def stat(self, path: str) -> str:
        return self._safe_shell("stat", path)

    # ── System ────────────────────────────────────────────────────────────────

    def get_density(self) -> int:
        raw = self._safe_shell("wm density")
        m = re.search(r'(\d+)', raw)
        return int(m.group(1)) if m else 420

    def set_density(self, dpi: int) -> None:
        self._shell("wm", "density", str(dpi))

    def reset_density(self) -> None:
        self._shell("wm", "density", "reset")

    def get_resolution(self) -> str:
        return self._safe_shell("wm size")

    def set_resolution(self, w: int, h: int) -> None:
        self._shell("wm", "size", f"{w}x{h}")

    def reset_resolution(self) -> None:
        self._shell("wm", "size", "reset")

    def trim_caches(self) -> None:
        self._shell("pm", "trim-caches", "9999999999")

    def reboot(self, mode: str = "") -> None:
        """mode: '' | 'bootloader' | 'recovery' | 'sideload'"""
        if mode:
            self._adb("reboot", mode)
        else:
            self._adb("reboot")

    def root(self) -> str:
        return self._adb("root")

    def remount(self) -> str:
        return self._adb("remount")

    def bugreport(self, path: str) -> str:
        return self._adb("bugreport", path, timeout=120)

    def logcat(self, lines: int = 200) -> str:
        return self._adb("logcat", "-d", "-t", str(lines))

    # ── getevent / sendevent ──────────────────────────────────────────────────

    def list_input_devices(self) -> str:
        return self._safe_shell("getevent", "-l", "-p")

    def replay_sendevent(self, device: str, events: list[tuple]) -> None:
        """events: list of (type, code, value) int tuples."""
        for etype, ecode, evalue in events:
            self._shell("sendevent", device, str(etype), str(ecode), str(evalue))

    # ── Port Forwarding ───────────────────────────────────────────────────────

    def forward(self, local: str, remote: str) -> str:
        return self._adb("forward", local, remote)

    def forward_list(self) -> str:
        return self._adb("forward", "--list")

    def forward_remove_all(self) -> str:
        return self._adb("forward", "--remove-all")

    def reverse(self, remote: str, local: str) -> str:
        return self._adb("reverse", remote, local)

    def reverse_list(self) -> str:
        return self._adb("reverse", "--list")

    # ── Shell (raw) ───────────────────────────────────────────────────────────

    def shell_raw(self, cmd: str, timeout: int = 30) -> str:
        return _run(self._base() + ["shell", cmd], timeout=timeout)

    def start_shell_process(self) -> subprocess.Popen:
        """Return a Popen for an interactive ADB shell."""
        return subprocess.Popen(
            self._base() + ["shell"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
