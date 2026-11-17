"""
USHCODEX Android Debugger - Theme & Design System
Matches ushcodex.tech: warm paper background, white cards, ink text,
purple hover accents, orange highlights, hairline borders, soft radii.
"""
import tkinter as tk
from tkinter import ttk

# ── Brand palette (ushcodex.tech design tokens) ──────────────────────────────
BRAND = {
    "paper":        "#f7f6f2",   # app background
    "white":        "#ffffff",   # cards
    "ink":          "#1b1a20",   # primary text / primary buttons
    "muted":        "#5d5a62",   # secondary text
    "line":         "#dfddd8",   # hairline borders
    "line_soft":    "#e8e6e2",   # even softer borders / dividers
    "purple":       "#5f30aa",   # hover / active accent
    "purple_light": "#e9e0f8",   # lavender fills (toggles ON, highlights)
    "purple_soft":  "#ebe5f2",   # decorative fills
    "orange":       "#ef7738",   # brand pop
    "orange_soft":  "#ffb98d",   # decorative orange
    "dark":         "#1e1c23",   # dark sections (header band)
    "success":      "#2e7d4f",
    "success_soft": "#e2f0e6",
    "danger":       "#b3402e",
    "danger_soft":  "#f8e4df",
    "hover_fill":   "#f1efe9",   # subtle hover on list rows
    "sel":          "#e9e0f8",   # selection
}

FONT_FAMILY = "Segoe UI"

# Backward-compat aliases (older modules use the dark-theme key names)
BRAND.update({
    "bg":     BRAND["paper"],     # was dark bg
    "bg2":    BRAND["white"],     # was panel bg
    "bg3":    BRAND["white"],     # was card bg
    "fg":     BRAND["ink"],
    "fg2":    BRAND["muted"],
    "accent": BRAND["purple"],
    "border": BRAND["line"],
    "mid":    BRAND["orange_soft"],
})
FONTS = {
    "h1":     (FONT_FAMILY, 20, "bold"),
    "h2":     (FONT_FAMILY, 14, "bold"),
    "h3":     (FONT_FAMILY, 10, "bold"),
    "body":   (FONT_FAMILY, 10),
    "small":  (FONT_FAMILY,  9),
    "tiny":   (FONT_FAMILY,  8),
    "mono":   ("Consolas",  10),
    "mono_sm":("Consolas",   9),
    "logo":   (FONT_FAMILY, 13, "bold"),
    "tab":    (FONT_FAMILY, 10, "bold"),
}


def apply_theme(root: tk.Tk) -> None:
    """Apply the Ushcodex paper theme to the whole Tkinter root."""
    root.configure(bg=BRAND["paper"])

    style = ttk.Style(root)
    style.theme_use("clam")

    # ── General ────────────────────────────────────────────────────────────────
    style.configure(".",
        background=BRAND["paper"],
        foreground=BRAND["ink"],
        fieldbackground=BRAND["white"],
        bordercolor=BRAND["line"],
        darkcolor=BRAND["paper"],
        lightcolor=BRAND["white"],
        troughcolor=BRAND["hover_fill"],
        selectbackground=BRAND["sel"],
        selectforeground=BRAND["ink"],
        font=FONTS["body"],
    )

    # ── Frame ─────────────────────────────────────────────────────────────────
    style.configure("TFrame", background=BRAND["paper"])
    style.configure("Card.TFrame", background=BRAND["white"])
    style.configure("Panel.TFrame", background=BRAND["white"])
    style.configure("Sidebar.TFrame", background=BRAND["white"])
    style.configure("Host.TFrame", background=BRAND["paper"])

    # ── Label ─────────────────────────────────────────────────────────────────
    style.configure("TLabel", background=BRAND["paper"], foreground=BRAND["ink"])
    style.configure("Card.TLabel", background=BRAND["white"], foreground=BRAND["ink"])
    style.configure("Panel.TLabel", background=BRAND["white"], foreground=BRAND["ink"])
    style.configure("Title.TLabel", background=BRAND["paper"], foreground=BRAND["ink"],
                    font=FONTS["h2"])
    style.configure("Sub.TLabel", background=BRAND["paper"], foreground=BRAND["muted"],
                    font=FONTS["small"])
    style.configure("CardSub.TLabel", background=BRAND["white"], foreground=BRAND["muted"],
                    font=FONTS["small"])
    style.configure("PanelSub.TLabel", background=BRAND["white"], foreground=BRAND["muted"],
                    font=FONTS["small"])
    style.configure("Eyebrow.TLabel", background=BRAND["paper"], foreground=BRAND["muted"],
                    font=FONTS["tiny"])
    style.configure("Success.TLabel", foreground=BRAND["success"], background=BRAND["white"])
    style.configure("Warning.TLabel", foreground=BRAND["orange"], background=BRAND["white"])
    style.configure("Danger.TLabel",  foreground=BRAND["danger"],  background=BRAND["white"])

    # ── Button ────────────────────────────────────────────────────────────────
    # Default = outline: white bg, hairline gray border, ink text → purple on hover
    style.configure("TButton",
        background=BRAND["white"],
        foreground=BRAND["ink"],
        bordercolor="#b8b4b1",
        focuscolor=BRAND["purple"],
        relief="flat",
        padding=(12, 7),
        font=FONTS["body"],
        anchor="center",
    )
    style.map("TButton",
        background=[("active", BRAND["paper"]), ("pressed", BRAND["purple_soft"])],
        foreground=[("active", BRAND["purple"])],
        bordercolor=[("active", BRAND["purple"]), ("pressed", BRAND["purple"])],
    )

    # Primary = ink (dark) button → purple on hover (site .button)
    style.configure("Primary.TButton",
        background=BRAND["ink"], foreground="#ffffff",
        bordercolor=BRAND["ink"],
        font=FONTS["h3"], padding=(14, 8))
    style.map("Primary.TButton",
        background=[("active", BRAND["purple"]), ("pressed", "#4a2387")],
        bordercolor=[("active", BRAND["purple"])],
        foreground=[("active", "#ffffff")],
    )

    # Danger = soft red card button
    style.configure("Danger.TButton",
        background=BRAND["white"], foreground=BRAND["danger"],
        bordercolor=BRAND["danger"], font=FONTS["body"])
    style.map("Danger.TButton",
        background=[("active", BRAND["danger"]), ("pressed", "#8f3123")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        bordercolor=[("active", BRAND["danger"])],
    )

    # Success = soft green
    style.configure("Success.TButton",
        background=BRAND["white"], foreground=BRAND["success"],
        bordercolor=BRAND["success"], font=FONTS["body"])
    style.map("Success.TButton",
        background=[("active", BRAND["success"]), ("pressed", "#256a42")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        bordercolor=[("active", BRAND["success"])],
    )

    # Accent = purple solid
    style.configure("Accent.TButton",
        background=BRAND["purple"], foreground="#ffffff",
        bordercolor=BRAND["purple"], font=FONTS["h3"])
    style.map("Accent.TButton",
        background=[("active", "#4a2387"), ("pressed", "#3c1d70")],
        foreground=[("active", "#ffffff")],
    )

    # Toggle ON = lavender fill, purple text (state indicator)
    style.configure("ToggleOn.TButton",
        background=BRAND["purple_light"], foreground=BRAND["purple"],
        bordercolor=BRAND["purple"], font=FONTS["body"])
    style.map("ToggleOn.TButton",
        background=[("active", "#dfd2f3"), ("pressed", "#d3c2ef")],
        foreground=[("active", BRAND["purple"])],
        bordercolor=[("active", BRAND["purple"])],
    )

    # ── Notebook (Tabs) ────────────────────────────────────────────────────────
    style.configure("TNotebook",
        background=BRAND["paper"], bordercolor=BRAND["line"],
        tabmargins=[2, 6, 0, 0])
    style.configure("TNotebook.Tab",
        background=BRAND["paper"], foreground=BRAND["muted"],
        padding=[16, 8], font=FONTS["tab"],
        bordercolor=BRAND["line"])
    style.map("TNotebook.Tab",
        background=[("selected", BRAND["white"]), ("active", BRAND["hover_fill"])],
        foreground=[("selected", BRAND["purple"]), ("active", BRAND["ink"])],
        expand=[("selected", [1, 1, 1, 0])],
    )

    # ── Entry ─────────────────────────────────────────────────────────────────
    style.configure("TEntry",
        fieldbackground=BRAND["white"], foreground=BRAND["ink"],
        bordercolor="#aaa6a1", insertcolor=BRAND["ink"],
        relief="flat")
    style.map("TEntry",
        bordercolor=[("focus", BRAND["purple"])],
        lightcolor=[("focus", BRAND["purple"])],
    )

    # ── Combobox ──────────────────────────────────────────────────────────────
    style.configure("TCombobox",
        fieldbackground=BRAND["white"], background=BRAND["white"],
        foreground=BRAND["ink"], arrowcolor=BRAND["ink"],
        bordercolor="#aaa6a1", selectbackground=BRAND["sel"])
    style.map("TCombobox",
        fieldbackground=[("readonly", BRAND["white"])],
        selectbackground=[("readonly", BRAND["sel"])],
        selectforeground=[("readonly", BRAND["ink"])],
        bordercolor=[("focus", BRAND["purple"])],
    )
    root.option_add("*TCombobox*Listbox.Background", BRAND["white"])
    root.option_add("*TCombobox*Listbox.Foreground", BRAND["ink"])
    root.option_add("*TCombobox*Listbox.selectBackground", BRAND["sel"])
    root.option_add("*TCombobox*Listbox.selectForeground", BRAND["ink"])

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    style.configure("TScrollbar",
        background=BRAND["line_soft"], troughcolor=BRAND["paper"],
        arrowcolor=BRAND["muted"], bordercolor=BRAND["paper"],
        relief="flat")
    style.map("TScrollbar",
        background=[("active", BRAND["line"])],
    )

    # ── Scale / Progress ──────────────────────────────────────────────────────
    style.configure("TScale",
        background=BRAND["paper"], troughcolor=BRAND["line_soft"],
        sliderlength=18)
    style.configure("TProgressbar",
        background=BRAND["purple"], troughcolor=BRAND["line_soft"],
        bordercolor=BRAND["line_soft"])

    # ── Treeview ──────────────────────────────────────────────────────────────
    style.configure("Treeview",
        background=BRAND["white"], foreground=BRAND["ink"],
        fieldbackground=BRAND["white"], bordercolor=BRAND["line"],
        rowheight=26, font=FONTS["body"])
    style.configure("Treeview.Heading",
        background=BRAND["paper"], foreground=BRAND["muted"],
        relief="flat", font=FONTS["tiny"])
    style.map("Treeview",
        background=[("selected", BRAND["sel"])],
        foreground=[("selected", BRAND["ink"])],
    )

    # ── Checkbutton / Radiobutton ─────────────────────────────────────────────
    style.configure("TCheckbutton",
        background=BRAND["paper"], foreground=BRAND["ink"],
        indicatorcolor=BRAND["white"], indicatorrelief="flat",
        bordercolor="#aaa6a1")
    style.map("TCheckbutton",
        indicatorcolor=[("selected", BRAND["purple"])],
        background=[("active", BRAND["paper"])],
    )
    style.configure("Card.TCheckbutton",
        background=BRAND["white"], foreground=BRAND["ink"])
    style.map("Card.TCheckbutton",
        indicatorcolor=[("selected", BRAND["purple"])],
        background=[("active", BRAND["white"])],
    )
    style.configure("TRadiobutton",
        background=BRAND["paper"], foreground=BRAND["ink"])
    style.map("TRadiobutton",
        indicatorcolor=[("selected", BRAND["purple"])],
        background=[("active", BRAND["paper"])],
    )

    # ── Separator ─────────────────────────────────────────────────────────────
    style.configure("TSeparator", background=BRAND["line"])

    # ── Labelframe ────────────────────────────────────────────────────────────
    style.configure("TLabelframe",
        background=BRAND["white"], bordercolor=BRAND["line"],
        relief="flat")
    style.configure("TLabelframe.Label",
        background=BRAND["white"], foreground=BRAND["purple"],
        font=FONTS["tiny"])

    # ── Spinbox ───────────────────────────────────────────────────────────────
    style.configure("TSpinbox",
        fieldbackground=BRAND["white"], foreground=BRAND["ink"],
        bordercolor="#aaa6a1", arrowcolor=BRAND["ink"])

    # Patch Tk text/listbox colours globally
    root.option_add("*Text.Background",          BRAND["white"])
    root.option_add("*Text.Foreground",          BRAND["ink"])
    root.option_add("*Text.InsertBackground",    BRAND["purple"])
    root.option_add("*Text.SelectBackground",    BRAND["sel"])
    root.option_add("*Text.SelectForeground",    BRAND["ink"])
    root.option_add("*Listbox.Background",       BRAND["white"])
    root.option_add("*Listbox.Foreground",       BRAND["ink"])
    root.option_add("*Listbox.SelectBackground", BRAND["sel"])
    root.option_add("*Listbox.SelectForeground", BRAND["ink"])
    root.option_add("*Menu.Background",          BRAND["white"])
    root.option_add("*Menu.Foreground",          BRAND["ink"])
    root.option_add("*Menu.ActiveBackground",    BRAND["purple_light"])
    root.option_add("*Menu.ActiveForeground",    BRAND["purple"])
    root.option_add("*Menu.Relief",              "flat")
