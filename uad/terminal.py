"""
USHCODEX Android Debugger - Terminal Tab
Interactive ADB shell with ANSI-stripped output.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import queue
import re

from .theme import BRAND, FONTS
from .adb_manager import ADBManager

ADB = r"C:\Users\PC\Projects\Scrcpy\adb.exe"
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class TerminalTab(ttk.Frame):
    """ADB Shell terminal with I/O."""

    def __init__(self, parent, adb: ADBManager):
        super().__init__(parent, style="TFrame")
        self._adb = adb
        self._proc = None
        self._q = queue.Queue()
        self._history: list[str] = []
        self._hist_idx = -1
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Output area
        out_frame = ttk.Frame(self, style="TFrame")
        out_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        out_frame.columnconfigure(0, weight=1)
        out_frame.rowconfigure(0, weight=1)

        self._output = tk.Text(out_frame, state="disabled",
                                bg=BRAND["bg"], fg=BRAND["fg"],
                                font=FONTS["mono"], relief="flat",
                                selectbackground=BRAND["sel"],
                                insertbackground=BRAND["accent"],
                                wrap="word")
        self._output.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(out_frame, command=self._output.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._output.configure(yscrollcommand=sb.set)

        # Tag colours
        self._output.tag_configure("prompt",  foreground=BRAND["accent"])
        self._output.tag_configure("output",  foreground=BRAND["fg"])
        self._output.tag_configure("error",   foreground=BRAND["danger"])
        self._output.tag_configure("info",    foreground=BRAND["fg2"])

        # Input bar
        in_bar = ttk.Frame(self, style="Panel.TFrame")
        in_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        in_bar.columnconfigure(1, weight=1)

        ttk.Label(in_bar, text="$ ", style="Panel.TLabel",
                  font=FONTS["mono"], foreground=BRAND["accent"]
                  ).grid(row=0, column=0, padx=(8,2), pady=6)

        self._input_var = tk.StringVar()
        self._input = ttk.Entry(in_bar, textvariable=self._input_var,
                                 font=FONTS["mono"], style="TEntry")
        self._input.grid(row=0, column=1, sticky="ew", padx=2, pady=6)
        self._input.bind("<Return>",    self._send_command)
        self._input.bind("<Up>",        self._hist_up)
        self._input.bind("<Down>",      self._hist_down)
        self._input.bind("<Tab>",       self._autocomplete)

        ttk.Button(in_bar, text="Send", style="Primary.TButton",
                   command=self._send_command).grid(row=0, column=2, padx=4)

        # Action buttons
        ab = ttk.Frame(self, style="Panel.TFrame")
        ab.grid(row=2, column=0, sticky="ew", padx=4, pady=2)
        for txt, cmd in [
            ("Connect Shell",  self._start_shell),
            ("Disconnect",     self._stop_shell),
            ("Clear",          self._clear),
            ("Copy Output",    self._copy_all),
        ]:
            ttk.Button(ab, text=txt, command=cmd).pack(side="left", padx=4, pady=4)

        # Device quick-commands
        qc = ttk.Frame(self, style="TFrame")
        qc.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        ttk.Label(qc, text="Quick:", font=FONTS["small"],
                  foreground=BRAND["fg2"]).pack(side="left", padx=4)
        for label, cmd in [
            ("top",         "top -n 1"),
            ("df",          "df -h"),
            ("ps",          "ps aux"),
            ("netstat",     "netstat"),
            ("logcat -d",   "logcat -d -t 50"),
            ("getprop",     "getprop"),
            ("pm list",     "pm list packages"),
            ("wm size",     "wm size"),
            ("wm density",  "wm density"),
        ]:
            ttk.Button(qc, text=label, style="TButton",
                       command=lambda c=cmd: self._run_quick(c)
                       ).pack(side="left", padx=2)

    # ── Shell Process ─────────────────────────────────────────────────────────

    def _start_shell(self):
        if self._proc and self._proc.poll() is None:
            self._append("Already connected.\n", "info")
            return
        serial = self._adb.serial
        args = [ADB]
        if serial:
            args += ["-s", serial]
        args += ["shell"]
        try:
            self._proc = subprocess.Popen(
                args, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._append("Shell connected.\n", "info")
            threading.Thread(target=self._reader, daemon=True).start()
            self._input.focus()
        except Exception as e:
            self._append(f"Error: {e}\n", "error")

    def _stop_shell(self):
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None
            self._append("\nShell disconnected.\n", "info")

    def _reader(self):
        try:
            for line in self._proc.stdout:
                clean = ANSI_ESCAPE.sub("", line)
                self._append(clean, "output")
        except Exception:
            pass
        self._append("\n[shell exited]\n", "info")

    def _send_command(self, _=None):
        cmd = self._input_var.get()
        if not cmd.strip():
            return
        self._history.append(cmd)
        self._hist_idx = len(self._history)
        self._append(f"$ {cmd}\n", "prompt")
        self._input_var.set("")

        if self._proc and self._proc.poll() is None:
            try:
                self._proc.stdin.write(cmd + "\n")
                self._proc.stdin.flush()
            except Exception as e:
                self._append(f"Error writing to shell: {e}\n", "error")
        else:
            # One-shot command
            self._run_quick(cmd)

    def _run_quick(self, cmd: str):
        def _do():
            return self._adb.shell_raw(cmd, timeout=15)
        self._append(f"$ {cmd}\n", "prompt")
        self._adb.run_async(_do,
            callback=lambda r: self._append(r + "\n", "output"),
            error_cb=lambda e: self._append(f"Error: {e}\n", "error"))

    def _append(self, text: str, tag: str = "output"):
        self._output.configure(state="normal")
        self._output.insert("end", text, tag)
        self._output.see("end")
        self._output.configure(state="disabled")

    def _clear(self):
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")

    def _copy_all(self):
        text = self._output.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("UAD", "Terminal output copied to clipboard.")

    # ── History ───────────────────────────────────────────────────────────────

    def _hist_up(self, _=None):
        if self._history:
            self._hist_idx = max(0, self._hist_idx - 1)
            self._input_var.set(self._history[self._hist_idx])

    def _hist_down(self, _=None):
        if self._history:
            self._hist_idx = min(len(self._history)-1, self._hist_idx + 1)
            if self._hist_idx < len(self._history):
                self._input_var.set(self._history[self._hist_idx])
            else:
                self._input_var.set("")

    def _autocomplete(self, _=None):
        # Basic tab-completion via ls on the shell
        cmd = self._input_var.get()
        return "break"
