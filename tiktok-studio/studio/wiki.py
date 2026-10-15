"""Small Wikimedia API client: feeds, article text, pageviews, Commons images."""

import html
import re
import time
from datetime import date, timedelta
from urllib.parse import quote

import requests

from . import config

session = requests.Session()
session.headers["User-Agent"] = config.USER_AGENT

FEED = "https://api.wikimedia.org/feed/v1/wikipedia/{lang}"
WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
REST = "https://{lang}.wikipedia.org/api/rest_v1"


def get_json(url, params=None, retries=3):
    for attempt in range(retries):
        r = session.get(url, params=params, timeout=30)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


def strip_html(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


# --- feeds -------------------------------------------------------------------

def featured(day: date):
    """Wikipedia's daily feed: 'in the news', most read, selected anniversaries."""
    url = f"{FEED.format(lang=config.LANG)}/featured/{day:%Y/%m/%d}"
    return get_json(url)


def on_this_day(day: date):
    """Every recorded event for this calendar date (selected + events)."""
    url = f"{FEED.format(lang=config.LANG)}/onthisday/all/{day:%m/%d}"
    return get_json(url)


def pageviews(title, days=30):
    """Average daily views over the last `days` days. 0 if unknown."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days)
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"{config.LANG}.wikipedia/all-access/user/{quote(title.replace(' ', '_'), safe='')}"
        f"/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    )
    try:
        items = get_json(url).get("items", [])
    except requests.HTTPError:
        return 0
    return sum(i["views"] for i in items) / max(len(items), 1)


# --- articles ----------------------------------------------------------------

def article(title):
    """Plain-text article plus its canonical title and url."""
    data = get_json(WIKI_API.format(lang=config.LANG), {
        "action": "query", "format": "json", "formatversion": 2, "redirects": 1,
        "prop": "extracts|info", "explaintext": 1, "inprop": "url", "titles": title,
    })
    page = data["query"]["pages"][0]
    if page.get("missing"):
        raise SystemExit(f"no wikipedia article called {title!r}")
    return {"title": page["title"], "url": page["fullurl"], "text": page.get("extract", "")}


def article_files(title):
    """File names used on an article, in page order (lead image first)."""
    url = f"{REST.format(lang=config.LANG)}/page/media-list/{quote(title.replace(' ', '_'), safe='')}"
    try:
        items = get_json(url).get("items", [])
    except requests.HTTPError:
        return []
    return [i["title"] for i in items if i.get("type") == "image" and "title" in i]


# --- commons -----------------------------------------------------------------

def commons_search(query, limit=20):
    data = get_json(COMMONS_API, {
        "action": "query", "format": "json", "formatversion": 2,
        "list": "search", "srnamespace": 6, "srlimit": limit,
        "srsearch": f"{query} filetype:bitmap",
    })
    return [hit["title"] for hit in data["query"]["search"]]


def image_info(file_titles, width=2000):
    """Url, size, mime and licence for up to 50 File: titles per call."""
    out = {}
    titles = [t if t.startswith("File:") else f"File:{t}" for t in file_titles]
    for i in range(0, len(titles), 50):
        data = get_json(COMMONS_API, {
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": width, "titles": "|".join(titles[i:i + 50]),
        })
        for page in data["query"].get("pages", []):
            info = (page.get("imageinfo") or [None])[0]
            if not info:
                continue
            meta = info.get("extmetadata", {})
            field = lambda k: strip_html(meta.get(k, {}).get("value", ""))
            out[page["title"]] = {
                "file": page["title"],
                "url": info.get("thumburl") or info["url"],
                "page": info.get("descriptionurl", ""),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "mime": info.get("mime", ""),
                "license": field("LicenseShortName"),
                "artist": field("Artist") or field("Credit"),
                "usage_terms": field("UsageTerms"),
                "description": field("ImageDescription")[:300],
            }
    return out


def download(url, path):
    r = session.get(url, timeout=60)
    r.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path
