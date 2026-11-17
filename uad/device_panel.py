"""
USHCODEX Android Debugger - Device Panel
Device list, connection controls, and device info card.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from typing import Callable, Optional

from .theme import BRAND, FONTS
from .adb_manager import ADBManager, ADBError
from .icons import IconSet


class DevicePanel(ttk.Frame):
    """Left sidebar: device list + connection controls."""

    def __init__(self, parent, adb: ADBManager, icons: IconSet,
                 on_device_selected: Callable, settings):
        super().__init__(parent, style="Sidebar.TFrame")
        self._adb = adb
        self._icons = icons
        self._on_selected = on_device_selected
        self._settings = settings
        self._refresh_job = None
        self._build()
        self.refresh_devices()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        row = 0

        # Header
        hdr = ttk.Frame(self, style="Sidebar.TFrame")
        hdr.grid(row=row, column=0, sticky="ew", padx=10, pady=(12, 4))
        ttk.Label(hdr, text="DEVICES", style="Panel.TLabel",
                  font=FONTS["h3"]).pack(side="left")
        ttk.Button(hdr, text="⟳", style="TButton", width=3,
                   command=self.refresh_devices).pack(side="right")
        row += 1

        # Device list
        list_frame = ttk.Frame(self, style="Sidebar.TFrame")
        list_frame.grid(row=row, column=0, sticky="nsew", padx=6, pady=2)
        list_frame.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)
        row += 1

        self._listbox = tk.Listbox(
            list_frame, selectmode="single",
            bg=BRAND["bg3"], fg=BRAND["fg"], selectbackground=BRAND["sel"],
            selectforeground=BRAND["accent"], relief="flat", bd=0,
            font=FONTS["body"], activestyle="none", highlightthickness=0,
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame, command=self._listbox.yview)
        sb.pack(side="right", fill="y")
        self._listbox.configure(yscrollcommand=sb.set)
        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Status badge
        self._status_lbl = ttk.Label(self, text="No device", style="Warning.TLabel",
                                      font=FONTS["small"])
        self._status_lbl.grid(row=row, column=0, sticky="w", padx=10, pady=2)
        row += 1

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, sticky="ew", padx=6, pady=4)
        row += 1

        # Connect section
        conn = ttk.LabelFrame(self, text=" WiFi Connect ", style="TLabelframe")
        conn.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
        conn.columnconfigure(0, weight=1)
        row += 1

        ttk.Label(conn, text="IP Address", style="TLabel",
                  font=FONTS["small"]).grid(row=0, column=0, sticky="w", padx=6, pady=2)
        self._ip_var = tk.StringVar(value=self._settings.get("last_wifi_ip", ""))
        ip_entry = ttk.Entry(conn, textvariable=self._ip_var, style="TEntry")
        ip_entry.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))

        ttk.Label(conn, text="Port", style="TLabel",
                  font=FONTS["small"]).grid(row=2, column=0, sticky="w", padx=6)
        self._port_var = tk.StringVar(value="5555")
        ttk.Entry(conn, textvariable=self._port_var, style="TEntry",
                  width=8).grid(row=3, column=0, sticky="w", padx=6, pady=(0, 4))

        btn_row = ttk.Frame(conn)
        btn_row.grid(row=4, column=0, sticky="ew", padx=6, pady=(0, 6))
        ttk.Button(btn_row, text="Connect", style="Primary.TButton",
                   command=self._wifi_connect).pack(side="left", padx=(0, 4))
        ttk.Button(btn_row, text="Pair", style="Accent.TButton",
                   command=self._wifi_pair).pack(side="left")

        # ADB wireless shortcut
        ttk.Button(self, text="Enable WiFi ADB (tcpip 5555)",
                   style="TButton", command=self._enable_tcpip
                   ).grid(row=row, column=0, sticky="ew", padx=8, pady=2)
        row += 1

        ttk.Button(self, text="Disconnect All",
                   style="Danger.TButton", command=self._disconnect_all
                   ).grid(row=row, column=0, sticky="ew", padx=8, pady=2)
        row += 1

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, sticky="ew", padx=6, pady=4)
        row += 1

        # Device info
        info = ttk.LabelFrame(self, text=" Device Info ", style="TLabelframe")
        info.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
        info.columnconfigure(1, weight=1)
        row += 1
        self._info_vars = {}
        for i, key in enumerate(["Model", "Android", "SDK", "Battery", "Storage"]):
            ttk.Label(info, text=key + ":", style="TLabel",
                      font=FONTS["small"], foreground=BRAND["fg2"]
                      ).grid(row=i, column=0, sticky="w", padx=6, pady=1)
            v = tk.StringVar(value="—")
            self._info_vars[key] = v
            ttk.Label(info, textvariable=v, style="TLabel",
                      font=FONTS["small"]).grid(row=i, column=1, sticky="w", padx=4)

        # Auto-refresh toggle
        self._auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="Auto-refresh devices (3s)",
                        variable=self._auto_var, style="TCheckbutton",
                        command=self._toggle_auto).grid(
            row=row, column=0, sticky="w", padx=10, pady=4)
        row += 1

        # Start auto-refresh
        self._schedule_refresh()

    # ── Device List ───────────────────────────────────────────────────────────

    def refresh_devices(self):
        def _do():
            try:
                return self._adb.list_devices()
            except Exception as e:
                return []
        self._adb.run_async(_do, callback=self._update_list)

    def _update_list(self, devices: list):
        self._listbox.delete(0, tk.END)
        self._devices = devices
        if not devices:
            self._status_lbl.configure(text="No devices found", style="Warning.TLabel")
            self._update_info({})
            return
        for d in devices:
            icon = "📱" if d["transport"] == "USB" else "📶"
            label = f"  {icon}  {d['model']}  [{d['serial']}]  {d['state']}"
            self._listbox.insert(tk.END, label)

        # Auto-select last known or first
        last = self._settings.get("last_device")
        idx = 0
        for i, d in enumerate(devices):
            if d["serial"] == last:
                idx = i
                break
        self._listbox.selection_set(idx)
        self._listbox.event_generate("<<ListboxSelect>>")

    def _on_listbox_select(self, _event=None):
        sel = self._listbox.curselection()
        if not sel or not hasattr(self, "_devices"):
            return
        d = self._devices[sel[0]]
        self._adb.select(d["serial"])
        self._settings.set("last_device", d["serial"])
        state = d["state"]
        if state == "device":
            self._status_lbl.configure(text=f"● {d['model']}  ({d['transport']})",
                                       style="Success.TLabel")
        else:
            self._status_lbl.configure(text=f"⚠ {d['serial']}  {state}",
                                       style="Warning.TLabel")
        self._on_selected(d)
        self._refresh_device_info()

    def _refresh_device_info(self):
        def _do():
            if not self._adb.serial:
                return {}
            return self._adb.device_info()
        self._adb.run_async(_do, callback=self._update_info)

    def _update_info(self, info: dict):
        mapping = {
            "Model":   info.get("model",   "—"),
            "Android": info.get("android", "—"),
            "SDK":     info.get("sdk",     "—"),
            "Battery": info.get("battery", "—"),
            "Storage": info.get("storage", "—"),
        }
        for k, v in mapping.items():
            if k in self._info_vars:
                self._info_vars[k].set(v)

    # ── WiFi ──────────────────────────────────────────────────────────────────

    def _wifi_connect(self):
        ip = self._ip_var.get().strip()
        port = self._port_var.get().strip() or "5555"
        if not ip:
            messagebox.showwarning("UAD", "Enter an IP address first.")
            return
        self._settings.set("last_wifi_ip", ip)
        def _do():
            return self._adb.connect(ip, int(port))
        self._adb.run_async(_do,
            callback=lambda r: self._post_connect(r),
            error_cb=lambda e: messagebox.showerror("Connect Error", str(e)))

    def _post_connect(self, result: str):
        messagebox.showinfo("WiFi Connect", result)
        self.refresh_devices()

    def _wifi_pair(self):
        ip = self._ip_var.get().strip()
        if not ip:
            messagebox.showwarning("UAD", "Enter IP address for pairing.")
            return
        pair_port = simpledialog.askstring("Pair Port",
            "Enter pairing port (from phone's Wireless debugging screen):", parent=self)
        code = simpledialog.askstring("Pair Code",
            "Enter 6-digit pairing code:", parent=self)
        if not pair_port or not code:
            return
        def _do():
            return self._adb.pair(ip, int(pair_port), code)
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo("Pair", r),
            error_cb=lambda e: messagebox.showerror("Pair Error", str(e)))

    def _enable_tcpip(self):
        def _do():
            return self._adb.tcpip(5555)
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo(
                "WiFi ADB", f"Done: {r}\nNow connect with the device's IP."),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

    def _disconnect_all(self):
        def _do():
            return self._adb.disconnect()
        self._adb.run_async(_do,
            callback=lambda r: (messagebox.showinfo("Disconnected", r),
                                self.refresh_devices()))

    # ── Auto-refresh ──────────────────────────────────────────────────────────

    def _toggle_auto(self):
        if self._auto_var.get():
            self._schedule_refresh()

    def _schedule_refresh(self):
        if self._auto_var.get():
            self.refresh_devices()
            self._refresh_job = self.after(3000, self._schedule_refresh)

    def destroy(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        super().destroy()
