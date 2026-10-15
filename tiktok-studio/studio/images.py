"""Find, licence-check and download a photo for every slide.

Order of preference per slide:
  1. photos used on the slide's `image_article` (or the post's main article for the hook)
  2. Wikimedia Commons search for `image_query`
Only freely licensed bitmaps are kept (public domain, CC0, CC BY, CC BY-SA). The top candidates
for each slide are saved to images/candidates.json and a contact sheet, so a bad pick is one
`pick` command away.
"""

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

from . import render, wiki

FREE = re.compile(r"public domain|^pd|cc0|cc[- ]by(?![- ]nc)|no restrictions", re.I)
NOT_FREE = re.compile(r"fair use|non-free|\bnc\b|\bnd\b|copyrighted", re.I)
JUNK = re.compile(r"logo|icon|flag of|coat of arms|signature|map|diagram|chart|seal of|symbol|"
                  r"\.svg|locator|blank|button|commons-|wiki", re.I)
BITMAP = {"image/jpeg", "image/png", "image/webp", "image/tiff"}


def is_free(info):
    lic = f"{info['license']} {info['usage_terms']}"
    return bool(FREE.search(lic)) and not NOT_FREE.search(lic)


def score(info, from_article, query):
    w, h = info["width"], info["height"]
    if not w or not h:
        return -99
    s = 0.0
    s += 2 if from_article else 0
    s += min(w, 3000) / 1000                       # resolution, capped
    s -= abs((w / h) - 4 / 3) * 1.5                # closer to the 4:3 frame crops better
    s -= 3 if JUNK.search(info["file"]) and not JUNK.search(query) else 0
    s -= 2 if w < 1000 else 0
    return s


def candidates(slide, post, used):
    query = slide.get("image_query") or ""
    article = slide.get("image_article") or (post.get("wikipedia", "") if slide["kind"] == "hook" else "")
    from_article = wiki.article_files(article)[:15] if article else []
    searched = wiki.commons_search(query) if query else []
    infos = wiki.image_info(dict.fromkeys(from_article + searched))
    article_set = {f if f.startswith("File:") else f"File:{f}" for f in from_article}
    good = []
    for title, info in infos.items():
        if info["mime"] not in BITMAP or not is_free(info) or title in used:
            continue
        if min(info["width"], info["height"]) < 600:
            continue
        good.append({**info, "score": round(score(info, title in article_set, query), 2)})
    good.sort(key=lambda i: i["score"], reverse=True)
    return good[:6]


def contact_sheet(cands, path):
    thumb_w, thumb_h, pad = 360, 270, 12
    sheet = Image.new("RGB", (pad + 3 * (thumb_w + pad), pad + 2 * (thumb_h + pad + 24)), "white")
    draw = ImageDraw.Draw(sheet)
    font = render.load_font(bold=True, size=20)
    for n, c in enumerate(cands):
        x = pad + (n % 3) * (thumb_w + pad)
        y = pad + (n // 3) * (thumb_h + pad + 24)
        try:
            img = Image.open(c["local"]).convert("RGB")
            sheet.paste(render.cover(img, thumb_w, thumb_h), (x, y))
        except Exception:
            draw.rectangle((x, y, x + thumb_w, y + thumb_h), fill="#eee")
        draw.text((x, y + thumb_h + 4), f"{n + 1}  {c['license'][:30]}", font=font, fill="#111")
    sheet.save(path)


def run(folder, slides=None, sheets=True):
    post_path = folder / "post.json"
    post = json.loads(post_path.read_text())
    img_dir = folder / "images"
    img_dir.mkdir(exist_ok=True)
    all_cands = json.loads((img_dir / "candidates.json").read_text()) \
        if (img_dir / "candidates.json").exists() else {}
    used = {s.get("image_file") for s in post["slides"] if s.get("image_file")}
    missing = []

    for n, slide in enumerate(post["slides"], 1):
        if slides and n not in slides:
            continue
        if slide["kind"] == "end" or not (slide.get("image_query") or slide["kind"] == "hook"):
            continue
        if slide.get("image") and not slides:
            continue  # already has one; pass explicit slide numbers to redo
        print(f"• slide {n}: {slide.get('image_query') or post.get('wikipedia', '')}")
        cands = candidates(slide, post, used)
        if not cands:
            print("  no free photo found; edit image_query and rerun")
            missing.append(n)
            continue
        for i, c in enumerate(cands, 1):
            ext = ".png" if c["mime"] == "image/png" else ".jpg"
            c["local"] = str(img_dir / f"{n:02d}-c{i}{ext}")
            wiki.download(c["url"], img_dir / f"{n:02d}-c{i}{ext}")
        all_cands[str(n)] = cands
        choose(post, n, cands[0], folder)
        used.add(cands[0]["file"])
        if sheets:
            contact_sheet(cands, img_dir / f"{n:02d}-sheet.jpg")

    (img_dir / "candidates.json").write_text(json.dumps(all_cands, indent=2, ensure_ascii=False))
    post_path.write_text(json.dumps(post, indent=2, ensure_ascii=False))
    return missing


def choose(post, slide_no, cand, folder):
    slide = post["slides"][slide_no - 1]
    slide["image"] = str(Path(cand["local"]).relative_to(folder))
    slide["image_file"] = cand["file"]
    slide["credit"] = {"artist": cand["artist"][:80], "license": cand["license"],
                       "page": cand["page"]}


def pick(folder, slide_no, cand_no):
    post_path = folder / "post.json"
    post = json.loads(post_path.read_text())
    cands = json.loads((folder / "images" / "candidates.json").read_text())[str(slide_no)]
    choose(post, slide_no, cands[cand_no - 1], folder)
    post_path.write_text(json.dumps(post, indent=2, ensure_ascii=False))
    print(f"slide {slide_no} → candidate {cand_no}: {cands[cand_no - 1]['file']}")
