# tiktok studio

Makes minimal TikTok photo carousels about big news and big moments in history. It doesn't post
anything. It finds the story, writes the slides, gets licensed photos and renders the PNGs, and
you post them yourself.

The look: a white page, a photo set inside it, lowercase Inter Display in the bottom right.
The rulebook is in [`brand.md`](brand.md), and the drafting step reads that file on every run.

```
find  →  draft  →  images  →  (pick)  →  render  →  you review + post
```

## setup

```bash
cd tiktok-studio
pip install -r requirements.txt
export STUDIO_CONTACT="you@example.com"   # wikimedia requires a contact in the user agent
export STUDIO_HANDLE="@yourhandle"
export ANTHROPIC_API_KEY=...               # only for `draft`; or use --skeleton
```

Fonts: Inter Display is bundled in `fonts/` (free, OFL), so nothing to install. To try another,
see `fonts/README.md`.

## daily flow

```bash
python -m studio find                    # → stories/2026-10-15.md, ranked
python -m studio make --story 1          # draft + photos + render for candidate #1
```

Or step by step, which is better when you want control:

```bash
python -m studio draft --story 3                 # or: draft "Apollo 11"
#   edit posts/<slug>/post.json: check every line against fact_check
python -m studio images <slug>                   # best licensed photo per slide
#   open posts/<slug>/images/04-sheet.jpg to see the other 5 options
python -m studio pick <slug> 4 2                 # slide 4 → option 2
python -m studio images <slug> 5                 # re-search slide 5 after editing its image_query
python -m studio render <slug>                   # → posts/<slug>/out/3x4/*.png + caption.txt
python -m studio render <slug> --format 9x16     # full-screen version with the TikTok-safe text zone
```

Plan a week ahead: `python -m studio find --days 7 --rss`.

## how stories are found

All free and keyless:

| source | what | why |
| --- | --- | --- |
| wikipedia on this day | every recorded event on this date | the history backbone |
| wikipedia in the news | big current events, picked by editors | already vetted as "big" |
| wikipedia most read | what people looked up yesterday | real public interest |
| rss (`--rss`) | bbc / npr / guardian headlines | stories carried by several outlets rank higher |

Score = round anniversary (100/50/75/25/10 years) + has a usable lead photo + 30-day pageviews
+ your `INTERESTS` in `studio/config.py`. Anything already in `posts/` is skipped, so you never
repeat a story.

## how photos are found

For each slide: photos from the matching Wikipedia article first, then a Wikimedia Commons search
on the slide's `image_query`. Only public domain / CC0 / CC BY / CC BY-SA bitmaps are kept, with
logos, maps and flags ranked down, and landscape high-res photos ranked up. Credits are written
into `caption.txt` automatically. CC BY photos legally require that credit, so keep it in the
caption when you post.

## post.json

One file per post, and you can edit any of it by hand. Per slide: `kind`, `text`, `date`,
`source`, `image_query`, `image_article`, `image`, `focus` (`[x, y]` from 0–1, where the crop
centres), and optionally `treatment` (`natural` / `muted` / `mono`) to override the post's.

`posts/fall-of-the-berlin-wall/post.json` is a finished example.
