"""
USHCODEX Android Debugger - Logcat Viewer
Real-time device logcat with level filter, search and buffer controls.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import re

from .theme import BRAND, FONTS
from .adb_manager import ADBManager, ADBError

ADB_PATH = r"C:\Users\PC\Projects\Scrcpy\adb.exe"

LEVEL_TAGS = {
    "V": "verbose", "D": "debug", "I": "info",
    "W": "warn",    "E": "error",  "F": "fatal",
}


class LogcatViewer(tk.Toplevel):
    """Live logcat stream with filters."""

    def __init__(self, parent, adb: ADBManager):
        super().__init__(parent)
        self._adb = adb
        self._proc = None
        self._thread = None
        self._streaming = False
        self._filter_text = ""
        self._min_level = "V"

        self.title("Logcat Viewer — USHCODEX Android Debugger")
        self.configure(bg=BRAND["bg"])
        self.geometry("980x640")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        bar = ttk.Frame(self, style="Panel.TFrame")
        bar.grid(row=0, column=0, sticky="ew")

        self._start_btn = ttk.Button(bar, text="▶ Start", style="Success.TButton",
                                     command=self._start)
        self._start_btn.pack(side="left", padx=6, pady=6)
        self._stop_btn = ttk.Button(bar, text="⏹ Stop", style="Danger.TButton",
                                    command=self._stop, state="disabled")
        self._stop_btn.pack(side="left", padx=2, pady=6)
        ttk.Button(bar, text="🗑 Clear", command=self._clear
                   ).pack(side="left", padx=2, pady=6)
        ttk.Button(bar, text="💾 Save…", command=self._save
                   ).pack(side="left", padx=2, pady=6)

        ttk.Label(bar, text="Level:", style="Panel.TLabel").pack(
            side="left", padx=(14, 2))
        self._level_var = tk.StringVar(value="V")
        lvl = ttk.Combobox(bar, textvariable=self._level_var, width=5,
                           values=["V", "D", "I", "W", "E"],
                           state="readonly")
        lvl.pack(side="left")
        lvl.bind("<<ComboboxSelected>>", lambda _: self._apply_level())

        ttk.Label(bar, text="Filter:", style="Panel.TLabel").pack(
            side="left", padx=(14, 2))
        self._filter_var = tk.StringVar()
        f = ttk.Entry(bar, textvariable=self._filter_var, width=28)
        f.pack(side="left")
        f.bind("<KeyRelease>", lambda _: self._apply_filter())
        ttk.Checkbutton(bar, text="Case sensitive",
                        command=self._toggle_case).pack(side="left", padx=8)
        self._case_sensitive = False

        # Output
        out = ttk.Frame(self)
        out.grid(row=1, column=0, sticky="nsew")
        out.columnconfigure(0, weight=1)
        out.rowconfigure(0, weight=1)

        self._text = tk.Text(out, state="disabled", wrap="none",
                             bg=BRAND["bg"], fg=BRAND["fg"],
                             font=FONTS["mono_sm"], relief="flat",
                             selectbackground=BRAND["sel"])
        self._text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(out, command=self._text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=sb.set)

        # Tag colours per level
        self._text.tag_configure("verbose", foreground="#8a8aa8")
        self._text.tag_configure("debug",   foreground="#6ec6ff")
        self._text.tag_configure("info",    foreground="#3ddc84")
        self._text.tag_configure("warn",    foreground="#ffb347")
        self._text.tag_configure("error",   foreground="#ff4f5e")
        self._text.tag_configure("fatal",   foreground="#ff4f5e",
                                 background="#3a1020")
        self._text.tag_configure("match",   background="#3a2a5a")

        self._status = tk.StringVar(value="Stopped")
        ttk.Label(self, textvariable=self._status, style="TLabel",
                  font=FONTS["small"]).grid(row=2, column=0, sticky="w", padx=8)

    # ── Streaming ─────────────────────────────────────────────────────────────

    def _start(self):
        if self._streaming:
            return
        self._clear()
        self._streaming = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status.set("Streaming logcat…")
        args = [ADB_PATH]
        if self._adb.serial:
            args += ["-s", self._adb.serial]
        args += ["logcat", "-v", "brief"]
        try:
            self._proc = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            self._status.set(f"Failed to start: {e}")
            self._streaming = False
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")
            return
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        try:
            for line in self._proc.stdout:
                if not self._streaming:
                    break
                line = line.rstrip("\r\n")
                if line:
                    self.after(0, self._append, line)
        except Exception:
            pass
        self.after(0, lambda: self._status.set("Stream ended."))

    def _append(self, line: str):
        tag = "info"
        m = re.match(r'^\S+\s+\S+\s+([VDIWEF])/', line)
        if m:
            tag = LEVEL_TAGS.get(m.group(1), "info")
        self._text.configure(state="normal")
        self._text.insert("end", line + "\n", tag)
        # cap size to keep UI responsive
        if int(self._text.index("end-1c").split(".")[0]) > 20000:
            self._text.delete("1.0", "5000.0")
        if self._passes_filter(line):
            self._text.see("end")
        self._text.configure(state="disabled")

    def _passes_filter(self, line: str) -> bool:
        # level check
        m = re.match(r'^\S+\s+\S+\s+([VDIWEF])/', line)
        if m:
            order = "VDIWEF"
            if order.index(m.group(1)) < order.index(self._min_level):
                return False
        text = self._filter_text
        if not text:
            return True
        hay = line if self._case_sensitive else line.lower()
        needle = text if self._case_sensitive else text.lower()
        return needle in hay

    def _stop(self):
        self._streaming = False
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._status.set("Stopped.")

    def _clear(self):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    # ── Filters ───────────────────────────────────────────────────────────────

    def _apply_filter(self):
        self._filter_text = self._filter_var.get()

    def _toggle_case(self):
        self._case_sensitive = not self._case_sensitive

    def _apply_level(self):
        self._min_level = self._level_var.get()

    def _save(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text", "*.txt"), ("All", "*.*")],
            title="Save Logcat As")
        if not path:
            return
        content = self._text.get("1.0", "end")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self._status.set(f"Saved: {path}")

    def _on_close(self):
        self._stop()
        self.destroy()
