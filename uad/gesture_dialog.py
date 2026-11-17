"""
USHCODEX Android Debugger - Gesture Automation Dialog
Hardware-Level Gesture Automation via getevent / sendevent.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import subprocess
import time
import re
import os
from pathlib import Path

from .theme import BRAND, FONTS
from .adb_manager import ADBManager

ADB = r"C:\Users\PC\Projects\Scrcpy\adb.exe"


class GestureDialog(tk.Toplevel):
    """
    Record getevent events from the phone, then replay them via sendevent.
    Also supports simple tap/swipe macros via input command.
    """

    def __init__(self, parent, adb: ADBManager):
        super().__init__(parent)
        self._adb = adb
        self._recording = False
        self._proc = None
        self._events: list[str] = []
        self._macros: list[dict] = []

        self.title("Gesture Automation — USHCODEX Android Debugger")
        self.configure(bg=BRAND["bg"])
        self.geometry("800x600")
        self.resizable(True, True)
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Tab 1: getevent recorder ──────────────────────────────────────────
        rec_tab = ttk.Frame(nb)
        nb.add(rec_tab, text="  getevent Recorder  ")
        self._build_recorder(rec_tab)

        # ── Tab 2: Tap / Swipe Macros ─────────────────────────────────────────
        macro_tab = ttk.Frame(nb)
        nb.add(macro_tab, text="  Tap/Swipe Macros  ")
        self._build_macros(macro_tab)

        # ── Tab 3: Input Devices ──────────────────────────────────────────────
        dev_tab = ttk.Frame(nb)
        nb.add(dev_tab, text="  Input Devices  ")
        self._build_devices(dev_tab)

    # ── Recorder ──────────────────────────────────────────────────────────────

    def _build_recorder(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # Device selection
        hdr = ttk.Frame(parent)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        ttk.Label(hdr, text="Input device:").pack(side="left", padx=4)
        self._dev_var = tk.StringVar(value="/dev/input/event0")
        ttk.Entry(hdr, textvariable=self._dev_var, width=28).pack(side="left", padx=4)
        ttk.Button(hdr, text="Detect Devices", command=self._detect_devices
                   ).pack(side="left", padx=4)

        # Buttons
        btn_row = ttk.Frame(parent)
        btn_row.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        self._rec_btn = ttk.Button(btn_row, text="● Start Recording",
                                    style="Danger.TButton",
                                    command=self._toggle_record)
        self._rec_btn.pack(side="left", padx=4)
        ttk.Button(btn_row, text="▶ Replay",
                   style="Success.TButton",
                   command=self._replay).pack(side="left", padx=4)
        ttk.Button(btn_row, text="💾 Save Script",
                   command=self._save_script).pack(side="left", padx=4)
        ttk.Button(btn_row, text="📂 Load Script",
                   command=self._load_script).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🗑 Clear",
                   style="Danger.TButton",
                   command=self._clear_events).pack(side="left", padx=4)

        # Event log
        self._event_text = tk.Text(parent, state="disabled",
                                    bg=BRAND["bg3"], fg=BRAND["fg"],
                                    font=FONTS["mono_sm"], relief="flat")
        self._event_text.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0,4))
        sb = ttk.Scrollbar(parent, command=self._event_text.yview)
        sb.grid(row=2, column=1, sticky="ns", pady=(0,4))
        self._event_text.configure(yscrollcommand=sb.set)

        ttk.Label(parent,
                  text="Tip: getevent captures raw Linux input events. "
                       "Replay them exactly with sendevent for precise automation.",
                  font=FONTS["small"], foreground=BRAND["fg2"]
                  ).grid(row=3, column=0, sticky="w", padx=8, pady=4)

    def _toggle_record(self):
        if self._recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        dev = self._dev_var.get().strip()
        if not dev:
            messagebox.showwarning("UAD", "Select an input device first.")
            return
        self._recording = True
        self._rec_btn.configure(text="⏹ Stop Recording", style="Warning.TButton")
        self._events = []

        serial_args = ["-s", self._adb.serial] if self._adb.serial else []
        self._proc = subprocess.Popen(
            [ADB] + serial_args + ["shell", "getevent", "-lt", dev],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        threading.Thread(target=self._read_events, daemon=True).start()

    def _read_events(self):
        for line in self._proc.stdout:
            line = line.rstrip()
            self._events.append(line)
            self._append_event(line)

    def _stop_record(self):
        self._recording = False
        self._rec_btn.configure(text="● Start Recording", style="Danger.TButton")
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def _append_event(self, line: str):
        self._event_text.configure(state="normal")
        self._event_text.insert("end", line + "\n")
        self._event_text.see("end")
        self._event_text.configure(state="disabled")

    def _replay(self):
        if not self._events:
            messagebox.showinfo("UAD", "No events recorded yet.")
            return
        dev = self._dev_var.get().strip()
        events = self._parse_events(self._events, dev)
        if not events:
            messagebox.showwarning("UAD", "No parseable events found.")
            return
        threading.Thread(target=self._run_replay, args=(events,), daemon=True).start()

    def _parse_events(self, raw_lines: list[str], device: str) -> list[tuple]:
        """Parse getevent -lt output → list of (device, type_hex, code_hex, value_hex)."""
        parsed = []
        for line in raw_lines:
            # Format: [timestamp] /dev/input/eventX: EV_* CODE VALUE
            m = re.search(
                r'(\/dev\/input\/\S+):\s+(\w+)\s+(\w+)\s+(\w+)', line)
            if m:
                dev = m.group(1)
                etype = m.group(2)
                ecode = m.group(3)
                evalue = m.group(4)
                parsed.append((dev, etype, ecode, evalue))
        return parsed

    def _run_replay(self, events: list[tuple]):
        serial_args = ["-s", self._adb.serial] if self._adb.serial else []
        for dev, etype, ecode, evalue in events:
            subprocess.run(
                [ADB] + serial_args + ["shell", "sendevent", dev,
                                        etype, ecode, evalue],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        self._append_event("[Replay done]")

    def _save_script(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Text", "*.txt")],
            title="Save Gesture Script")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"events": self._events,
                       "device": self._dev_var.get()}, f, indent=2)

    def _load_script(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Text", "*.txt")],
            title="Load Gesture Script")
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._events = data.get("events", [])
        self._dev_var.set(data.get("device", self._dev_var.get()))
        self._event_text.configure(state="normal")
        self._event_text.delete("1.0", "end")
        for line in self._events:
            self._event_text.insert("end", line + "\n")
        self._event_text.configure(state="disabled")

    def _clear_events(self):
        self._events = []
        self._event_text.configure(state="normal")
        self._event_text.delete("1.0", "end")
        self._event_text.configure(state="disabled")

    def _detect_devices(self):
        def _do():
            return self._adb.list_input_devices()
        def _show(raw):
            # Extract device paths
            devs = re.findall(r'(\/dev\/input\/event\d+)', raw)
            if devs:
                self._dev_var.set(devs[0])
                messagebox.showinfo(
                    "Input Devices",
                    "Found:\n" + "\n".join(devs) +
                    "\n\nFirst one selected. Change if needed.")
            else:
                messagebox.showinfo("Input Devices", raw[:800])
        self._adb.run_async(_do, callback=_show)

    # ── Tap/Swipe Macros ──────────────────────────────────────────────────────

    def _build_macros(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # Quick input helpers
        qf = ttk.LabelFrame(parent, text=" Quick Actions ")
        qf.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        qf.columnconfigure((0,1,2,3), weight=1)

        # Tap
        ttk.Label(qf, text="Tap X:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self._tap_x = tk.StringVar(value="540")
        ttk.Entry(qf, textvariable=self._tap_x, width=7).grid(row=0, column=1, sticky="w")
        ttk.Label(qf, text="Y:").grid(row=0, column=2, sticky="e")
        self._tap_y = tk.StringVar(value="960")
        ttk.Entry(qf, textvariable=self._tap_y, width=7).grid(row=0, column=3, sticky="w")
        ttk.Button(qf, text="Tap", style="Primary.TButton",
                   command=self._do_tap).grid(row=0, column=4, padx=4)

        # Swipe
        ttk.Label(qf, text="Swipe X1:").grid(row=1,column=0, padx=4, pady=4, sticky="e")
        self._sx1 = tk.StringVar(value="200")
        self._sy1 = tk.StringVar(value="960")
        self._sx2 = tk.StringVar(value="800")
        self._sy2 = tk.StringVar(value="960")
        self._sdur = tk.StringVar(value="300")
        for col, var in enumerate([self._sx1, self._sy1, self._sx2, self._sy2]):
            ttk.Entry(qf, textvariable=var, width=7).grid(row=1, column=col+1, sticky="w")
        ttk.Label(qf, text="Duration ms:").grid(row=1, column=5, sticky="e")
        ttk.Entry(qf, textvariable=self._sdur, width=6).grid(row=1, column=6, sticky="w")
        ttk.Button(qf, text="Swipe", style="Primary.TButton",
                   command=self._do_swipe).grid(row=1, column=7, padx=4)

        # Macro list
        btn_row = ttk.Frame(parent)
        btn_row.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        ttk.Button(btn_row, text="+ Add Tap Step", command=self._add_tap).pack(side="left", padx=4)
        ttk.Button(btn_row, text="+ Add Swipe Step", command=self._add_swipe).pack(side="left", padx=4)
        ttk.Button(btn_row, text="+ Add Delay", command=self._add_delay).pack(side="left", padx=4)
        ttk.Button(btn_row, text="+ Add Keyevent", command=self._add_key).pack(side="left", padx=4)
        ttk.Button(btn_row, text="▶ Run Macro", style="Success.TButton",
                   command=self._run_macro).pack(side="left", padx=4)
        ttk.Button(btn_row, text="💾 Save", command=self._save_macro).pack(side="left", padx=4)
        ttk.Button(btn_row, text="📂 Load", command=self._load_macro).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🗑 Clear", style="Danger.TButton",
                   command=self._clear_macro).pack(side="left", padx=4)

        self._macro_text = tk.Text(parent, bg=BRAND["bg3"], fg=BRAND["fg"],
                                    font=FONTS["mono_sm"], relief="flat")
        self._macro_text.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        sb = ttk.Scrollbar(parent, command=self._macro_text.yview)
        sb.grid(row=2, column=1, sticky="ns", pady=4)
        self._macro_text.configure(yscrollcommand=sb.set)

    def _do_tap(self):
        x, y = int(self._tap_x.get()), int(self._tap_y.get())
        self._adb.run_async(lambda: self._adb.tap(x, y))

    def _do_swipe(self):
        x1,y1,x2,y2 = (int(self._sx1.get()), int(self._sy1.get()),
                        int(self._sx2.get()), int(self._sy2.get()))
        dur = int(self._sdur.get())
        self._adb.run_async(lambda: self._adb.swipe(x1,y1,x2,y2,dur))

    def _add_tap(self):
        self._macro_text.insert("end",
            f'tap {self._tap_x.get()} {self._tap_y.get()}\n')

    def _add_swipe(self):
        self._macro_text.insert("end",
            f'swipe {self._sx1.get()} {self._sy1.get()} '
            f'{self._sx2.get()} {self._sy2.get()} {self._sdur.get()}\n')

    def _add_delay(self):
        from tkinter import simpledialog
        ms = simpledialog.askinteger("Delay", "Delay in milliseconds:", minvalue=1, maxvalue=30000)
        if ms:
            self._macro_text.insert("end", f'delay {ms}\n')

    def _add_key(self):
        from tkinter import simpledialog
        code = simpledialog.askstring("Keyevent", "KEYCODE or number (e.g. 4 or KEYCODE_BACK):")
        if code:
            self._macro_text.insert("end", f'keyevent {code}\n')

    def _run_macro(self):
        script = self._macro_text.get("1.0", "end").strip()
        if not script:
            return
        threading.Thread(target=self._exec_macro, args=(script,), daemon=True).start()

    def _exec_macro(self, script: str):
        for line in script.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cmd = parts[0].lower()
            try:
                if cmd == "tap":
                    self._adb.tap(int(parts[1]), int(parts[2]))
                elif cmd == "swipe":
                    dur = int(parts[5]) if len(parts) > 5 else 300
                    self._adb.swipe(int(parts[1]), int(parts[2]),
                                    int(parts[3]), int(parts[4]), dur)
                elif cmd == "delay":
                    time.sleep(int(parts[1]) / 1000)
                elif cmd == "keyevent":
                    self._adb.keyevent(parts[1])
                elif cmd == "text":
                    self._adb.text(" ".join(parts[1:]))
            except Exception as e:
                print(f"[Macro] Error on '{line}': {e}")

    def _save_macro(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if path:
            with open(path, "w") as f:
                f.write(self._macro_text.get("1.0", "end"))

    def _load_macro(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if path:
            with open(path) as f:
                self._macro_text.delete("1.0", "end")
                self._macro_text.insert("1.0", f.read())

    def _clear_macro(self):
        self._macro_text.delete("1.0", "end")

    # ── Input Devices ─────────────────────────────────────────────────────────

    def _build_devices(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Button(parent, text="⟳ Refresh Input Devices",
                   style="Primary.TButton",
                   command=self._refresh_devices).grid(row=0, column=0,
                                                        sticky="w", padx=10, pady=8)
        self._dev_text = tk.Text(parent, state="disabled",
                                  bg=BRAND["bg3"], fg=BRAND["fg"],
                                  font=FONTS["mono_sm"], relief="flat")
        self._dev_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        sb = ttk.Scrollbar(parent, command=self._dev_text.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self._dev_text.configure(yscrollcommand=sb.set)
        self._refresh_devices()

    def _refresh_devices(self):
        def _do():
            return self._adb.list_input_devices()
        def _show(raw):
            self._dev_text.configure(state="normal")
            self._dev_text.delete("1.0", "end")
            self._dev_text.insert("1.0", raw)
            self._dev_text.configure(state="disabled")
        self._adb.run_async(_do, callback=_show,
            error_cb=lambda e: None)
