"""
USHCODEX Android Debugger - Brand asset generator.
Rasterizes the official wordmark SVG (via headless Edge) and builds
the app icon (multi-size ICO) + header banner PNG with Pillow.
Run once:  python assets/gen_brand.py
"""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ICONS  = ASSETS / "icons"
ICONS.mkdir(parents=True, exist_ok=True)

SVG    = ASSETS / "logo.svg"
RAW    = ASSETS / "logo_raw.png"
BANNER = ASSETS / "banner.png"
ICO    = ASSETS / "icons" / "uad.ico"

ORANGE = (247, 147, 30)
PURPLE = (71, 42, 190)
DARK   = (15, 15, 26)


def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def rasterize_svg(svg_path: Path, out_png: Path, width: int = 1600) -> bool:
    """Use headless Edge to render SVG -> PNG (transparent-safe via white remove)."""
    edge = None
    for p in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.exists(p):
            edge = p
            break
    if not edge:
        return False
    h = int(width * 9.56 / 29.09) + 8
    html = out_png.with_suffix(".html")
    html.write_text(
        f'<html><body style="margin:0;background:#0f0f1a;">'
        f'<img src="{svg_path.as_uri()}" width="{width}"></body></html>',
        encoding="utf-8")
    try:
        subprocess.run(
            [edge, "--headless", "--disable-gpu",
             f"--screenshot={out_png}",
             f"--window-size={width},{h}",
             "--default-background-color=00000000",
             "--hide-scrollbars", html.as_uri()],
            timeout=60, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        return out_png.exists() and out_png.stat().st_size > 1000
    finally:
        html.unlink(missing_ok=True)


def gradient_bg(size: int, rounded=True) -> Image.Image:
    """Diagonal orange->purple gradient, rounded-square, transparent corners."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x / size + y / size) / 2
            px[x, y] = (*lerp(ORANGE, PURPLE, t), 255)
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [1, 1, size - 2, size - 2], radius=int(size * 0.22), fill=255)
        img.putalpha(mask)
    return img


def find_font(px: int):
    for f in ("segoeuib.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            continue
    return ImageFont.load_default()


def make_icon(sizes=(16, 24, 32, 48, 64, 128, 256)):
    """Square badge: gradient rounded square + bold 'U' + orange dot (droid eye)."""
    big = 512
    img = gradient_bg(big)
    draw = ImageDraw.Draw(img)
    # subtle inner highlight ring
    draw.rounded_rectangle([14, 14, big - 14, big - 14],
                           radius=int(big * 0.21),
                           outline=(255, 255, 255, 40), width=6)
    # Android-robot antenna hint + bold U
    font = find_font(int(big * 0.62))
    bbox = draw.textbbox((0, 0), "U", font=font)
    tx = (big - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = (big - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((tx + 5, ty + 7), "U", fill=(0, 0, 0, 90), font=font)   # shadow
    draw.text((tx, ty), "U", fill=(255, 255, 255, 255), font=font)    # U
    # orange accent dot (top-right, like the f7931e brand pop)
    r = int(big * 0.075)
    cx, cy = int(big * 0.78), int(big * 0.22)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*ORANGE, 255))
    draw.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6],
                 fill=(255, 255, 255, 230))

    frames = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    frames[0].save(ICO, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=frames[1:])
    return frames


def make_banner():
    """Header banner: dark bg + rasterized wordmark, fallback to text."""
    W, H = 1200, 260
    banner = Image.new("RGBA", (W, H), (*DARK, 255))

    if RAW.exists():
        logo = Image.open(RAW).convert("RGBA")
        ratio = min((W - 160) / logo.width, (H - 80) / logo.height)
        logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)),
                           Image.LANCZOS)
        # drop shadow
        sh = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        alpha = logo.split()[3].point(lambda a: int(a * 0.5))
        sh.putalpha(alpha)
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow.paste((0, 0, 0, 160), (102, 84), sh)
        banner = Image.alpha_composite(banner, shadow)
        banner.alpha_composite(logo, (100, 80))
    else:  # fallback: text wordmark with gradient
        font = find_font(140)
        text = "USHCODEX"
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        bbox = d.textbbox((0, 0), text, font=font)
        tx, ty = (W - (bbox[2] - bbox[0])) // 2 - bbox[0], \
                 (H - (bbox[3] - bbox[1])) // 2 - bbox[1]
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gp = grad.load()
        for x in range(W):
            c = lerp(ORANGE, PURPLE, x / W)
            for y in range(H):
                gp[x, y] = (*c, 255)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).text((tx, ty), text, fill=255, font=font)
        banner.paste(grad, (0, 0), mask)
        d2 = ImageDraw.Draw(banner)
        d2.text((tx + 2, ty + 2), text, fill=(255, 255, 255, 60), font=font)
    banner.save(BANNER)
    return banner


if __name__ == "__main__":
    ok = rasterize_svg(SVG, RAW, width=1600)
    print(f"SVG rasterize: {'OK' if ok else 'FAILED (fallback text)'}")
    frames = make_icon()
    print(f"ICO written: {ICO}  ({len(frames)} sizes)")
    make_banner()
    print(f"Banner written: {BANNER}")
    # also save a 512 png for GitHub/social
    frames[-1].save(ICONS / "uad_512.png")
    print(f"PNG written: {ICONS / 'uad_512.png'}")
