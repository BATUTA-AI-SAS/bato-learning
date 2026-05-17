"""Tests for the Socratic tutor post-processing filter."""
from __future__ import annotations

from app.services.tutor_filter import FilterState, filter_chunk, flush

_OMITTED = "(omitido por el mentor)"


def test_single_chunk_def_block_is_stripped():
    """A complete runnable def block in one chunk yields the omission notice."""
    text = "```python\ndef add(a, b):\n    return a + b\n```\n"
    state = FilterState()
    result = filter_chunk(text, state)
    assert _OMITTED in result
    assert "def add" not in result
    assert "return" not in result


def test_socratic_response_passes_through():
    """A normal Socratic reply without code is not touched."""
    text = "¿qué pasa si amount es 1000?\n"
    state = FilterState()
    result = filter_chunk(text, state)
    assert result == text
    assert _OMITTED not in result


def test_code_block_split_across_two_chunks_yields_replacement():
    """A runnable block arriving in two chunks is assembled and replaced."""
    chunk1 = "```python\n"
    chunk2 = "def add():\n  return 1\n```\n"
    state = FilterState()
    out1 = filter_chunk(chunk1, state)
    # First chunk opens the fence — nothing emitted yet.
    assert out1 == ""
    out2 = filter_chunk(chunk2, state)
    combined = out1 + out2
    assert _OMITTED in combined
    assert "def add" not in combined


def test_short_inline_backtick_survives():
    """Inline `print(x)` (1 statement) is not stripped."""
    text = "Puedes usar `print(x)` para inspeccionar el valor.\n"
    state = FilterState()
    result = filter_chunk(text, state)
    assert "`print(x)`" in result
    assert _OMITTED not in result
