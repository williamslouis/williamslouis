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

Based on the reference: white page, one photograph sitting inside it, a single line of heavy
Helvetica in the bottom right. Nothing else competes.

| element | spec (3:4 canvas, 1080 × 1440) |
| --- | --- |
| background | pure white `#FFFFFF` |
| photo | inset box, 7.3% side margins, top at 14.4% of height, 4:3 landscape, no border, no rounding, no shadow |
| main text | Helvetica Bold (fallback: Liberation Sans Bold / Arial Bold), **all lowercase**, near-black `#0A0A0A`, slight positive tracking, right-aligned to the photo's right edge minus 2.7%, baseline at 91.8% of height |
| meta text | Helvetica Regular, lowercase, grey `#8C8C8C`, small. Date top-left above the photo, slide counter top-right, source under the photo on the left |
| colour | none. The photo is the only colour on the slide |
| graphics | none. No logos, stickers, emoji, arrows, gradients or boxes |

Other canvases: `4x5` (1080 × 1350) and `9x16` (1080 × 1920). In 9:16 the text sits higher
(baseline 76%) so TikTok's caption and buttons don't cover it.

Photo treatment: `natural` by default. Use `muted` (less saturation) when photos from different
decades sit in one carousel and need to feel like a set, `mono` for anything pre-1960 or when
colour photos would clash with black-and-white ones.

---

## 3. the carousel

6 to 8 slides. Structure borrowed from the best-performing explainer carousels: a hook,
then a short chronological story where every slide is one fact with a source, then the outcome.

| # | slide | what it does | words |
| --- | --- | --- | --- |
| 1 | **hook** | the most striking true sentence about the story. Strongest photo. | 4–10 |
| 2 | **context** | who/what/where, explained so a 14-year-old gets it | 15–30 |
| 3–5 | **beats** | what happened, in order. One fact per slide. Start with the date | 15–30 |
| 6 | **turn** | the surprising detail, the human moment, or the mistake | 15–30 |
| 7 | **outcome** | what it changed, with a number if possible | 15–30 |
| 8 | **end** (optional) | text only, no photo: a quiet line + follow prompt | 3–10 |

Every fact slide carries a `source` line (publication names, not URLs), shown small under the
photo. Every slide gets its own photo; never reuse one inside a carousel.

---

## 4. voice

- **lowercase everything**, including names, places and the start of sentences. Proper acronyms
  stay readable: write `nasa`, `un`, `bbc` in lowercase too.
- Short declarative sentences. Full stops, no exclamation marks, no question marks on fact slides.
- Lead fact slides with time: "in 1961, …", "at 6:53pm, …", "two days later, …".
- Explain anything technical in plain words, once: "graphene os, free software that replaces the
  system running your phone".
- Digits for numbers (`3`, `1,300`, `£2m`), and give them scale ("about the population of leeds").
- No adjectives doing the work: not "shocking", "insane", "heartbreaking". Let the fact land.
- No opinions, no "we think", no moralising. If people disagree about something, say who
  says what.
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
