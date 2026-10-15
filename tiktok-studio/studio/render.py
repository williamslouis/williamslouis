"""Render post.json into carousel slides (PNG) plus caption.txt. Layout spec: brand.md section 2."""

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from . import config

BG = "#FFFFFF"
INK = "#0A0A0A"
META = "#8C8C8C"
EMPTY = "#ECECEC"

# Measured from the reference (1500 x 2000) and kept as fractions so any canvas works.
FORMATS = {
    #        size          photo top  text baseline
    "3x4":  ((1080, 1440), 0.144, 0.918),
    "4x5":  ((1080, 1350), 0.120, 0.915),
    "9x16": ((1080, 1920), 0.170, 0.760),
}
SIDE = 0.073          # photo side margin, fraction of width
PHOTO_RATIO = 0.75    # photo height / width (4:3)
TEXT_INSET = 0.027    # text right edge inset from photo right edge, fraction of width
TRACKING = 0.02       # letter spacing, fraction of font size

# Font lookup: your own files in fonts/ first, then the system.
BOLD_FONTS = [
    "fonts/Helvetica-Bold.ttf", "fonts/HelveticaNeue-Bold.otf", "fonts/Helvetica-Bold.otf",
    "fonts/HelveticaNowDisplay-Bold.otf",
    ("/System/Library/Fonts/Helvetica.ttc", 1),
    ("/System/Library/Fonts/HelveticaNeue.ttc", 1),
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf",
]
REGULAR_FONTS = [
    "fonts/Helvetica.ttf", "fonts/HelveticaNeue.otf", "fonts/Helvetica.otf",
    "fonts/HelveticaNowDisplay-Regular.otf",
    ("/System/Library/Fonts/Helvetica.ttc", 0),
    ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf",
]
_font_cache = {}


def load_font(bold, size):
    key = (bold, size)
    if key not in _font_cache:
        for entry in BOLD_FONTS if bold else REGULAR_FONTS:
            path, index = entry if isinstance(entry, tuple) else (entry, 0)
            path = config.ROOT / path if not Path(path).is_absolute() and not path[1:3] == ":/" else Path(path)
            if path.exists():
                _font_cache[key] = ImageFont.truetype(str(path), size, index=index)
                break
        else:
            raise SystemExit("no usable font found; put Helvetica-Bold.ttf in fonts/")
    return _font_cache[key]


# --- text -------------------------------------------------------------------

def text_width(font, s, tracking):
    return font.getlength(s) + tracking * max(len(s) - 1, 0)


def draw_tracked(draw, x, y, s, font, fill, tracking):
    """Draw with letter spacing while keeping the font's own kerning (anchor: left baseline)."""
    for i, ch in enumerate(s):
        draw.text((x + font.getlength(s[:i]) + i * tracking, y), ch, font=font, fill=fill,
                  anchor="ls")


NBSP = "\u00a0"
# keep "155 km", "3 october", "11:30 pm" etc. on one line
GLUE = re.compile(r"(\d) (?=[a-z%£$€]{1,9}\b)")


def wrap(font, text, max_w, tracking):
    lines, line = [], ""
    for word in text.split(" "):
        test = f"{line} {word}".strip()
        if line and text_width(font, test, tracking) > max_w:
            lines.append(line)
            line = word
        else:
            line = test
    return lines + ([line] if line else [])


def balance(font, text, max_w, tracking):
    """Narrowest width that keeps the same line count: even lines, no one-word last line."""
    lines = wrap(font, text, max_w, tracking)
    lo, hi = max_w * 0.5, max_w
    while hi - lo > 4:
        mid = (lo + hi) / 2
        if len(wrap(font, text, mid, tracking)) == len(lines):
            hi = mid
        else:
            lo = mid
    return wrap(font, text, hi, tracking)


def fit(text, max_w, start, minimum, max_lines):
    text = GLUE.sub(r"\1" + NBSP, " ".join(text.split()))
    size = start
    while True:
        font = load_font(True, size)
        tracking = size * TRACKING
        lines = balance(font, text, max_w, tracking)
        if len(lines) <= max_lines or size <= minimum:
            return font, tracking, lines
        size -= 2


# --- photo ------------------------------------------------------------------

def cover(img, w, h, focus=(0.5, 0.5)):
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = max(w, round(iw * scale)), max(h, round(ih * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = round((nw - w) * focus[0]), round((nh - h) * focus[1])
    return img.crop((left, top, left + w, top + h))


def treat(img, mode):
    if mode == "mono":
        return ImageOps.grayscale(img).convert("RGB")
    if mode == "muted":
        img = ImageEnhance.Color(img).enhance(0.7)
        return ImageEnhance.Contrast(img).enhance(0.95)
    return img


# --- slide ------------------------------------------------------------------

def slide(post, n, total, folder, fmt="3x4"):
    (W, H), photo_top, baseline = FORMATS[fmt]
    s = post["slides"][n - 1]
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    x0 = round(W * SIDE)
    pw = W - 2 * x0
    ph = round(pw * PHOTO_RATIO)
    y0 = round(H * photo_top)
    right = x0 + pw - round(W * TEXT_INSET)
    meta = load_font(False, round(H * 0.0155))
    small = load_font(False, round(H * 0.0125))
    is_end = s["kind"] == "end"

    if not is_end:
        if s.get("image") and (folder / s["image"]).exists():
            img = ImageOps.exif_transpose(Image.open(folder / s["image"])).convert("RGB")
            img = treat(cover(img, pw, ph, tuple(s.get("focus") or (0.5, 0.5))),
                        s.get("treatment") or post.get("treatment", "natural"))
            canvas.paste(img, (x0, y0))
        else:
            draw.rectangle((x0, y0, x0 + pw, y0 + ph), fill=EMPTY)
            draw.text((x0 + pw / 2, y0 + ph / 2), "no image yet", font=meta, fill=META,
                      anchor="mm")

        # meta row above the photo: date left, counter (or handle on the hook) right
        meta_y = y0 - round(H * 0.018)
        if s.get("date"):
            draw_tracked(draw, x0, meta_y, s["date"].lower(), meta, META, 0)
        label = config.HANDLE.lower() if s["kind"] == "hook" else f"{n:02d}/{total:02d}"
        draw.text((x0 + pw, meta_y), label, font=meta, fill=META, anchor="rs")

        # source under the photo
        if s.get("source"):
            draw.text((x0, y0 + ph + round(H * 0.026)), f"source: {s['source']}".lower(),
                      font=small, fill=META, anchor="ls")

    # main text: bottom right, lowercase, stacked upward from the baseline
    text = s["text"].lower()
    if s["kind"] in ("hook", "end"):
        font, tracking, lines = fit(text, pw * 0.86, round(H * 0.042), round(H * 0.03), 3)
    else:
        font, tracking, lines = fit(text, pw * 0.86, round(H * 0.030), round(H * 0.022), 5)
    line_h = round(font.size * 1.18)
    y = round(H * baseline) - line_h * (len(lines) - 1)
    for line in lines:
        draw_tracked(draw, right - text_width(font, line, tracking), y, line, font, INK, tracking)
        y += line_h

    if is_end:
        draw.text((right, round(H * baseline) + round(H * 0.03)), config.HANDLE.lower(),
                  font=meta, fill=META, anchor="rs")
    return canvas


def caption(post):
    credits = []
    for s in post["slides"]:
        c = s.get("credit")
        if c:
            line = f"{c['artist'] or 'unknown'} / {c['license']}".strip()
            if line not in credits:
                credits.append(line)
    parts = [post.get("caption", "").lower(), " ".join(post.get("hashtags", []))]
    if credits:
        parts.append("photos: " + ", ".join(credits))
    return "\n\n".join(p for p in parts if p) + "\n"


def run(folder, fmt="3x4"):
    post = json.loads((folder / "post.json").read_text())
    out = folder / "out" / fmt
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    total = len(post["slides"])
    for n in range(1, total + 1):
        slide(post, n, total, folder, fmt).save(out / f"{n:02d}.png", optimize=True)
    (out / "caption.txt").write_text(caption(post))
    return out
