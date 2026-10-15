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

## automatic: 3 posts every morning

```bash
python -m studio daily                          # → daily/<date>/ + review.md
STUDIO_MIX=news,news,history python -m studio daily
```

What happens:

1. **find**: ranks today's candidates. Wikipedia's on this day, in the news and most read
   lists, plus the BBC/NPR/Guardian headlines.
2. **pick**: Claude acts as editor, choosing the best story for each slot in `STUDIO_MIX` and
   ranking reserves. It avoids anything close to recent posts.
3. **draft**: news slots are **researched live with web search** across at least 2 outlets, then
   written from those notes. History slots are written from the Wikipedia article.
4. **photos + render**: if a story fails at any step (thin research, under half its slides with
   photos), the next reserve takes its place.
5. **review**: `daily/<date>/review.md` has every slide, the flags, the fact check and a caption
   ready to paste, with suggested times (`STUDIO_TIMES`, default 08:00, 13:00, 19:00).
6. **send** (optional): with `STUDIO_DISCORD_WEBHOOK` set, each post lands in a Discord channel as
   slides + caption. On your phone, long-press to save the images, then post them on TikTok.

### running it every day by itself (github actions)

`.github/workflows/daily.yml` runs `daily` at 05:13 UTC, sends to Discord, keeps the slides as a
download for 7 days, and commits the `post.json` files back so no story repeats. Setup, in the
repo's **Settings → Secrets and variables → Actions**:

| name | type | value |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | secret | from console.anthropic.com |
| `STUDIO_DISCORD_WEBHOOK` | secret | Discord: channel settings → integrations → webhooks → copy url |
| `STUDIO_CONTACT` | variable | your email (wikimedia asks for one) |
| `STUDIO_HANDLE` | variable | `@yourhandle` |
| `STUDIO_MIX` | variable | optional, e.g. `news,history,history` |

The workflow file has to sit at the root of a repo's `.github/workflows/`, and scheduled runs only
happen on the default branch. So this folder works best as its own repository.

Cost: about 4–6 Claude calls a day (1 pick, 3 drafts, research for news slots). Actions minutes
are free for public repos.

## by hand

```bash
python -m studio find                    # → stories/2026-10-15.md, ranked
python -m studio make --story 1          # draft + photos + render for candidate #1
```

Or step by step:

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

## news photos

Agency news photos (Reuters, AP, Getty) are copyrighted and can't be used. For news posts, the
photo search uses free photos of the **people, places and organisations involved** from Wikimedia
Commons, not shots of the event itself. Check those slides in the review: if a photo is off, swap
it with `pick`.

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
