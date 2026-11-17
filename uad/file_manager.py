"""
USHCODEX Android Debugger - File Manager Tab
Full ADB file browser with upload, download, delete, rename, mkdir, preview.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import threading
from pathlib import Path, PurePosixPath

from .theme import BRAND, FONTS
from .adb_manager import ADBManager, ADBError


FAVORITES = [
    "/sdcard",
    "/sdcard/DCIM",
    "/sdcard/Download",
    "/sdcard/Pictures",
    "/sdcard/WhatsApp",
    "/sdcard/Android/data",
]


class FileManagerTab(ttk.Frame):
    """ADB file manager — browse, upload, download, delete, rename."""

    def __init__(self, parent, adb: ADBManager):
        super().__init__(parent, style="TFrame")
        self._adb = adb
        self._path = "/sdcard"
        self._history: list[str] = ["/sdcard"]
        self._hist_idx = 0
        self._build()
        self._navigate("/sdcard")

    def _build(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Toolbar ───────────────────────────────────────────────────────────
        tb = ttk.Frame(self, style="Panel.TFrame")
        tb.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

        self._back_btn = ttk.Button(tb, text="◀", width=3, command=self._go_back)
        self._back_btn.pack(side="left", padx=4, pady=4)
        self._fwd_btn = ttk.Button(tb, text="▶", width=3, command=self._go_fwd)
        self._fwd_btn.pack(side="left", padx=2, pady=4)
        ttk.Button(tb, text="↑ Up", command=self._go_up).pack(side="left", padx=4, pady=4)
        ttk.Button(tb, text="⟳ Refresh", command=self._refresh).pack(side="left", padx=4)

        self._path_var = tk.StringVar(value="/sdcard")
        path_entry = ttk.Entry(tb, textvariable=self._path_var, font=FONTS["mono"])
        path_entry.pack(side="left", fill="x", expand=True, padx=8, pady=4)
        path_entry.bind("<Return>", lambda _: self._navigate(self._path_var.get()))

        ttk.Button(tb, text="Go", style="Primary.TButton",
                   command=lambda: self._navigate(self._path_var.get())
                   ).pack(side="left", padx=4)

        # ── Sidebar: favorites ────────────────────────────────────────────────
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=160)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        ttk.Label(sidebar, text="Favorites", style="Panel.TLabel",
                  font=FONTS["h3"]).pack(anchor="w", padx=8, pady=6)
        for fav in FAVORITES:
            name = fav.split("/")[-1] or "/"
            ttk.Button(sidebar, text=f"  📁  {name}", style="TButton",
                       command=lambda p=fav: self._navigate(p)
                       ).pack(fill="x", padx=4, pady=1)

        # ── Main area ─────────────────────────────────────────────────────────
        main = ttk.Frame(self, style="TFrame")
        main.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        # Treeview
        cols = ("name", "size", "date", "perms")
        self._tree = ttk.Treeview(main, columns=cols, show="headings",
                                   selectmode="extended")
        self._tree.heading("name",  text="Name",        anchor="w")
        self._tree.heading("size",  text="Size",        anchor="e")
        self._tree.heading("date",  text="Date",        anchor="w")
        self._tree.heading("perms", text="Permissions", anchor="w")
        self._tree.column("name",  width=320, stretch=True)
        self._tree.column("size",  width=90,  stretch=False, anchor="e")
        self._tree.column("date",  width=140, stretch=False)
        self._tree.column("perms", width=100, stretch=False)
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(main, command=self._tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(main, orient="horizontal", command=self._tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self._tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self._tree.bind("<Double-1>", self._on_dbl_click)
        self._tree.bind("<Button-3>", self._on_right_click)

        # ── Action bar ────────────────────────────────────────────────────────
        abar = ttk.Frame(self, style="Panel.TFrame")
        abar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

        for txt, cmd in [
            ("⬇ Download",  self._download),
            ("⬆ Upload",    self._upload),
            ("📁 New Folder", self._mkdir),
            ("✏ Rename",   self._rename),
            ("🗑 Delete",   self._delete),
            ("ℹ Stat",      self._stat),
        ]:
            ttk.Button(abar, text=txt, command=cmd).pack(side="left", padx=4, pady=4)

        # Status bar
        self._status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status_var, style="Sub.TLabel"
                  ).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        # Right-click menu
        self._ctx = tk.Menu(self, tearoff=0, bg=BRAND["bg2"], fg=BRAND["fg"])
        for txt, cmd in [
            ("Download", self._download),
            ("Upload here", self._upload),
            ("New Folder", self._mkdir),
            ("Rename", self._rename),
            ("Delete", self._delete),
            ("Properties / Stat", self._stat),
        ]:
            self._ctx.add_command(label=txt, command=cmd)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, path: str):
        path = path.strip()
        if not path:
            return
        self._path = path
        self._path_var.set(path)
        self._status_var.set(f"Loading {path} …")

        def _do():
            return self._adb.ls(path)

        self._adb.run_async(_do,
            callback=lambda entries: self._populate(entries, path),
            error_cb=lambda e: self._status_var.set(f"Error: {e}"))

        # History
        if self._hist_idx < len(self._history) - 1:
            self._history = self._history[:self._hist_idx+1]
        self._history.append(path)
        self._hist_idx = len(self._history) - 1

    def _refresh(self):
        self._navigate(self._path)

    def _go_up(self):
        parent = str(PurePosixPath(self._path).parent)
        if parent != self._path:
            self._navigate(parent)

    def _go_back(self):
        if self._hist_idx > 0:
            self._hist_idx -= 1
            self._navigate_no_history(self._history[self._hist_idx])

    def _go_fwd(self):
        if self._hist_idx < len(self._history) - 1:
            self._hist_idx += 1
            self._navigate_no_history(self._history[self._hist_idx])

    def _navigate_no_history(self, path: str):
        self._path = path
        self._path_var.set(path)
        def _do():
            return self._adb.ls(path)
        self._adb.run_async(_do,
            callback=lambda e: self._populate(e, path),
            error_cb=lambda e: self._status_var.set(f"Error: {e}"))

    def _populate(self, entries: list[dict], path: str):
        self._tree.delete(*self._tree.get_children())
        self._entries = entries
        for e in sorted(entries, key=lambda x: (not x["is_dir"], x["name"].lower())):
            icon = "📁" if e["is_dir"] else "📄"
            self._tree.insert("", "end", values=(
                f"{icon}  {e['name']}",
                e["size"],
                e["date"],
                e["perms"],
            ), tags=("dir" if e["is_dir"] else "file",))
        self._tree.tag_configure("dir",  foreground=BRAND["accent"])
        self._tree.tag_configure("file", foreground=BRAND["fg"])
        self._status_var.set(f"{len(entries)} items in {path}")

    def _selected_names(self) -> list[str]:
        names = []
        for iid in self._tree.selection():
            vals = self._tree.item(iid, "values")
            # strip icon prefix
            names.append(vals[0].split("  ", 1)[-1].strip())
        return names

    def _selected_paths(self) -> list[str]:
        return [f"{self._path.rstrip('/')}/{n}" for n in self._selected_names()]

    # ── Events ───────────────────────────────────────────────────────────────

    def _on_dbl_click(self, _event=None):
        names = self._selected_names()
        if not names:
            return
        name = names[0]
        for e in self._entries:
            if e["name"] == name and e["is_dir"]:
                self._navigate(f"{self._path.rstrip('/')}/{name}")
                return

    def _on_right_click(self, event):
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
        self._ctx.post(event.x_root, event.y_root)

    # ── File Operations ───────────────────────────────────────────────────────

    def _download(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showwarning("UAD", "Select at least one item.")
            return
        dest = filedialog.askdirectory(title="Download to…")
        if not dest:
            return
        def _do():
            results = []
            for p in paths:
                results.append(self._adb.pull(p, dest))
            return results
        self._adb.run_async(_do,
            callback=lambda r: self._status_var.set(f"Downloaded {len(paths)} item(s) to {dest}"),
            error_cb=lambda e: messagebox.showerror("Download Error", str(e)))

    def _upload(self):
        files = filedialog.askopenfilenames(title="Select files to upload")
        if not files:
            return
        def _do():
            for f in files:
                remote = f"{self._path.rstrip('/')}/{os.path.basename(f)}"
                self._adb.push(f, remote)
            return len(files)
        self._adb.run_async(_do,
            callback=lambda n: (self._status_var.set(f"Uploaded {n} file(s)"),
                                self._refresh()),
            error_cb=lambda e: messagebox.showerror("Upload Error", str(e)))

    def _mkdir(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self)
        if not name:
            return
        remote = f"{self._path.rstrip('/')}/{name}"
        self._adb.run_async(lambda: self._adb.mkdir(remote),
            callback=lambda _: self._refresh(),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))

    def _rename(self):
        names = self._selected_names()
        if len(names) != 1:
            messagebox.showwarning("UAD", "Select exactly one item to rename.")
            return
        old = f"{self._path.rstrip('/')}/{names[0]}"
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=names[0])
        if not new_name:
            return
        new = f"{self._path.rstrip('/')}/{new_name}"
        self._adb.run_async(lambda: self._adb.rename(old, new),
            callback=lambda _: self._refresh(),
            error_cb=lambda e: messagebox.showerror("Rename Error", str(e)))

    def _delete(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showwarning("UAD", "Select at least one item.")
            return
        if not messagebox.askyesno("Delete",
                f"Delete {len(paths)} item(s)? This cannot be undone."):
            return
        def _do():
            for p in paths:
                self._adb.delete(p, recursive=True)
        self._adb.run_async(_do,
            callback=lambda _: self._refresh(),
            error_cb=lambda e: messagebox.showerror("Delete Error", str(e)))

    def _stat(self):
        paths = self._selected_paths()
        if not paths:
            return
        def _do():
            return self._adb.stat(paths[0])
        self._adb.run_async(_do,
            callback=lambda r: messagebox.showinfo("Properties", r),
            error_cb=lambda e: messagebox.showerror("Error", str(e)))
