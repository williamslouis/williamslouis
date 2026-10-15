"""The two AI jobs the studio needs, on either Gemini (free tier) or Claude.

  write(system, prompt, schema)  → dict that matches the JSON schema
  research(prompt)               → plain-text notes, written after searching the web

Provider: STUDIO_PROVIDER=gemini|claude, or picked automatically from whichever key is set
(GEMINI_API_KEY first, then ANTHROPIC_API_KEY).
"""

import json
import os
import time

GEMINI_MODEL = os.environ.get("STUDIO_GEMINI_MODEL", "gemini-flash-latest")
CLAUDE_MODEL = os.environ.get("STUDIO_MODEL", "claude-opus-5-5")


def provider():
    chosen = os.environ.get("STUDIO_PROVIDER", "").lower()
    if chosen in ("gemini", "claude"):
        return chosen
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    raise RuntimeError("no AI key: set GEMINI_API_KEY (free at aistudio.google.com) "
                       "or ANTHROPIC_API_KEY, or use --skeleton")


def model_name():
    return GEMINI_MODEL if provider() == "gemini" else CLAUDE_MODEL


def write(system, prompt, schema, effort="medium"):
    return (_gemini_write if provider() == "gemini" else _claude_write)(system, prompt, schema, effort)


def research(prompt):
    return (_gemini_research if provider() == "gemini" else _claude_research)(prompt)


# --- gemini ------------------------------------------------------------------

def _gemini():
    from google import genai

    return genai.Client()  # reads GEMINI_API_KEY / GOOGLE_API_KEY


def _gemini_call(**kwargs):
    """Free-tier keys hit per-minute limits easily, so wait and retry on 429/503."""
    from google.genai import errors

    client = _gemini()
    for attempt in range(5):
        try:
            return client.models.generate_content(model=GEMINI_MODEL, **kwargs)
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or attempt == 4:
                raise
            wait = 20 * (attempt + 1)
            print(f"  gemini busy ({e.code}), retrying in {wait}s")
            time.sleep(wait)


def _gemini_write(system, prompt, schema, effort):
    from google.genai import types

    response = _gemini_call(
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
        ),
    )
    if not response.text:
        raise RuntimeError(f"gemini returned nothing ({_gemini_reason(response)})")
    return json.loads(response.text)


def _gemini_research(prompt):
    from google.genai import types

    response = _gemini_call(
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch()),
                   types.Tool(url_context=types.UrlContext())],
        ),
    )
    notes = (response.text or "").strip()
    if not notes:
        raise RuntimeError(f"gemini research returned nothing ({_gemini_reason(response)})")
    # Append the pages Google Search actually grounded the answer in.
    meta = response.candidates[0].grounding_metadata if response.candidates else None
    chunks = (meta.grounding_chunks or []) if meta else []
    urls = [f"- {c.web.title}: {c.web.uri}" for c in chunks if c.web]
    if urls:
        notes += "\n\nSearch results used:\n" + "\n".join(dict.fromkeys(urls))
    return notes


def _gemini_reason(response):
    if response.candidates:
        return str(response.candidates[0].finish_reason)
    return str(getattr(response.prompt_feedback, "block_reason", "unknown"))


# --- claude ------------------------------------------------------------------

def _claude_create(**kwargs):
    import anthropic

    response = anthropic.Anthropic().beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        # If a request is declined on safety grounds (possible for wars and attacks), the API
        # retries it on a suitable fallback model in the same call.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        **kwargs,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("claude declined this story")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("response was cut off; try again")
    return response


def _claude_write(system, prompt, schema, effort):
    response = _claude_create(
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(next(b.text for b in response.content if b.type == "text"))


def _claude_research(prompt):
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8},
             {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8}]
    messages = [{"role": "user", "content": prompt}]
    for _ in range(5):  # server tools pause after 10 steps; resend to let them carry on
        response = _claude_create(output_config={"effort": "medium"}, tools=tools,
                                  messages=messages)
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": response.content}]
    return "\n".join(b.text for b in response.content if b.type == "text").strip()
