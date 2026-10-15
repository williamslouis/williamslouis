"""One command for the whole day: find → pick 3 → draft → photos → render → review sheet.

  python -m studio daily                         # default mix: news, history, history
  STUDIO_MIX=news,news,history python -m studio daily

Output goes to daily/<date>/: one folder of slides per post, plus review.md with captions,
warnings and fact checks. With STUDIO_DISCORD_WEBHOOK set, each post is also sent to a Discord
channel so you can save the slides straight to your phone.
"""

import json
import os
import shutil
from datetime import date

from . import config, draft, find, images, render

MIX = [m.strip() for m in os.environ.get("STUDIO_MIX", "news,history,history").split(",")]
TIMES = [t.strip() for t in os.environ.get("STUDIO_TIMES", "08:00,13:00,19:00").split(",")]
SLOT_KINDS = {"news": ("news", "rss"), "history": ("history",)}

PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "slot": {"type": "string", "enum": ["news", "history"]},
                    "angle": {"type": "string",
                              "description": "the turn or detail that makes it worth a post, one line"},
                },
                "required": ["id", "slot", "angle"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["picks"],
    "additionalProperties": False,
}


def _brand_section(title):
    text = config.BRAND_FILE.read_text()
    start = text.find(title)
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else None]


def editor_pick(cands, mix):
    """Ask Claude to choose like an editor: ranked order per slot, best first, with reserves."""
    import anthropic

    recent = sorted(config.POSTS_DIR.glob("*/post.json"), key=lambda p: p.stat().st_mtime)[-30:]
    recent_titles = [json.loads(p.read_text()).get("title", "") for p in recent]
    shortlist = [{k: c.get(k) for k in ("id", "kind", "text", "wikipedia", "description",
                                        "year", "years_ago", "views", "score")}
                 for c in cands if any(c["kind"] in SLOT_KINDS.get(m, ()) for m in set(mix))]
    prompt = (
        f"Pick stories for today's posts. Slots: {', '.join(mix)}.\n"
        "Return every candidate worth posting, best first, so failures can fall back to the next. "
        "Avoid two posts on the same subject, and anything too close to recent posts.\n\n"
        f"{_brand_section('## 6. what makes a story')}\n\n"
        f"Recent posts: {json.dumps(recent_titles)}\n\n"
        f"Candidates:\n{json.dumps(shortlist, ensure_ascii=False)}"
    )
    response = anthropic.Anthropic().beta.messages.create(
        model=config.MODEL, max_tokens=8000,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": PICK_SCHEMA}},
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    by_id = {c["id"]: c for c in cands}
    return [({**by_id[p["id"]], "slot": p["slot"]}, p["angle"])
            for p in json.loads(text or '{"picks": []}')["picks"] if p["id"] in by_id]


def heuristic_pick(cands, mix):
    return [({**c, "slot": slot}, "") for c in cands for slot in set(mix)
            if c["kind"] in SLOT_KINDS.get(slot, ())]


def _make(cand, angle, fmt):
    folder = draft.run_candidate(cand, angle)
    missing = images.run(folder)
    post = json.loads((folder / "post.json").read_text())
    photo_slides = [n for n, s in enumerate(post["slides"], 1) if s["kind"] != "end"]
    if len(missing) > len(photo_slides) // 2:
        raise RuntimeError(f"only found photos for {len(photo_slides) - len(missing)} slides")
    out = render.run(folder, fmt)
    return folder, out, missing, list(render.warnings)


def run(day=None, fmt="3x4", mix=None, use_editor=True, send=True):
    day = day or date.today()
    mix = mix or MIX
    cands = find.run(day, days=1, views=True, use_rss=True, top=40)
    find.save(cands, day)

    try:
        ranked = editor_pick(cands, mix) if use_editor else heuristic_pick(cands, mix)
    except Exception as e:  # the editor is a nice-to-have; fall back to the score order
        print(f"  editor pick failed ({e}); using scores")
        ranked = []
    ranked += heuristic_pick(cands, mix)  # reserves, in score order, if the picks run out

    day_dir = config.ROOT / "daily" / day.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    made, tried = [], set()
    for n, slot in enumerate(mix, 1):
        for cand, angle in ranked:
            if cand["slot"] != slot or cand["id"] in tried:
                continue
            tried.add(cand["id"])
            print(f"\n=== post {n} ({slot}): {cand['text'][:80]}")
            try:
                folder, out, missing, warnings = _make(cand, angle, fmt)
            except (Exception, SystemExit) as e:
                print(f"  skipped: {e}")
                continue
            dest = day_dir / f"{n}-{folder.name}"
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(out, dest)
            made.append({"n": n, "slot": slot, "folder": folder, "dest": dest,
                         "missing": missing, "warnings": warnings})
            break
        else:
            print(f"  no usable {slot} story today")

    review = write_review(day, day_dir, made)
    print(f"\n{len(made)}/{len(mix)} posts ready → {review}")
    if send and os.environ.get("STUDIO_DISCORD_WEBHOOK"):
        for m in made:
            send_discord(m)
    return made


def write_review(day, day_dir, made):
    lines = [f"# posts for {day}", ""]
    for m in made:
        post = json.loads((m["folder"] / "post.json").read_text())
        when = TIMES[m["n"] - 1] if m["n"] <= len(TIMES) else ""
        flags = m["warnings"] + [f"slide {s}: no photo" for s in m["missing"]]
        lines += [
            f"## {m['n']}. {post['title']}  ·  {m['slot']}  ·  post at {when}",
            "",
            f"- [ ] read every slide against the fact check below",
            f"- [ ] posted",
            f"- slides: `{m['dest'].relative_to(config.ROOT)}/`",
            "",
            *(f"> ⚠ {f}" for f in flags),
            "" if flags else "",
            "**slides**", "",
            *(f"{i}. {s['text']}" for i, s in enumerate(post["slides"], 1)),
            "", "**caption** (paste as is)", "", "```",
            (m["dest"] / "caption.txt").read_text().strip(), "```", "",
            "**fact check**", "",
            *(f"- {f}" for f in post.get("fact_check", [])),
            "", "---", "",
        ]
    path = day_dir / "review.md"
    path.write_text("\n".join(lines))
    return path


def send_discord(m):
    """Post one carousel to a Discord channel: caption as text, slides as attachments."""
    import requests

    caption = (m["dest"] / "caption.txt").read_text()
    pngs = sorted(m["dest"].glob("*.png"))[:10]  # discord allows 10 files per message
    note = f"**post {m['n']} · {m['slot']}**" + (" · ⚠ check review.md" if m["warnings"] or m["missing"] else "")
    files = {f"files[{i}]": (p.name, p.read_bytes(), "image/png") for i, p in enumerate(pngs)}
    r = requests.post(os.environ["STUDIO_DISCORD_WEBHOOK"],
                      data={"content": f"{note}\n```\n{caption[:1800]}\n```"}, files=files, timeout=60)
    if r.status_code >= 300:
        print(f"  discord send failed: {r.status_code} {r.text[:200]}")
