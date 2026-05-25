import io
import os
import re
import textwrap

from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

_NIKUD_RE = re.compile(r'[֑-ׇ]')

_DEFAULT_FONT_DIRS = [
    "/mnt/ssd2/cyttic/datasets/hebrew-handwritten-dataset/fonts_out",
    "/mnt/ssd2/cyttic/projects/handwrittenTextGenerator/fonts",
    "/app/fonts",
]
FONT_DIRS = [d for d in (
    os.environ.get("FONT_DIRS", "").split(":") + _DEFAULT_FONT_DIRS
) if d and os.path.isdir(d)]

BG_DIR = os.environ.get(
    "BG_DIR",
    next((d for d in [
        "/app/backgrounds",
        "/mnt/ssd2/cyttic/projects/handwrittenTextGenerator/images",
    ] if os.path.isdir(d)), "/app/backgrounds")
)


def strip_nikud(text: str) -> str:
    return _NIKUD_RE.sub('', text)


def list_fonts() -> list[dict]:
    fonts = []
    seen  = set()
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if fname.lower().endswith(".ttf") and fname not in seen:
                seen.add(fname)
                fonts.append({"name": fname.replace(".ttf", ""),
                               "file": fname,
                               "path": os.path.join(d, fname)})
    return fonts


def get_font_path(font_file: str) -> str | None:
    for d in FONT_DIRS:
        p = os.path.join(d, font_file)
        if os.path.exists(p):
            return p
    return None


def list_backgrounds() -> list[str]:
    if not os.path.isdir(BG_DIR):
        return []
    return sorted(
        f for f in os.listdir(BG_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )


def get_background_path(filename: str) -> str | None:
    p = os.path.join(BG_DIR, filename)
    return p if os.path.exists(p) else None


def render(text: str, font_path: str, font_size: int = 60,
           max_width: int = 1600, padding: int = 30,
           bg: str = "#ffffff", fg: str = "#1a1a1a",
           bg_image: str | None = None,
           transparent: bool = False) -> bytes:

    text = strip_nikud(text)
    font = ImageFont.truetype(font_path, size=font_size)

    avg_char_px   = font_size * 0.6
    chars_per_line = max(1, int(max_width / avg_char_px))
    raw_lines = text.splitlines() or [""]
    lines = []
    for raw in raw_lines:
        if not raw.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw, width=chars_per_line) or [raw])

    lines = [get_display(line) if line.strip() else line for line in lines]

    dummy  = Image.new("RGB", (1, 1))
    draw   = ImageDraw.Draw(dummy)
    line_h = font_size + int(font_size * 0.3)
    widths = [
        (draw.textbbox((0, 0), line, font=font)[2] -
         draw.textbbox((0, 0), line, font=font)[0])
        if line else 0
        for line in lines
    ]

    img_w = min(max(max_width, max(widths, default=0) + 2 * padding), 3200)
    img_h = line_h * len(lines) + 2 * padding

    # Build background
    if transparent:
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    elif bg_image:
        bg_path = get_background_path(bg_image)
        if bg_path:
            src = Image.open(bg_path).convert("RGB")
            sw, sh = src.size
            if sw < img_w or sh < img_h:
                src = src.resize((max(sw, img_w), max(sh, img_h)))
                sw, sh = src.size
            left = (sw - img_w) // 2
            top  = (sh - img_h) // 2
            img  = src.crop((left, top, left + img_w, top + img_h))
        else:
            img = Image.new("RGB", (img_w, img_h), bg)
    else:
        img = Image.new("RGB", (img_w, img_h), bg)

    draw = ImageDraw.Draw(img)
    y = padding
    for line in lines:
        if line.strip():
            bb = draw.textbbox((0, 0), line, font=font)
            lw = bb[2] - bb[0]
            x  = img_w - padding - lw
            draw.text((x, y), line, font=font, fill=fg)
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
