"""
USHCODEX Android Debugger - Theme & Color System
USHCODEX branding: Orange #f7931e → Purple #472abe gradient
"""
import tkinter as tk
from tkinter import ttk

# ── Brand Colours ──────────────────────────────────────────────────────────────
BRAND = {
    "orange":       "#f7931e",
    "purple":       "#472abe",
    "mid":          "#a56267",   # midpoint of gradient
    "bg":           "#0f0f1a",   # near-black background
    "bg2":          "#171727",   # slightly lighter panel bg
    "bg3":          "#1e1e30",   # card/frame bg
    "fg":           "#e8e8f0",   # primary text
    "fg2":          "#a0a0b8",   # secondary text
    "accent":       "#f7931e",   # accent == orange
    "accent2":      "#7b3fce",   # second accent (violet)
    "success":      "#3ddc84",   # green – connected
    "warning":      "#ffb347",   # amber – warning
    "danger":       "#ff4f5e",   # red – disconnect / error
    "border":       "#2a2a3e",   # subtle border
    "highlight":    "#2e2e45",   # hover highlight
    "sel":          "#3a2a5a",   # selection colour
    "btn_primary":  "#f7931e",
    "btn_hover":    "#e8820f",
    "btn_danger":   "#ff4f5e",
    "btn_success":  "#3ddc84",
    "btn_neutral":  "#2a2a3e",
}

FONT_FAMILY = "Segoe UI"
FONTS = {
    "h1":     (FONT_FAMILY, 18, "bold"),
    "h2":     (FONT_FAMILY, 14, "bold"),
    "h3":     (FONT_FAMILY, 11, "bold"),
    "body":   (FONT_FAMILY, 10),
    "small":  (FONT_FAMILY,  9),
    "mono":   ("Consolas",  10),
    "mono_sm":("Consolas",   9),
    "logo":   (FONT_FAMILY, 13, "bold"),
    "tab":    (FONT_FAMILY, 10, "bold"),
}


def apply_theme(root: tk.Tk) -> None:
    """Apply dark USHCODEX theme to the whole Tkinter root."""
    root.configure(bg=BRAND["bg"])

    style = ttk.Style(root)
    style.theme_use("clam")

    # ── General ────────────────────────────────────────────────────────────────
    style.configure(".",
        background=BRAND["bg"],
        foreground=BRAND["fg"],
        fieldbackground=BRAND["bg3"],
        bordercolor=BRAND["border"],
        darkcolor=BRAND["bg"],
        lightcolor=BRAND["bg2"],
        troughcolor=BRAND["bg2"],
        selectbackground=BRAND["sel"],
        selectforeground=BRAND["fg"],
        font=FONTS["body"],
    )

    # ── Frame ──────────────────────────────────────────────────────────────────
    style.configure("TFrame", background=BRAND["bg"])
    style.configure("Card.TFrame", background=BRAND["bg3"],
                    relief="flat", borderwidth=1,
                    bordercolor=BRAND["border"])
    style.configure("Panel.TFrame", background=BRAND["bg2"])
    style.configure("Sidebar.TFrame", background=BRAND["bg2"])

    # ── Label ─────────────────────────────────────────────────────────────────
    style.configure("TLabel", background=BRAND["bg"], foreground=BRAND["fg"])
    style.configure("Card.TLabel", background=BRAND["bg3"], foreground=BRAND["fg"])
    style.configure("Panel.TLabel", background=BRAND["bg2"], foreground=BRAND["fg"])
    style.configure("Title.TLabel", background=BRAND["bg"], foreground=BRAND["fg"],
                    font=FONTS["h2"])
    style.configure("Sub.TLabel", background=BRAND["bg"], foreground=BRAND["fg2"],
                    font=FONTS["small"])
    style.configure("Success.TLabel", foreground=BRAND["success"], background=BRAND["bg2"])
    style.configure("Warning.TLabel", foreground=BRAND["warning"], background=BRAND["bg2"])
    style.configure("Danger.TLabel",  foreground=BRAND["danger"],  background=BRAND["bg2"])

    # ── Button ────────────────────────────────────────────────────────────────
    style.configure("TButton",
        background=BRAND["btn_neutral"],
        foreground=BRAND["fg"],
        bordercolor=BRAND["border"],
        focuscolor=BRAND["accent"],
        relief="flat",
        padding=(8, 5),
        font=FONTS["body"],
    )
    style.map("TButton",
        background=[("active", BRAND["highlight"]), ("pressed", BRAND["sel"])],
        foreground=[("active", BRAND["fg"])],
        bordercolor=[("active", BRAND["accent"])],
    )

    style.configure("Primary.TButton",
        background=BRAND["btn_primary"], foreground="#ffffff",
        font=FONTS["h3"])
    style.map("Primary.TButton",
        background=[("active", BRAND["btn_hover"]), ("pressed", "#d07010")])

    style.configure("Danger.TButton",
        background=BRAND["btn_danger"], foreground="#ffffff")
    style.map("Danger.TButton",
        background=[("active", "#e03040"), ("pressed", "#c02030")])

    style.configure("Success.TButton",
        background=BRAND["btn_success"], foreground="#000000")
    style.map("Success.TButton",
        background=[("active", "#2ecc70"), ("pressed", "#1db360")])

    style.configure("Accent.TButton",
        background=BRAND["accent2"], foreground="#ffffff")
    style.map("Accent.TButton",
        background=[("active", "#6a30b0"), ("pressed", "#521f90")])

    # ── Notebook (Tabs) ────────────────────────────────────────────────────────
    style.configure("TNotebook",
        background=BRAND["bg"], bordercolor=BRAND["border"], tabmargins=[2,4,0,0])
    style.configure("TNotebook.Tab",
        background=BRAND["bg2"], foreground=BRAND["fg2"],
        padding=[14, 7], font=FONTS["tab"],
        bordercolor=BRAND["border"])
    style.map("TNotebook.Tab",
        background=[("selected", BRAND["bg3"]), ("active", BRAND["highlight"])],
        foreground=[("selected", BRAND["accent"]), ("active", BRAND["fg"])],
        expand=[("selected", [1, 1, 1, 0])],
    )

    # ── Entry ─────────────────────────────────────────────────────────────────
    style.configure("TEntry",
        fieldbackground=BRAND["bg3"], foreground=BRAND["fg"],
        bordercolor=BRAND["border"], insertcolor=BRAND["accent"],
        relief="flat")
    style.map("TEntry",
        fieldbackground=[("focus", BRAND["bg2"])],
        bordercolor=[("focus", BRAND["accent"])],
    )

    # ── Combobox ──────────────────────────────────────────────────────────────
    style.configure("TCombobox",
        fieldbackground=BRAND["bg3"], background=BRAND["bg3"],
        foreground=BRAND["fg"], arrowcolor=BRAND["accent"],
        bordercolor=BRAND["border"], selectbackground=BRAND["sel"])
    style.map("TCombobox",
        fieldbackground=[("readonly", BRAND["bg3"])],
        selectbackground=[("readonly", BRAND["bg3"])],
        selectforeground=[("readonly", BRAND["fg"])],
    )

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    style.configure("TScrollbar",
        background=BRAND["bg2"], troughcolor=BRAND["bg"],
        arrowcolor=BRAND["fg2"], bordercolor=BRAND["border"],
        relief="flat")
    style.map("TScrollbar",
        background=[("active", BRAND["highlight"])],
    )

    # ── Scale ─────────────────────────────────────────────────────────────────
    style.configure("TScale",
        background=BRAND["bg"], troughcolor=BRAND["bg3"],
        sliderlength=18)

    # ── Progressbar ───────────────────────────────────────────────────────────
    style.configure("TProgressbar",
        background=BRAND["accent"], troughcolor=BRAND["bg3"],
        bordercolor=BRAND["bg3"])

    # ── Treeview ──────────────────────────────────────────────────────────────
    style.configure("Treeview",
        background=BRAND["bg3"], foreground=BRAND["fg"],
        fieldbackground=BRAND["bg3"], bordercolor=BRAND["border"],
        rowheight=24, font=FONTS["body"])
    style.configure("Treeview.Heading",
        background=BRAND["bg2"], foreground=BRAND["accent"],
        relief="flat", font=FONTS["h3"])
    style.map("Treeview",
        background=[("selected", BRAND["sel"])],
        foreground=[("selected", BRAND["fg"])],
    )

    # ── Checkbutton ───────────────────────────────────────────────────────────
    style.configure("TCheckbutton",
        background=BRAND["bg"], foreground=BRAND["fg"],
        indicatorcolor=BRAND["bg3"],
        indicatorrelief="flat",
    )
    style.map("TCheckbutton",
        indicatorcolor=[("selected", BRAND["accent"])],
        background=[("active", BRAND["bg"])],
    )

    # ── Radiobutton ───────────────────────────────────────────────────────────
    style.configure("TRadiobutton",
        background=BRAND["bg"], foreground=BRAND["fg"])
    style.map("TRadiobutton",
        indicatorcolor=[("selected", BRAND["accent"])],
        background=[("active", BRAND["bg"])],
    )

    # ── Separator ─────────────────────────────────────────────────────────────
    style.configure("TSeparator", background=BRAND["border"])

    # ── Labelframe ────────────────────────────────────────────────────────────
    style.configure("TLabelframe",
        background=BRAND["bg3"], bordercolor=BRAND["border"],
        relief="flat")
    style.configure("TLabelframe.Label",
        background=BRAND["bg3"], foreground=BRAND["accent"],
        font=FONTS["h3"])

    # ── Spinbox ───────────────────────────────────────────────────────────────
    style.configure("TSpinbox",
        fieldbackground=BRAND["bg3"], foreground=BRAND["fg"],
        bordercolor=BRAND["border"], arrowcolor=BRAND["accent"])

    # Patch Tk text/listbox colours globally
    root.option_add("*Text.Background",          BRAND["bg3"])
    root.option_add("*Text.Foreground",          BRAND["fg"])
    root.option_add("*Text.InsertBackground",    BRAND["accent"])
    root.option_add("*Text.SelectBackground",    BRAND["sel"])
    root.option_add("*Text.SelectForeground",    BRAND["fg"])
    root.option_add("*Listbox.Background",       BRAND["bg3"])
    root.option_add("*Listbox.Foreground",       BRAND["fg"])
    root.option_add("*Listbox.SelectBackground", BRAND["sel"])
    root.option_add("*Listbox.SelectForeground", BRAND["fg"])
    root.option_add("*Menu.Background",          BRAND["bg2"])
    root.option_add("*Menu.Foreground",          BRAND["fg"])
    root.option_add("*Menu.ActiveBackground",    BRAND["sel"])
    root.option_add("*Menu.ActiveForeground",    BRAND["accent"])
    root.option_add("*Menu.Relief",              "flat")
