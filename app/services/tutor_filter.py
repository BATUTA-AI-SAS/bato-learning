"""Post-processing filter for the Socratic tutor.

Strips runnable code answers from the token stream to enforce the no-solution
rule even when the model slips.  The filter is token-stream-aware: callers pass
each SSE chunk through ``filter_chunk`` and the state accumulates across calls.
When a code fence closes, the filter either emits it (safe) or replaces it with
the omission notice.

Usage::

    state = FilterState()
    for raw_chunk in model_stream:
        filtered = filter_chunk(raw_chunk, state)
        if filtered:
            emit(filtered)
    # flush any dangling open block at end of stream
    tail = flush(state)
    if tail:
        emit(tail)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_OMITTED = "(omitido por el mentor)"

# Keywords that, when present inside a code block, mark it as a runnable solution.
_CODE_KEYWORDS = re.compile(r"\b(def |for |while |class )\S")

# A line that looks like a bare function definition followed by a body on the
# VERY NEXT LINE (detected inside plain prose, outside fences).
_DEF_LINE = re.compile(r"^\s*def \w+\s*\(.*\)\s*:")

# Inline backtick content with >2 statements (separated by ; or \n).
_INLINE_CODE = re.compile(r"`([^`]+)`")


@dataclass
class FilterState:
    in_code_block: bool = False
    current_block_lines: list[str] = field(default_factory=list)
    # Carries over partial line text across chunks
    _pending: str = field(default="", repr=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _block_is_runnable(lines: list[str]) -> bool:
    """Return True if the collected fence lines contain executable keywords."""
    body = "\n".join(lines)
    return bool(_CODE_KEYWORDS.search(body))


def _strip_inline_violations(line: str) -> str:
    """Replace inline backtick snippets that contain >2 statements."""
    def _check(m: re.Match) -> str:
        inner = m.group(1)
        stmts = [s.strip() for s in re.split(r";|\n", inner) if s.strip()]
        if len(stmts) > 2:
            return _OMITTED
        return m.group(0)
    return _INLINE_CODE.sub(_check, line)


def _filter_prose_line(line: str, prev_line: str | None) -> str:
    """Apply inline and bare-def filters to a single prose line."""
    # Strip bare def: if this line looks like a def header AND the previous
    # line also looked like one (body follows), replace body with omission.
    if prev_line is not None and _DEF_LINE.match(prev_line):
        # The current line is the body — omit the pair (caller handles prev).
        return _OMITTED
    line = _strip_inline_violations(line)
    return line


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_chunk(text: str, state: FilterState) -> str:
    """Filter one raw SSE chunk.

    Returns the filtered text to emit (may be empty if inside an open block).
    Accumulates state for the next call.
    """
    if not text:
        return text

    # Combine pending carry-over with new text.
    combined = state._pending + text
    state._pending = ""

    # Split on newlines but keep the delimiter so we can detect open lines.
    # We only process complete lines; an incomplete last line is held in pending.
    parts = combined.split("\n")
    if not combined.endswith("\n"):
        # Last part is incomplete — hold it over.
        state._pending = parts.pop()
    else:
        # Remove the empty string that follows the trailing \n.
        if parts and parts[-1] == "":
            parts.pop()

    out_lines: list[str] = []
    prev_line: str | None = None

    for line in parts:
        stripped = line.strip()

        # Detect fence open/close.
        if stripped.startswith("```"):
            if not state.in_code_block:
                # Opening fence — start accumulating.
                state.in_code_block = True
                state.current_block_lines = [line]
                prev_line = line
                continue
            else:
                # Closing fence — decide fate of the whole block.
                state.current_block_lines.append(line)
                if _block_is_runnable(state.current_block_lines):
                    out_lines.append(_OMITTED)
                else:
                    out_lines.extend(state.current_block_lines)
                state.in_code_block = False
                state.current_block_lines = []
                prev_line = line
                continue

        if state.in_code_block:
            state.current_block_lines.append(line)
            prev_line = line
            continue

        # --- Prose line processing ---
        filtered = _filter_prose_line(line, prev_line)
        # If the previous line was a def header, replace that already-emitted
        # line too — but since we haven't emitted it yet (we emit after the
        # loop iteration), we can replace it in out_lines.
        if prev_line is not None and _DEF_LINE.match(prev_line) and out_lines:
            out_lines[-1] = _OMITTED
        out_lines.append(filtered)
        prev_line = line

    result = "\n".join(out_lines)
    # Re-add the trailing newline if the original combined text ended with one
    # (i.e., state._pending was empty before we stripped the trailing empty part).
    if combined.endswith("\n") and result:
        result += "\n"
    return result


def flush(state: FilterState) -> str:
    """Flush any remaining open code block or pending text at stream end."""
    out: list[str] = []

    if state._pending:
        pending = state._pending
        state._pending = ""
        # Apply prose filters to the dangling line.
        pending = _strip_inline_violations(pending)
        out.append(pending)

    if state.in_code_block and state.current_block_lines:
        if _block_is_runnable(state.current_block_lines):
            out.append(_OMITTED)
        else:
            out.extend(state.current_block_lines)
        state.in_code_block = False
        state.current_block_lines = []

    return "\n".join(out)
