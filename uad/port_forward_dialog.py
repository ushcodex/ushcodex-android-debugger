"""
USHCODEX Android Debugger - Port Forwarding Dialog
ADB port forwarding / reverse tunnel management.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from .theme import BRAND, FONTS
from .adb_manager import ADBManager


class PortForwardDialog(tk.Toplevel):
    """Manage ADB forward / reverse rules for the selected device."""

    def __init__(self, parent, adb: ADBManager):
        super().__init__(parent)
        self._adb = adb

        self.title("Port Forwarding — USHCODEX Android Debugger")
        self.configure(bg=BRAND["bg"])
        self.geometry("560x460")
        self.resizable(True, True)
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        fwd = ttk.Frame(nb)
        nb.add(fwd, text="  Forward (PC → Device)  ")
        self._build_forward(fwd)

        rev = ttk.Frame(nb)
        nb.add(rev, text="  Reverse (Device → PC)  ")
        self._build_reverse(rev)

    # ── Forward tab ───────────────────────────────────────────────────────────

    def _build_forward(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        form = ttk.Frame(parent)
        form.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        ttk.Label(form, text="Local (PC):", style="TLabel").grid(
            row=0, column=0, padx=4, pady=4, sticky="w")
        self._local_var = tk.StringVar(value="tcp:8080")
        ttk.Entry(form, textvariable=self._local_var, width=18).grid(
            row=0, column=1, padx=4)
        ttk.Label(form, text="Remote (device):", style="TLabel").grid(
            row=0, column=2, padx=4)
        self._remote_var = tk.StringVar(value="tcp:8080")
        ttk.Entry(form, textvariable=self._remote_var, width=18).grid(
            row=0, column=3, padx=4)
        ttk.Label(form, text="e.g. tcp:8080, localabstract:foo, jdwp:123",
                  style="Sub.TLabel", font=FONTS["small"]).grid(
            row=1, column=0, columnspan=4, sticky="w", padx=4)

        ttk.Button(form, text="➕ Add Rule", style="Primary.TButton",
                   command=self._add_forward).grid(row=2, column=0, columnspan=2,
                                                   padx=4, pady=6, sticky="ew")
        ttk.Button(form, text="🗑 Remove All", style="Danger.TButton",
                   command=self._remove_forwards).grid(row=2, column=2,
                                                       columnspan=2, padx=4,
                                                       pady=6, sticky="ew")

        lst = ttk.Frame(parent)
        lst.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        lst.columnconfigure(0, weight=1)
        lst.rowconfigure(0, weight=1)
        self._fwd_list = tk.Listbox(lst, bg=BRAND["bg3"], fg=BRAND["fg"],
                                    selectbackground=BRAND["sel"],
                                    relief="flat", font=FONTS["mono_sm"],
                                    highlightthickness=0)
        self._fwd_list.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lst, command=self._fwd_list.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._fwd_list.configure(yscrollcommand=sb.set)
        self.refresh_forwards()

    def _add_forward(self):
        local, remote = self._local_var.get().strip(), self._remote_var.get().strip()
        if not local or not remote:
            messagebox.showwarning("UAD", "Enter both local and remote specs.")
            return
        self._adb.run_async(
            lambda: self._adb.forward(local, remote),
            callback=lambda _: self.refresh_forwards(),
            error_cb=lambda e: messagebox.showerror("Forward Error", str(e)))

    def _remove_forwards(self):
        self._adb.run_async(
            lambda: self._adb.forward_remove_all(),
            callback=lambda _: self.refresh_forwards(),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

    def refresh_forwards(self):
        def _do():
            try:
                return self._adb.forward_list() or "(no rules)"
            except Exception as e:
                return f"(error: {e})"
        self._adb.run_async(_do, callback=self._fill_fwd)

    def _fill_fwd(self, text: str):
        self._fwd_list.delete(0, tk.END)
        for line in text.splitlines():
            self._fwd_list.insert(tk.END, line)

    # ── Reverse tab ───────────────────────────────────────────────────────────

    def _build_reverse(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        form = ttk.Frame(parent)
        form.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

        ttk.Label(form, text="Remote (device):", style="TLabel").grid(
            row=0, column=0, padx=4, pady=4, sticky="w")
        self._rev_remote_var = tk.StringVar(value="tcp:8080")
        ttk.Entry(form, textvariable=self._rev_remote_var, width=18).grid(
            row=0, column=1, padx=4)
        ttk.Label(form, text="Local (PC):", style="TLabel").grid(
            row=0, column=2, padx=4)
        self._rev_local_var = tk.StringVar(value="tcp:8080")
        ttk.Entry(form, textvariable=self._rev_local_var, width=18).grid(
            row=0, column=3, padx=4)

        ttk.Button(form, text="➕ Add Rule", style="Primary.TButton",
                   command=self._add_reverse).grid(row=1, column=0, columnspan=2,
                                                   padx=4, pady=6, sticky="ew")

        lst = ttk.Frame(parent)
        lst.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        lst.columnconfigure(0, weight=1)
        lst.rowconfigure(0, weight=1)
        self._rev_list = tk.Listbox(lst, bg=BRAND["bg3"], fg=BRAND["fg"],
                                    selectbackground=BRAND["sel"],
                                    relief="flat", font=FONTS["mono_sm"],
                                    highlightthickness=0)
        self._rev_list.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lst, command=self._rev_list.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._rev_list.configure(yscrollcommand=sb.set)
        self.refresh_reverses()

    def _add_reverse(self):
        remote, local = (self._rev_remote_var.get().strip(),
                         self._rev_local_var.get().strip())
        if not remote or not local:
            messagebox.showwarning("UAD", "Enter both specs.")
            return
        self._adb.run_async(
            lambda: self._adb.reverse(remote, local),
            callback=lambda _: self.refresh_reverses(),
            error_cb=lambda e: messagebox.showerror("Reverse Error", str(e)))

    def refresh_reverses(self):
        def _do():
            try:
                return self._adb.reverse_list() or "(no rules)"
            except Exception as e:
                return f"(error: {e})"
        self._adb.run_async(_do, callback=self._fill_rev)

    def _fill_rev(self, text: str):
        self._rev_list.delete(0, tk.END)
        for line in text.splitlines():
            self._rev_list.insert(tk.END, line)
