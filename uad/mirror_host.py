"""
USHCODEX Android Debugger - Mirror Host
Launches scrcpy and embeds its window inside a Tkinter frame using Win32
SetParent, so device controls live beside the screen instead of on top of it.
"""
from __future__ import annotations
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import windll, wintypes

from .theme import BRAND, FONTS

WS_CHILD    = 0x40000000
WS_VISIBLE  = 0x10000000
WS_POPUP    = 0x80000000
WS_CAPTION  = 0x00C00000
WS_THICKFRAME = 0x00040000
SWP_FRAMECHANGED = 0x0020
SWP_NOZORDER     = 0x0004
GWL_STYLE = -16

u32 = windll.user32
# Proper Win32 prototypes (LONG_PTR args overflow plain ints)
if hasattr(u32, "SetWindowLongPtrW"):
    u32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    u32.GetWindowLongPtrW.restype  = ctypes.c_longlong
    u32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_longlong]
    u32.SetWindowLongPtrW.restype  = ctypes.c_longlong
u32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
u32.GetWindowLongW.restype  = ctypes.c_long
u32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
u32.SetWindowLongW.restype  = ctypes.c_long
u32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
u32.SetParent.restype  = wintypes.HWND
u32.GetParent.argtypes = [wintypes.HWND]
u32.GetParent.restype  = wintypes.HWND
u32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
u32.FindWindowW.restype  = wintypes.HWND
u32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND,
                             ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             ctypes.c_uint]
u32.SetWindowPos.restype = wintypes.BOOL


class MirrorHost(ttk.Frame):
    """
    A frame that hosts the scrcpy video window as a Win32 child.

    Launch flow:
      1. launcher launches scrcpy with a unique --window-title
      2. a poll thread finds the HWND (FindWindowW)
      3. the HWND is re-styled to WS_CHILD and SetParent'ed into this frame
      4. on <Configure> the child is resized to fill the frame
    """

    def __init__(self, parent, launcher, log_fn=None):
        super().__init__(parent, style="Host.TFrame")
        self._launcher = launcher
        self._log = log_fn or (lambda msg: None)
        self._hwnd: wintypes.HWND | None = None
        self._title: str | None = None
        self._embedded = False
        self._poll_stop = threading.Event()
        self._q: queue.Queue = queue.Queue()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.bind("<Configure>", self._on_configure)
        self._build_empty_state()
        self._drain_queue()

    # ── Empty state ───────────────────────────────────────────────────────────

    def _build_empty_state(self):
        self._empty = tk.Frame(self, bg=BRAND["purple_soft"])
        self._empty.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        lbl = tk.Label(
            self._empty, bg=BRAND["purple_soft"], fg=BRAND["purple"],
            font=(FONTS["h2"][0], FONTS["h2"][1], "bold"),
            text="⏵  Start Mirror to embed the device screen here")
        lbl.pack(expand=True)
        sub = tk.Label(self._empty, bg=BRAND["purple_soft"], fg=BRAND["muted"],
                       font=FONTS["small"],
                       text="The phone screen appears inside this panel.\n"
                            "All controls are in the sidebar →")
        sub.pack(pady=(0, 30))

    def _hide_empty(self):
        self._empty.grid_forget()

    def _show_empty(self):
        self._empty.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

    # ── Launch & embed ────────────────────────────────────────────────────────

    def start(self, args_builder) -> None:
        """args_builder(title) -> full scrcpy argv list."""
        self._title = f"UAD-MIRROR-{os.getpid()}"
        self._poll_stop.clear()
        self._embedded = False
        args = args_builder(self._title)
        self._launcher.launch_args(args, on_exit=self._on_exit)
        threading.Thread(target=self._poll_for_window, daemon=True).start()
        self._log("Launching mirror session…")

    def _poll_for_window(self):
        deadline = time.time() + 20
        hwnd = None
        while time.time() < deadline and not self._poll_stop.is_set():
            hwnd = u32.FindWindowW(None, self._title)
            if hwnd:
                break
            time.sleep(0.25)
        if self._poll_stop.is_set():
            return
        self._q.put(hwnd if hwnd else "NOTFOUND")

    def _drain_queue(self):
        """Runs on the Tk main thread; applies queued results safely."""
        try:
            while True:
                item = self._q.get_nowait()
                if item == "NOTFOUND":
                    if self._launcher.running:
                        self._log("Mirror window not found yet — still looking…")
                elif isinstance(item, str) and item.startswith("EXIT:"):
                    code = item.split(":", 1)[1]
                    self._show_empty()
                    self._log(f"Mirror session ended (code {code}).")
                elif item and not self._poll_stop.is_set():
                    self._hwnd = item
                    self._embed()
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(150, self._drain_queue)

    def _embed(self):
        if not self._hwnd:
            return
        hwnd = self._hwnd
        host_hwnd = self.winfo_id()

        # Re-style as a child window (strip popup/caption/thickframe)
        get_style = u32.GetWindowLongPtrW if hasattr(u32, "GetWindowLongPtrW") \
            else u32.GetWindowLongW
        set_style = u32.SetWindowLongPtrW if hasattr(u32, "SetWindowLongPtrW") \
            else u32.SetWindowLongW

        style = get_style(hwnd, GWL_STYLE) & 0xFFFFFFFF
        style = (style & ~WS_POPUP & ~WS_CAPTION & ~WS_THICKFRAME) | WS_CHILD
        set_style(hwnd, GWL_STYLE, style)

        # Move to origin first, then re-parent, then resize inside the host
        u32.SetWindowPos(hwnd, wintypes.HWND(0), 0, 0, 10, 10,
                         SWP_NOZORDER | SWP_FRAMECHANGED)
        ok = u32.SetParent(hwnd, host_hwnd)
        parent_after = u32.GetParent(hwnd)
        self._resize()

        # Some SDL builds re-apply their own geometry shortly after creation;
        # re-assert the child geometry a couple of times.
        for delay in (300, 800, 1500):
            self.after(delay, self._resize)

        if parent_after == host_hwnd or ok:
            self._hide_empty()
            self._embedded = True
            self._log("Mirror embedded. Click the screen to give it input focus.")
        else:
            self._log("Mirror running in its own window (embedding failed).")

    def _on_configure(self, _event=None):
        if self._embedded:
            self._resize()

    def _resize(self):
        if not self._hwnd:
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w > 4 and h > 4:
            u32.SetWindowPos(
                self._hwnd, wintypes.HWND(0), 0, 0, w, h,
                SWP_NOZORDER | SWP_FRAMECHANGED)

    def _on_exit(self, code):
        self._poll_stop.set()
        self._hwnd = None
        self._embedded = False
        self._q.put(f"EXIT:{code}")

    def stop(self):
        self._poll_stop.set()
        self._launcher.stop()
