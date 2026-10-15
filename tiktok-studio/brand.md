# brand

Working name: **set in `studio/config.py` (`HANDLE`)**. Everything below is the rulebook. The
drafting step sends this whole file to Claude, so editing it changes every future post.

---

## 1. what we are

Minimal photo carousels about big moments: the news that matters today, and the events that
shaped the world on this date in history. One story per post. Real photos, plain facts, no noise.

The feeling is a gallery wall, not a news ticker. White space does the talking. The viewer
should finish the carousel knowing one story properly, in under 30 seconds.

**We are:** calm, exact, curious, a bit dry.
**We are not:** outraged, breathless, partisan, memey, clickbait.

---

## 2. the look

Minimal on purpose, not minimal because it's unfinished. Every slide is built on the same grid,
so when something is missing it reads as a decision.

**The grid** (fractions of width): outer margin 7.3%, text column starts at 44%, text measure
ends at 90%. Two things never move:

1. **the text**: bottom right, left-aligned on the 44% column, Inter Display SemiBold, slightly tight tracking (-1%),
   all lowercase,
   near-black `#0A0A0A`, **one size on every slide** (4.5% of width), max 4 lines, sitting on a
   fixed baseline (91.8% of height on 3:4).
2. **the label**: bottom left on the outer margin, same baseline as the last line of text.
   Inter Display Regular, small, grey `#8C8C8C`. A museum caption: `place, date`. Nothing else.

**Only the photo moves**, between five grid positions. That movement is the art direction:

| layout | photo | used for |
| --- | --- | --- |
| `plate` | full width inside the margins, 4:3 (the reference) | hook, outcome |
| `column` | over the text column only, 4:3 | context, quiet beats |
| `portrait` | left column only, tall 3:4 | people, single objects |
| `band` | edge to edge, 16:9, a little lower | crowds, places, scale |
| `square` | over the text column, 1:1 | details, documents |

Default rhythm: `plate` → `column` → `portrait` → `band` → `square` → … → `plate`. The end
slide has no photo, just the line and the handle as its label.

**What's not on a slide:** slide counters, handles (except the end slide), sources (they go in
the caption), logos, icons, emoji, arrows, boxes, rounded corners, shadows, gradients, grain.

Photo treatment: `natural` by default. `muted` when photos from different decades need to feel
like one set, `mono` for anything pre-1960 or when colour and black-and-white would clash.

Canvases: `3x4` (1080 × 1440, default), `4x5`, and `9x16`, where the baseline rises to 76% so
TikTok's caption and buttons don't cover the text.

---

## 3. the carousel

6 to 8 slides. A hook, a short chronological story, the outcome, a quiet end.

| # | slide | what it does |
| --- | --- | --- |
| 1 | **hook** | the most striking true sentence about the story. Strongest photo. |
| 2 | **context** | who/what/where, in plain words |
| 3–5 | **beats** | what happened, in order. One fact per slide |
| 6 | **turn** | the surprising detail, the human moment, or the mistake |
| 7 | **outcome** | what it changed |
| 8 | **end** | no photo: a quiet line |

**One sentence per slide, 12 words at most.** If a fact needs more, split it over two slides or
move the detail to the caption. Never shrink the text to fit: the renderer warns when a slide is
over. The time and place go in the label, so the sentence doesn't have to carry them.

Every slide gets its own photo, and every fact slide still has a `source`. The sources are
collected into the caption.

---

## 4. voice

- **lowercase everything**, including names, places and acronyms (`nasa`, `un`, `bbc`).
- One short declarative sentence. Full stops. No exclamation marks.
- Cut until it hurts: drop "the government of", "it is said that", "in fact".
- Explain anything technical in plain words, once.
- Digits for numbers (`3`, `1,300`, `£2m`).
- No adjectives doing the work: not "shocking", "insane", "heartbreaking". Let the fact land.
- No opinions, no moralising. If people disagree, say who says what.
- No emoji, no hashtags on slides, no "you won't believe".

### hook patterns

Use one, and only if it's true:

- `the day ___.` → "the day the berlin wall opened by mistake."
- `___ years ago today, ___.` → "36 years ago today, a press conference ended a country."
- `this photo ___.` → "this photo was taken 20 minutes before it all changed."
- `nobody ___.` → "nobody gave the order to open the gate."
- `how ___ in ___.` → "how one sentence ended the cold war in 4 hours."
- `the ___ that ___.` → "the typo that sank a $125m spacecraft."

### end slide lines

"one moment a day." · "that's the whole story." · "follow for tomorrow's." — keep it to a
whisper. Never "smash that follow button".

---

## 5. caption + hashtags

- Caption: 1–2 lowercase sentences that add one detail not on the slides, then the date.
- 3–5 hashtags: 1 broad (`#history` or `#news`), 1–2 topic (`#coldwar`, `#space`),
  1 place, optionally `#onthisday`. No tag spam.
- Sources go after the hashtags: `sources: bbc, wikipedia`. Added automatically.
- Image credits go at the end of the caption: `photos: name / licence, name / licence`.
  This is required for CC BY / CC BY-SA images.

---

## 6. what makes a story

Pick stories that score on at least three of these:

1. **big**: changed a country, an industry, or how people live; or most people have heard of it.
2. **anniversary**: round number today (10, 25, 50, 75, 100 years). The finder scores this.
3. **visual**: there are strong, freely licensed photos of the actual moment.
4. **a turn**: a mistake, coincidence, or human detail most people don't know.
5. **current echo**: something in today's news makes it relevant again.

Avoid: celebrity gossip, deaths as the main hook unless the person shaped history, ongoing
tragedies where facts are unclear, anything we can't source to two reputable outlets.

Sensitive events (wars, attacks, disasters): no graphic photos, no victim close-ups, numbers from
official or academic sources, the tone gets even quieter. Skip the joke-ish hook patterns.

---

## 7. accuracy rules

- Every number, date and quote must appear in the source text the draft was written from.
- If sources disagree, use the more conservative figure or say "about".
- No AI-generated images, ever. Real photos only, with a licence we can credit.
- Logos only when the story is about the company itself.
- Read the draft once against the source before rendering. Automation writes it; a person
  publishes it.
