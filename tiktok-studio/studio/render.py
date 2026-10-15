"""Render post.json into carousel slides (PNG) plus caption.txt. Layout spec: brand.md section 2.

The page is a fixed grid. Two things never move: the text column (bottom right, left-aligned,
one size) and the label (bottom left, on the same baseline). Only the photo moves, snapping to
one of a few grid positions so the carousel reads like a gallery wall.
"""

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from . import config

BG = "#FFFFFF"
INK = "#0A0A0A"
META = "#8C8C8C"
EMPTY = "#EDEDED"

FORMATS = {
    #        size          photo top  text baseline
    "3x4":  ((1080, 1440), 0.144, 0.918),
    "4x5":  ((1080, 1350), 0.120, 0.915),
    "9x16": ((1080, 1920), 0.170, 0.760),
}

# Grid, as fractions of width. Measured from the reference.
MARGIN = 0.073        # outer margin
COLUMN = 0.440        # where the text column (and some photos) start
TEXT_RIGHT = 0.900    # right edge of the text measure
GUTTER = 0.037        # space between the two columns

TEXT_SIZE = 0.0453    # one size for every slide and format, fraction of width
LABEL_SIZE = 0.018    # fraction of width
TRACKING = 0.02       # fraction of font size
LEADING = 1.16
MAX_LINES = 4
MAX_WORDS = 12

# Photo positions on the grid: (left, right, aspect h/w, top offset). left/right are fractions
# of width; None for top offset means "the format's photo top".
LAYOUTS = {
    "plate":    (MARGIN, 1 - MARGIN, 3 / 4, None),           # the reference: wide inset photo
    "column":   (COLUMN, 1 - MARGIN, 3 / 4, None),           # smaller, sits over the text column
    "portrait": (MARGIN, COLUMN - GUTTER, 4 / 3, None),      # tall, left column only
    "band":     (0.0, 1.0, 9 / 16, 0.05),                    # edge to edge, a little lower
    "square":   (COLUMN, 1 - MARGIN, 1.0, None),             # square over the text column
}
# Default rhythm for the middle slides; hook and outcome are always "plate".
RHYTHM = ["column", "portrait", "band", "square"]

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
            if not Path(path).is_absolute() and path[1:3] != ":/":
                path = config.ROOT / path
            if Path(path).exists():
                _font_cache[key] = ImageFont.truetype(str(path), size, index=index)
                break
        else:
            raise SystemExit("no usable font found; put Helvetica-Bold.ttf in fonts/")
    return _font_cache[key]


# --- text -------------------------------------------------------------------

NBSP = "\u00a0"
# keep "155 km", "3 october", "11:30 pm" etc. on one line
GLUE = re.compile(r"(\d) (?=[a-z%£$€]{1,9}\b)")


def text_width(font, s, tracking):
    return font.getlength(s) + tracking * max(len(s) - 1, 0)


def draw_tracked(draw, x, y, s, font, fill, tracking):
    """Draw with letter spacing while keeping the font's own kerning (anchor: left baseline)."""
    for i, ch in enumerate(s):
        draw.text((x + font.getlength(s[:i]) + i * tracking, y), ch, font=font, fill=fill,
                  anchor="ls")


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
    lo, hi = max_w * 0.6, max_w
    while hi - lo > 4:
        mid = (lo + hi) / 2
        if len(wrap(font, text, mid, tracking)) == len(lines):
            hi = mid
        else:
            lo = mid
    return wrap(font, text, hi, tracking)


def check_copy(n, text):
    words = len(text.split())
    if words > MAX_WORDS:
        print(f"  ! slide {n}: {words} words (max {MAX_WORDS}). cut it, don't shrink it.")


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


def layout_for(post, n):
    s = post["slides"][n - 1]
    if s.get("layout") in LAYOUTS:
        return s["layout"]
    if s["kind"] in ("hook", "outcome"):
        return "plate"
    middle = [i for i, x in enumerate(post["slides"], 1) if x["kind"] not in ("hook", "outcome", "end")]
    return RHYTHM[middle.index(n) % len(RHYTHM)] if n in middle else "plate"


# --- slide ------------------------------------------------------------------

def slide(post, n, total, folder, fmt="3x4"):
    (W, H), photo_top, baseline_f = FORMATS[fmt]
    s = post["slides"][n - 1]
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    baseline = round(H * baseline_f)
    col_x = round(W * COLUMN)
    margin_x = round(W * MARGIN)

    font = load_font(True, round(W * TEXT_SIZE))
    tracking = font.size * TRACKING
    text = GLUE.sub(r"\1" + NBSP, " ".join(s["text"].lower().split()))
    check_copy(n, s["text"])
    lines = balance(font, text, W * TEXT_RIGHT - col_x, tracking)
    if len(lines) > MAX_LINES:
        print(f"  ! slide {n}: {len(lines)} lines (max {MAX_LINES})")
    line_h = round(font.size * LEADING)
    text_top = baseline - line_h * (len(lines) - 1) - font.size

    if s["kind"] != "end":
        left, right, aspect, offset = LAYOUTS[layout_for(post, n)]
        x0, x1 = round(W * left), round(W * right)
        pw = x1 - x0
        ph = round(pw * aspect)
        y0 = round(H * (photo_top + (offset or 0)))
        # never let a photo crowd the text: keep at least one text line of air above it
        ph = min(ph, text_top - line_h * 2 - y0)
        if s.get("image") and (folder / s["image"]).exists():
            img = ImageOps.exif_transpose(Image.open(folder / s["image"])).convert("RGB")
            img = treat(cover(img, pw, ph, tuple(s.get("focus") or (0.5, 0.5))),
                        s.get("treatment") or post.get("treatment", "natural"))
            canvas.paste(img, (x0, y0))
        else:
            draw.rectangle((x0, y0, x1, y0 + ph), fill=EMPTY)

    y = baseline - line_h * (len(lines) - 1)
    for line in lines:
        draw_tracked(draw, col_x, y, line, font, INK, tracking)
        y += line_h

    # the label: bottom left, same baseline as the last line of text
    label = config.HANDLE if s["kind"] == "end" else (s.get("label") or s.get("date") or "")
    if label:
        small = load_font(False, round(W * LABEL_SIZE))
        draw_tracked(draw, margin_x, baseline, label.lower(), small, META, small.size * 0.03)
    return canvas


def caption(post):
    sources, credits = [], []
    for s in post["slides"]:
        for src in (s.get("source") or "").split(","):
            if src.strip() and src.strip().lower() not in sources:
                sources.append(src.strip().lower())
        c = s.get("credit")
        if c:
            line = f"{c['artist'] or 'unknown'} / {c['license']}".strip()
            if line not in credits:
                credits.append(line)
    parts = [post.get("caption", "").lower(), " ".join(post.get("hashtags", []))]
    if sources:
        parts.append("sources: " + ", ".join(sources))
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
