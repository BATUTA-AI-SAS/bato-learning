"""
lint_track0_terms.py — scan Track 0 .md and .yaml files for forbidden terms.

Prints path:line:term for each violation and exits with code 1 if any are found.

Exclusions (per spec):
  - async / await     : allowed in A07 citation (any file containing "A07")
  - PyPI              : allowed in 00-08 and 00-16
  - virtualenv        : allowed in 00-08
  - lockfile          : allowed in 00-08

Run:
    uv run python -m scripts.lint_track0_terms
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Forbidden terms and their per-file exclusion rules.
# Each entry: (pattern_regex, exclusion_callable(path) -> bool)
# If exclusion returns True, the term is ALLOWED in that file.
# ---------------------------------------------------------------------------

def _always_excluded(_path: Path) -> bool:  # never excluded
    return False


def _a07_file(path: Path) -> bool:
    """async/await are allowed when the file contains a citation to A07."""
    try:
        return "A07" in path.read_text(encoding="utf-8")
    except Exception:
        return False


def _pypi_file(path: Path) -> bool:
    return path.stem in ("00-08", "00-16") or any(
        p in path.name for p in ("00-08", "00-16")
    )


def _virtualenv_file(path: Path) -> bool:
    return "00-08" in path.name


def _lockfile_file(path: Path) -> bool:
    return "00-08" in path.name


# (display_name, compiled_regex, exclusion_fn)
FORBIDDEN: list[tuple[str, re.Pattern[str], object]] = [
    ("bytecode",              re.compile(r"\bbytecode\b", re.IGNORECASE),           _always_excluded),
    ("AST",                   re.compile(r"\bAST\b"),                               _always_excluded),
    ("abstract syntax tree",  re.compile(r"abstract syntax tree", re.IGNORECASE),   _always_excluded),
    ("type hint",             re.compile(r"\btype hint", re.IGNORECASE),             _always_excluded),
    ("IEEE 754",              re.compile(r"IEEE\s*754", re.IGNORECASE),              _always_excluded),
    ("heap",                  re.compile(r"\bheap\b", re.IGNORECASE),                _always_excluded),
    ("stack frame",           re.compile(r"\bstack frame\b", re.IGNORECASE),         _always_excluded),
    ("PEP 8",                 re.compile(r"\bPEP\s*8\b", re.IGNORECASE),             _always_excluded),
    ("PEP 484",               re.compile(r"\bPEP\s*484\b", re.IGNORECASE),           _always_excluded),
    ("metaclass",             re.compile(r"\bmetaclass\b", re.IGNORECASE),           _always_excluded),
    ("__slots__",             re.compile(r"__slots__"),                              _always_excluded),
    ("GIL",                   re.compile(r"\bGIL\b"),                               _always_excluded),
    ("asyncio internals",     re.compile(r"asyncio internals", re.IGNORECASE),       _always_excluded),
    ("descriptor",            re.compile(r"\bdescriptor\b", re.IGNORECASE),          _always_excluded),
    ("async",                 re.compile(r"\basync\b", re.IGNORECASE),               _a07_file),
    ("await",                 re.compile(r"\bawait\b", re.IGNORECASE),               _a07_file),
    ("PyPI",                  re.compile(r"\bPyPI\b"),                               _pypi_file),
    ("virtualenv",            re.compile(r"\bvirtualenv\b", re.IGNORECASE),          _virtualenv_file),
    ("lockfile",              re.compile(r"\blockfile\b", re.IGNORECASE),            _lockfile_file),
]

CONTENT_DIR = Path(__file__).parent.parent / "app" / "content" / "00"


def _details_mask(lines: list[str]) -> list[bool]:
    """Return a boolean mask: True for lines inside <details>...</details> blocks.

    Terms inside <details> are considered intentionally gated as optional
    deep-dives — they are allowed even if they appear in the forbidden list.
    """
    mask = [False] * len(lines)
    depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if stripped.startswith("<details"):
            depth += 1
        mask[i] = depth > 0
        if stripped.startswith("</details"):
            depth = max(0, depth - 1)
    return mask


def scan() -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []

    files = sorted(
        f for f in CONTENT_DIR.rglob("*")
        if f.suffix in (".md", ".yaml") and f.is_file()
    )

    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            print(f"ERROR reading {path}: {exc}", file=sys.stderr)
            continue

        # Build mask: lines inside <details> blocks are exempt
        in_details = _details_mask(lines)

        for term_name, pattern, exclusion_fn in FORBIDDEN:
            if exclusion_fn(path):  # term is allowed in this file
                continue
            for lineno, line in enumerate(lines, start=1):
                if in_details[lineno - 1]:
                    continue  # inside <details>: allowed
                if pattern.search(line):
                    violations.append((path, lineno, term_name))

    return violations


def main() -> None:
    violations = scan()

    if not violations:
        print("lint_track0_terms: 0 violations — Track 0 is clean.")
        sys.exit(0)

    for path, lineno, term in violations:
        rel = path.relative_to(CONTENT_DIR.parent.parent.parent)
        print(f"{rel}:{lineno}:{term}")

    print(
        f"\nlint_track0_terms: {len(violations)} violation(s) found.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
