"""
USHCODEX Android Debugger - Icon Manager
Generates pixel-art / solid-color icons using Pillow when no SVG available.
Falls back to text characters if Pillow is unavailable.
"""
from __future__ import annotations
import os
import io
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    _PIL = True
except ImportError:
    _PIL = False

try:
    import tkinter as tk
    _TK = True
except ImportError:
    _TK = False

ASSETS = Path(__file__).parent.parent / "assets"
ICONS_DIR = ASSETS / "icons"

# USHCODEX brand colours
ORANGE = (247, 147, 30)
PURPLE = (71, 42, 190)
WHITE  = (255, 255, 255)
BG     = (15,  15,  26)


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i])*t) for i in range(3))


def _make_icon(symbol: str, size: int = 20, bg=None, fg=ORANGE) -> Optional[object]:
    """Create a small icon PhotoImage with given symbol."""
    if not _PIL or not _TK:
        return None
    img = Image.new("RGBA", (size, size), bg or (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Draw a filled circle background
    pad = 2
    draw.ellipse([pad, pad, size-pad, size-pad], fill=(*fg, 220))
    # Draw white symbol in center
    try:
        font = ImageFont.truetype("segoeui.ttf", int(size * 0.55))
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), symbol, font=font)
    tx = (size - (bbox[2]-bbox[0])) // 2 - bbox[0]
    ty = (size - (bbox[3]-bbox[1])) // 2 - bbox[1]
    draw.text((tx, ty), symbol, fill=(255,255,255,255), font=font)
    return img


def _gradient_icon(symbol: str, size: int = 20) -> Optional[object]:
    """Gradient orange→purple background icon."""
    if not _PIL:
        return None
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for x in range(size):
        t = x / size
        c = _lerp_color(ORANGE, PURPLE, t)
        draw.line([(x, 0), (x, size)], fill=(*c, 255))
    # Clip to circle
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([1,1,size-2,size-2], fill=255)
    img.putalpha(mask)
    # Symbol
    draw2 = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("segoeui.ttf", int(size * 0.55))
    except Exception:
        font = ImageFont.load_default()
    bbox = draw2.textbbox((0,0), symbol, font=font)
    tx = (size - (bbox[2]-bbox[0])) // 2 - bbox[0]
    ty = (size - (bbox[3]-bbox[1])) // 2 - bbox[1]
    draw2.text((tx, ty), symbol, fill=(255,255,255,255), font=font)
    return img


class IconSet:
    """Lazy-load icon PhotoImages for use in Tkinter widgets."""

    _cache: dict[str, object] = {}

    # Map of name → (symbol, colour_variant)
    # variant: 'gradient' | 'orange' | 'purple' | 'green' | 'red'
    DEFS: dict[str, tuple[str, str]] = {
        # Navigation
        "back":        ("◀", "orange"),
        "home":        ("⌂", "orange"),
        "recents":     ("▭", "orange"),
        "menu":        ("≡", "orange"),
        # Power / Screen
        "power":       ("⏻", "red"),
        "screen_off":  ("◑", "purple"),
        "screen_on":   ("☀", "orange"),
        "brightness_up":   ("🔆", "orange"),
        "brightness_down": ("🔅", "purple"),
        # Volume
        "vol_up":      ("🔊", "green"),
        "vol_down":    ("🔉", "purple"),
        "mute":        ("🔇", "red"),
        # Media
        "play":        ("▶", "green"),
        "pause":       ("⏸", "orange"),
        "stop_media":  ("⏹", "red"),
        "prev":        ("⏮", "purple"),
        "next":        ("⏭", "purple"),
        # System
        "screenshot":  ("📷", "gradient"),
        "rotate":      ("↻", "orange"),
        "expand_notif":("🔔", "purple"),
        "expand_qs":   ("▤",  "purple"),
        "clipboard":   ("📋", "orange"),
        "kill_app":    ("✕",  "red"),
        "keyboard":    ("⌨", "orange"),
        "lock":        ("🔒", "purple"),
        "unlock":      ("🔓", "orange"),
        # Mirroring
        "mirror":      ("📺", "gradient"),
        "record":      ("⏺", "red"),
        "otg":         ("🖱", "orange"),
        "camera":      ("📹", "gradient"),
        "wifi":        ("📶", "green"),
        "audio":       ("🎵", "purple"),
        # Files
        "file":        ("📁", "orange"),
        "upload":      ("⬆", "green"),
        "download":    ("⬇", "purple"),
        "delete":      ("🗑", "red"),
        # Advanced
        "tablet":      ("⬛", "gradient"),
        "gesture":     ("👆", "gradient"),
        "apk":         ("📦", "orange"),
        "terminal":    (">_", "purple"),
        "settings":    ("⚙", "purple"),
        "about":       ("ℹ", "gradient"),
        "gnirehtet":   ("🌐", "green"),
        "logcat":      ("📋", "orange"),
        "forward":     ("🔀", "purple"),
        "reboot":      ("↺",  "orange"),
        "debug":       ("🐛", "gradient"),
        # App actions
        "stop":        ("■",  "red"),
        "play_app":    ("▶",  "green"),
        "clear":       ("🗑", "red"),
        "disable":     ("🚫", "red"),
        # Connect
        "connect":     ("🔗", "green"),
        "disconnect":  ("✂",  "red"),
    }

    COLOR_MAP = {
        "gradient": None,          # special
        "orange":   ORANGE,
        "purple":   PURPLE,
        "green":    (61, 220, 132),
        "red":      (255, 79, 94),
    }

    @classmethod
    def get(cls, name: str, size: int = 18) -> Optional[object]:
        """Return a Tkinter PhotoImage for the given icon name."""
        key = f"{name}_{size}"
        if key in cls._cache:
            return cls._cache[key]
        if not _PIL or not _TK:
            return None

        sym, variant = cls.DEFS.get(name, ("?", "orange"))
        if variant == "gradient":
            pil_img = _gradient_icon(sym, size)
        else:
            colour = cls.COLOR_MAP.get(variant, ORANGE)
            pil_img = _make_icon(sym, size, fg=colour)

        if pil_img is None:
            return None
        try:
            photo = ImageTk.PhotoImage(pil_img)
            cls._cache[key] = photo
            return photo
        except Exception:
            return None

    @classmethod
    def preload(cls, size: int = 18):
        for name in cls.DEFS:
            cls.get(name, size)


def make_app_icon(svg_path: str, ico_path: str, sizes=(16, 32, 48, 64, 128, 256)) -> bool:
    """Convert USHCODEX SVG → multi-size ICO using cairosvg + Pillow."""
    if not _PIL:
        return False
    try:
        import cairosvg
        pngs = []
        for s in sizes:
            png_data = cairosvg.svg2png(url=svg_path, output_width=s, output_height=s)
            pngs.append(Image.open(io.BytesIO(png_data)).convert("RGBA"))
        pngs[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes],
                     append_images=pngs[1:])
        return True
    except ImportError:
        pass

    # Fallback: generate a programmatic icon
    _generate_fallback_ico(ico_path, sizes)
    return True


def _generate_fallback_ico(ico_path: str, sizes=(16,32,48,64,128,256)):
    """Generate a gradient 'U' logo ICO without cairosvg."""
    if not _PIL:
        return
    frames = []
    for s in sizes:
        img = Image.new("RGBA", (s, s), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        # Gradient background circle
        for x in range(s):
            t = x / s
            c = _lerp_color(ORANGE, PURPLE, t)
            for y in range(s):
                # inside circle?
                cx = s//2; cy = s//2; r = s//2 - 1
                if (x-cx)**2 + (y-cy)**2 <= r**2:
                    img.putpixel((x, y), (*c, 255))
        # Draw "U" letter
        try:
            font_size = max(8, int(s * 0.6))
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0,0), "U", font=font)
        tx = (s - (bbox[2]-bbox[0])) // 2 - bbox[0]
        ty = (s - (bbox[3]-bbox[1])) // 2 - bbox[1]
        # Drop shadow
        draw.text((tx+1, ty+1), "U", fill=(0,0,0,120), font=font)
        draw.text((tx, ty), "U", fill=(255,255,255,255), font=font)
        frames.append(img)

    frames[0].save(ico_path, format="ICO",
                   sizes=[(s,s) for s in sizes],
                   append_images=frames[1:])
