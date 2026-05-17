"""Centralized Jinja2 templates with custom filters."""
from __future__ import annotations

import json
import re

from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

from .services.glossary import apply_glossary_tooltips

# html=True allows <details>/<summary> and other raw HTML from trusted
# module markdown (content is repo-controlled, never user-submitted).
_md = (
    MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})
    .enable("table")
    .enable("strikethrough")
)

templates = Jinja2Templates(directory="app/templates")

# Regex patterns for inline exercise/quiz markers emitted by markdown-it
# when the source contains HTML comments (html=False strips them, so we
# match the raw source markers before rendering).
_INLINE_EX_RE = re.compile(r"<!--\s*INLINE_EXERCISE:\s*([\w-]+)\s*-->")
_INLINE_QUIZ_RE = re.compile(r"<!--\s*INLINE_QUIZ:\s*([\w-]+)\s*-->")

# Match ALL h2 headings in the module body (each section = 1 checkpoint).
# Captures group 1 = title text. Track 0 modules don't use numbered headings;
# we slugify the title for a stable checkpoint_id.
_CHECKPOINT_H2_RE = re.compile(r"<h2>([^<]+?)</h2>", re.IGNORECASE)


def _slugify_title(title: str) -> str:
    """Lowercase, ASCII-fold, replace non-alphanum with single dashes."""
    import unicodedata

    norm = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return slug[:40] or "section"


def _replace_inline_markers(text: str) -> str:
    """Replace INLINE_EXERCISE/QUIZ HTML comments with anchor divs."""
    text = _INLINE_EX_RE.sub(
        lambda m: f'<div class="inline-exercise-anchor" data-slug="{m.group(1)}"></div>',
        text,
    )
    text = _INLINE_QUIZ_RE.sub(
        lambda m: f'<div class="inline-quiz-anchor" data-slug="{m.group(1)}"></div>',
        text,
    )
    return text


def _mark_checkpoints(html: str) -> str:
    """Add class="checkpoint" and data-checkpoint-id to every <h2> in body."""
    def _repl(m: re.Match) -> str:
        title = m.group(1)
        slug = _slugify_title(title)
        return (
            f'<h2 class="checkpoint" data-checkpoint-id="{slug}">'
            f"{title}</h2>"
        )
    return _CHECKPOINT_H2_RE.sub(_repl, html)


def _markdown(text: str) -> str:
    if not text:
        return ""
    # Pre-process: replace inline markers with fenced divs that survive
    # markdown-it's html=False setting.  We convert each marker to a
    # bare <div> tag on its own paragraph; markdown-it preserves block-level
    # raw HTML when html=True on a secondary renderer or — simpler — we swap
    # them for unique sentinel strings, render, then restore them.
    _EX_SENTINEL = "BLINEXS_{slug}_BLINEXE"
    _QUIZ_SENTINEL = "BLINQUIZS_{slug}_BLINQUIZE"

    sentinels: list[tuple[str, str, str]] = []  # (sentinel, kind, slug)

    def _ex_sentinel(m: re.Match) -> str:
        slug = m.group(1)
        key = f"BLINEXS{len(sentinels)}E"
        sentinels.append((key, "exercise", slug))
        return f"\n\n{key}\n\n"

    def _quiz_sentinel(m: re.Match) -> str:
        slug = m.group(1)
        key = f"BLINQUIZS{len(sentinels)}E"
        sentinels.append((key, "quiz", slug))
        return f"\n\n{key}\n\n"

    text = _INLINE_EX_RE.sub(_ex_sentinel, text)
    text = _INLINE_QUIZ_RE.sub(_quiz_sentinel, text)

    html = _md.render(text)

    # Restore sentinels as anchor divs
    for key, kind, slug in sentinels:
        css_class = f"inline-{kind}-anchor"
        anchor = f'<div class="{css_class}" data-slug="{slug}"></div>'
        # markdown-it may wrap the sentinel in <p>; replace the whole <p>
        html = re.sub(
            rf"<p>\s*{re.escape(key)}\s*</p>",
            anchor,
            html,
        )
        # fallback: bare sentinel (shouldn't happen)
        html = html.replace(key, anchor)

    # Mark checkpoint headings
    html = _mark_checkpoints(html)
    # Apply glossary tooltips (first occurrence of each term)
    html = apply_glossary_tooltips(html)
    return html


def _track_label(track: str) -> str:
    return {
        "0": "0 · Cimientos (de cero)",
        "A": "A · Python pragmático",
        "B": "B · Web full-stack",
        "C": "C · Datos y persistencia",
        "D": "D · Operación",
        "E": "E · Agentes IA",
        "F": "F · Playbook (casos de uso)",
    }.get(track, track)


def _dept_label(ext_id: str) -> str:
    """For Track F entries, return the department code (FIN/CTA/...) or empty."""
    if not ext_id.startswith("F-"):
        return ""
    parts = ext_id.split("-")
    if len(parts) >= 2:
        return parts[1]
    return ""


def _fromjson(value: str) -> dict:
    """Parse a JSON string to a dict; returns {} on empty or invalid input."""
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


templates.env.filters["md"] = _markdown
templates.env.filters["track_label"] = _track_label
templates.env.filters["dept_label"] = _dept_label
templates.env.filters["fromjson"] = _fromjson
