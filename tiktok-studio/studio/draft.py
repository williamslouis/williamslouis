"""Write a post.json from a Wikipedia article, using Claude and brand.md.

Without ANTHROPIC_API_KEY (or an `ant auth login` profile) it writes a skeleton you fill in.
"""

import json
import re

from . import config, wiki

SCHEMA = {
    "type": "object",
    "properties": {
        "slug": {"type": "string", "description": "kebab-case, 2-6 words"},
        "title": {"type": "string"},
        "event_date": {"type": "string", "description": "YYYY-MM-DD, or YYYY if unknown"},
        "treatment": {"type": "string", "enum": ["natural", "muted", "mono"]},
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["hook", "context", "beat", "turn",
                                                         "outcome", "end"]},
                    "text": {"type": "string"},
                    "date": {"type": "string", "description": "short label, e.g. 09.11.1989, or ''"},
                    "source": {"type": "string", "description": "outlet names, e.g. 'bbc, wikipedia'"},
                    "image_query": {"type": "string",
                                    "description": "wikimedia commons search for a real photo of this exact moment; '' for end slide"},
                    "image_article": {"type": "string",
                                      "description": "wikipedia article title whose photos fit this slide, or ''"},
                },
                "required": ["kind", "text", "date", "source", "image_query", "image_article"],
                "additionalProperties": False,
            },
        },
        "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "fact_check": {"type": "array", "items": {"type": "string"},
                       "description": "each number, date and quote used, with the source sentence it came from"},
    },
    "required": ["slug", "title", "event_date", "treatment", "slides", "caption", "hashtags",
                 "fact_check"],
    "additionalProperties": False,
}

INSTRUCTIONS = """You write carousel posts for the account described in the brand guide below. \
Follow it exactly: structure, word counts, lowercase voice, hook patterns, sources on every fact slide.

Write only from the source material in the user message. Every number, date, name and quote on a \
slide must appear there; list each in fact_check with the sentence it came from. If the material \
is too thin for 6 slides, make fewer slides rather than adding outside facts. For `source`, name \
the outlets the article itself cites for that fact where possible, plus "wikipedia".

For each slide, write an image_query that would find a real, freely licensed photo of that exact \
moment, place or person on Wikimedia Commons (specific nouns and years, no adjectives), and an \
image_article when a Wikipedia article's own photos would fit.

<brand_guide>
{brand}
</brand_guide>"""


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _source_message(art, event):
    parts = [f"Story: {event}" if event else "",
             f"Wikipedia article: {art['title']} ({art['url']})",
             f"<article>\n{art['text']}\n</article>"]
    return "\n\n".join(p for p in parts if p)


def _ask_claude(art, event):
    import anthropic

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=config.MODEL,
        max_tokens=16000,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        # If the request is declined on safety grounds (rare for history, possible for wars and
        # attacks), the API retries it on a suitable fallback model in the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=[{"type": "text",
                 "text": INSTRUCTIONS.format(brand=config.BRAND_FILE.read_text()),
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": _source_message(art, event)}],
    )
    if response.stop_reason == "refusal":
        raise SystemExit("claude declined this story; write it by hand with --skeleton")
    if response.stop_reason == "max_tokens":
        raise SystemExit("draft was cut off; try again")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def _skeleton(art, event):
    lead = art["text"].split("\n")[0][:400]
    slides = [{"kind": "hook", "text": "todo: hook line.", "date": "", "source": "",
               "image_query": art["title"], "image_article": art["title"]}]
    for kind in ("context", "beat", "beat", "turn", "outcome"):
        slides.append({"kind": kind, "text": f"todo: {kind}.", "date": "", "source": "wikipedia",
                       "image_query": art["title"], "image_article": ""})
    slides.append({"kind": "end", "text": "one moment a day.", "date": "", "source": "",
                   "image_query": "", "image_article": ""})
    return {"slug": slugify(art["title"]), "title": art["title"], "event_date": "",
            "treatment": "natural", "slides": slides,
            "caption": f"todo. {lead}", "hashtags": ["#history", "#onthisday"], "fact_check": []}


def run(title, event="", skeleton=False):
    art = wiki.article(title)
    print(f"• article: {art['title']} ({len(art['text']):,} chars)")
    if skeleton:
        post = _skeleton(art, event)
    else:
        print(f"• drafting with {config.MODEL}")
        post = _ask_claude(art, event)
    post["slug"] = slugify(post.get("slug") or art["title"])
    post["wikipedia"] = art["title"]
    post["wikipedia_url"] = art["url"]
    for s in post["slides"]:
        s.setdefault("image", None)
        s.setdefault("focus", [0.5, 0.5])
    folder = config.POSTS_DIR / post["slug"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "post.json"
    if path.exists():
        path.rename(folder / "post.prev.json")
        print("  (kept the old draft as post.prev.json)")
    path.write_text(json.dumps(post, indent=2, ensure_ascii=False))
    return folder
