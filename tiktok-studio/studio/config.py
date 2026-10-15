"""Settings. Everything can be overridden with an environment variable of the same name."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
STORIES_DIR = ROOT / "stories"
FONTS_DIR = ROOT / "fonts"
BRAND_FILE = ROOT / "brand.md"

HANDLE = os.environ.get("STUDIO_HANDLE", "@yourhandle")

# Wikimedia asks every client to identify itself with a way to reach the owner.
CONTACT = os.environ.get("STUDIO_CONTACT", "set STUDIO_CONTACT to an email or url")
USER_AGENT = f"tiktok-studio/0.1 ({CONTACT})"

LANG = os.environ.get("STUDIO_LANG", "en")

MODEL = os.environ.get("STUDIO_MODEL", "claude-opus-5-5")

# Topics that get a small boost in story ranking. Edit to steer the channel.
INTERESTS = [
    "space", "moon", "rocket", "nasa", "apollo", "satellite",
    "computer", "internet", "software", "phone", "apple", "microsoft", "google", "invent",
    "war", "treaty", "revolution", "independence", "election", "wall", "empire",
    "earthquake", "eruption", "hurricane", "disaster", "sank", "crash",
    "olympic", "world cup", "record", "first",
    "album", "film", "released", "premiere",
]

# Optional RSS feeds for current news. Headlines that show up in several feeds rank higher.
NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.theguardian.com/world/rss",
]
