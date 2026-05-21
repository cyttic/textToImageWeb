import io
import os
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Hebrew nikud (vowel points) + cantillation marks: U+0591–U+05C7
_NIKUD_RE = re.compile(r'[֑-ׇ]')

def strip_nikud(text: str) -> str:
    """Remove Hebrew diacritical marks (nikud, dagesh, cantillation) from text."""
    return _NIKUD_RE.sub('', text)

FONT_DIRS = [
    "/mnt/ssd2/cyttic/datasets/hebrew-handwritten-dataset/fonts_out",
    "/mnt/ssd2/cyttic/projects/handwrittenTextGenerator/fonts",
]


def list_fonts() -> list[dict]:
    fonts = []
    seen = set()
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if fname.lower().endswith(".ttf") and fname not in seen:
                seen.add(fname)
                fonts.append({
                    "name": fname.replace(".ttf", ""),
                    "file": fname,
                    "path": os.path.join(d, fname),
                })
    return fonts


def get_font_path(font_file: str) -> str | None:
    for d in FONT_DIRS:
        p = os.path.join(d, font_file)
        if os.path.exists(p):
            return p
    return None


def render(text: str, font_path: str, font_size: int = 60,
           max_width: int = 760, padding: int = 30,
           bg: str = "#ffffff", fg: str = "#1a1a1a") -> bytes:

    text = strip_nikud(text)
    font = ImageFont.truetype(font_path, size=font_size)

    # Wrap long text into lines
    avg_char_px = font_size * 0.6
    chars_per_line = max(1, int(max_width / avg_char_px))
    raw_lines = text.splitlines() or [""]
    lines = []
    for raw in raw_lines:
        if not raw.strip():
            lines.append("")
            continue
        wrapped = textwrap.wrap(raw, width=chars_per_line) or [raw]
        lines.extend(wrapped)

    # Measure
    dummy   = Image.new("RGB", (1, 1))
    draw    = ImageDraw.Draw(dummy)
    line_h  = font_size + int(font_size * 0.3)
    widths  = []
    for line in lines:
        if line:
            bb = draw.textbbox((0, 0), line, font=font)
            widths.append(bb[2] - bb[0])
        else:
            widths.append(0)

    img_w = min(max(max_width, max(widths, default=0) + 2 * padding), 1600)
    img_h = line_h * len(lines) + 2 * padding

    img  = Image.new("RGB", (img_w, img_h), bg)
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        if line.strip():
            draw.text((padding, y), line, font=font, fill=fg)
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()
