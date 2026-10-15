"""tiktok studio: find stories, draft posts, pull photos, render carousels.

  python -m studio find                      rank today's candidates → stories/<date>.md
  python -m studio find --days 7 --rss       plan a week ahead, add news headlines
  python -m studio draft "Fall of the Berlin Wall"
  python -m studio draft --story 3           draft candidate #3 from today's list
  python -m studio images <slug>             fetch a licensed photo for each slide
  python -m studio pick <slug> 4 2           slide 4 → candidate 2 (see images/04-sheet.jpg)
  python -m studio render <slug> [--format 3x4|4x5|9x16]
  python -m studio make "Apollo 11"          draft + images + render in one go
"""

import argparse
import json
import sys
from datetime import date

from . import config, draft, find, images, render


def _folder(slug):
    folder = config.POSTS_DIR / slug
    if not (folder / "post.json").exists():
        sys.exit(f"no post at {folder}/post.json")
    return folder


def _story(n, day):
    path = config.STORIES_DIR / f"{day}.json"
    if not path.exists():
        sys.exit(f"run `python -m studio find` first ({path} missing)")
    cand = next((c for c in json.loads(path.read_text()) if c["id"] == n), None)
    if not cand or not cand["wikipedia"]:
        sys.exit(f"story {n} has no wikipedia article; draft it by title instead")
    return cand["wikipedia"], cand["text"]


def main():
    p = argparse.ArgumentParser(prog="studio", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find", help="rank story candidates")
    f.add_argument("--date", type=date.fromisoformat, default=date.today())
    f.add_argument("--days", type=int, default=1, help="look ahead this many days of history")
    f.add_argument("--rss", action="store_true", help="also cluster news headlines")
    f.add_argument("--no-views", action="store_true", help="skip pageview lookups (faster)")
    f.add_argument("--top", type=int, default=25)

    for name in ("draft", "make"):
        d = sub.add_parser(name, help="write post.json" if name == "draft" else "draft+images+render")
        d.add_argument("title", nargs="?", help="wikipedia article title")
        d.add_argument("--story", type=int, help="candidate number from `find`")
        d.add_argument("--date", type=date.fromisoformat, default=date.today())
        d.add_argument("--skeleton", action="store_true", help="no AI; write a template")
        d.add_argument("--format", default="3x4", choices=render.FORMATS)

    i = sub.add_parser("images", help="fetch photos for a post")
    i.add_argument("slug")
    i.add_argument("slides", nargs="*", type=int, help="only these slides (re-fetches)")

    k = sub.add_parser("pick", help="swap a slide's photo for another candidate")
    k.add_argument("slug")
    k.add_argument("slide", type=int)
    k.add_argument("candidate", type=int)

    r = sub.add_parser("render", help="render slides + caption")
    r.add_argument("slug")
    r.add_argument("--format", default="3x4", choices=render.FORMATS)

    a = p.parse_args()

    if a.cmd == "find":
        cands = find.run(a.date, a.days, views=not a.no_views, use_rss=a.rss, top=a.top)
        stem = find.save(cands, a.date)
        print(f"\n{len(cands)} candidates → {stem}.md\n")
        for c in cands[:10]:
            print(f"  {c['id']:>2}  {c['score']:>5}  {c['kind']:<8} {c['text'][:90]}")
    elif a.cmd in ("draft", "make"):
        if a.story:
            title, event = _story(a.story, a.date)
        elif a.title:
            title, event = a.title, ""
        else:
            sys.exit("give an article title or --story N")
        folder = draft.run(title, event, skeleton=a.skeleton)
        print(f"→ {folder}/post.json")
        if a.cmd == "make":
            images.run(folder)
            out = render.run(folder, a.format)
            print(f"→ {out}")
    elif a.cmd == "images":
        images.run(_folder(a.slug), slides=a.slides or None)
    elif a.cmd == "pick":
        images.pick(_folder(a.slug), a.slide, a.candidate)
    elif a.cmd == "render":
        out = render.run(_folder(a.slug), a.format)
        print(f"→ {out}")


if __name__ == "__main__":
    main()
