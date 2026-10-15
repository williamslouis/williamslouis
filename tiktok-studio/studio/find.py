"""Find and rank story candidates.

Three sources, all free and keyless:
  history  Wikipedia "on this day" for the target date(s)
  news     Wikipedia "in the news" (curated big events, already linked to articles)
  trending Wikipedia most-read articles yesterday
  rss      optional headlines from config.NEWS_FEEDS, ranked by how many outlets carry them

Ranking favours what makes a good post (see brand.md section 6): round anniversaries, a usable
lead photo, real public interest (pageviews), and the channel's interests. Stories already
posted (any posts/*/post.json with the same article) are skipped.
"""

import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta

from . import config, wiki


def _posted_articles():
    done = set()
    for p in config.POSTS_DIR.glob("*/post.json"):
        try:
            done.add(json.loads(p.read_text())["wikipedia"].replace("_", " ").lower())
        except (KeyError, ValueError):
            pass
    return done


def _anniversary_bonus(years):
    for step, bonus in ((100, 4), (50, 3.5), (75, 3), (25, 2.5), (10, 1.5), (5, 0.5)):
        if years > 0 and years % step == 0:
            return bonus
    return 0


def _interest_bonus(text):
    text = text.lower()
    return min(sum(1 for word in config.INTERESTS if word in text) * 0.5, 1.5)


def _image_bonus(page):
    img = page.get("originalimage") or page.get("thumbnail")
    if not img:
        return 0
    return 1.5 + (0.5 if img.get("width", 0) >= 1000 else 0)


def _main_page(pages):
    """The linked article that best represents the event (the one with a photo, first)."""
    with_img = [p for p in pages if p.get("originalimage")]
    return (with_img or pages or [{}])[0]


def _candidate(kind, day, text, page, score, **extra):
    return {
        "kind": kind,
        "date": day.isoformat(),
        "text": text,
        "wikipedia": page.get("titles", {}).get("canonical") or page.get("title", ""),
        "description": page.get("description", ""),
        "image": (page.get("originalimage") or page.get("thumbnail") or {}).get("source", ""),
        "score": round(score, 2),
        **extra,
    }


def history(day):
    data = wiki.on_this_day(day)
    seen, out = set(), []
    for bucket, base in (("selected", 3), ("events", 0)):
        for ev in data.get(bucket, []):
            text = wiki.strip_html(ev.get("text", ""))
            if text in seen or "year" not in ev:
                continue
            seen.add(text)
            page = _main_page(ev.get("pages", []))
            years = day.year - ev["year"]
            score = (base + _anniversary_bonus(years) + _image_bonus(page)
                     + _interest_bonus(text + " " + page.get("description", ""))
                     + min(len(ev.get("pages", [])), 5) * 0.2)
            out.append(_candidate("history", day, text, page, score,
                                  year=ev["year"], years_ago=years))
    return out


def news_and_trending(day):
    # The featured feed for day D carries "most read" for D-1, which is the freshest available.
    data = wiki.featured(day)
    most_read = {a.get("title"): a.get("views", 0)
                 for a in data.get("mostread", {}).get("articles", [])}
    out = []
    for item in data.get("news", []):
        page = _main_page(item.get("links", []))
        views = max((most_read.get(p.get("title"), 0) for p in item.get("links", [])), default=0)
        score = 4 + _image_bonus(page) + (math.log10(views) - 3 if views > 1000 else 0)
        out.append(_candidate("news", day, wiki.strip_html(item.get("story", "")), page, score,
                              views=views))
    for a in data.get("mostread", {}).get("articles", [])[:25]:
        if a.get("title", "").startswith(("Special:", "Main_Page", "Wikipedia:")):
            continue
        score = math.log10(max(a.get("views", 1), 1)) - 3 + _image_bonus(a) + _interest_bonus(
            a.get("description", "") + " " + a.get("extract", ""))
        out.append(_candidate("trending", day, a.get("extract", "")[:280], a, score,
                              views=a.get("views", 0)))
    return out


_WORD = re.compile(r"[a-z]{4,}")


def rss(feeds=None):
    """Headlines clustered across outlets. More outlets on one story = bigger story."""
    items = []
    for url in feeds or config.NEWS_FEEDS:
        try:
            root = ET.fromstring(wiki.session.get(url, timeout=20).content)
        except Exception as e:  # one dead feed shouldn't stop the run
            print(f"  skipped feed {url}: {e}")
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            items.append({"title": title, "link": it.findtext("link") or "", "feed": url,
                          "words": set(_WORD.findall(title.lower()))})
    clusters = []
    for it in items:
        for c in clusters:
            overlap = len(it["words"] & c["words"]) / max(len(it["words"] | c["words"]), 1)
            if overlap >= 0.3:
                c["items"].append(it)
                c["words"] |= it["words"]
                break
        else:
            clusters.append({"words": set(it["words"]), "items": [it]})
    out = []
    for c in clusters:
        outlets = {i["feed"].split("/")[2] for i in c["items"]}
        lead = c["items"][0]
        out.append({
            "kind": "rss", "date": date.today().isoformat(), "text": lead["title"],
            "wikipedia": "", "description": "", "image": "",
            "links": [i["link"] for i in c["items"]][:4],
            "score": round(len(outlets) * 1.5 + _interest_bonus(lead["title"]), 2),
        })
    return out


def run(start: date, days=1, views=True, use_rss=False, top=25):
    done = _posted_articles()
    cands = []
    for i in range(days):
        day = start + timedelta(days=i)
        print(f"• {day}: on this day")
        cands += history(day)
        if i == 0:
            print(f"• {day}: in the news + trending")
            cands += news_and_trending(day)
    if use_rss:
        print("• rss feeds")
        cands += rss()

    cands = [c for c in cands if c["wikipedia"].replace("_", " ").lower() not in done]
    cands.sort(key=lambda c: c["score"], reverse=True)
    seen = set()  # one entry per article, keeping the best-scoring one
    cands = [c for c in cands if not c["wikipedia"] or not (c["wikipedia"] in seen or seen.add(c["wikipedia"]))]

    # Pageviews are one request each, so only check the shortlist.
    if views:
        print("• pageviews for shortlist")
        for c in cands[:top * 2]:
            if c["wikipedia"] and "views" not in c:
                v = wiki.pageviews(c["wikipedia"])
                c["views"] = round(v)
                c["score"] = round(c["score"] + (math.log10(v) - 2.5 if v > 300 else 0), 2)
        cands.sort(key=lambda c: c["score"], reverse=True)

    cands = cands[:top]
    for n, c in enumerate(cands, 1):
        c["id"] = n
    return cands


def save(cands, start):
    config.STORIES_DIR.mkdir(exist_ok=True)
    stem = config.STORIES_DIR / f"{start.isoformat()}"
    stem.with_suffix(".json").write_text(json.dumps(cands, indent=2, ensure_ascii=False))
    lines = [f"# story candidates from {start}", "",
             "| # | score | kind | when | story | article | photo |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for c in cands:
        when = f"{c['year']} ({c['years_ago']}y)" if "year" in c else c["date"]
        story = c["text"].replace("|", "/")[:140]
        lines.append(f"| {c['id']} | {c['score']} | {c['kind']} | {when} | {story} | "
                     f"{c['wikipedia']} | {'yes' if c['image'] else '—'} |")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    return stem
