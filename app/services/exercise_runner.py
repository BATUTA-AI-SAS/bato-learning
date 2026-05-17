"""Backend runner for exercises whose `runner != "pyodide"`.

Pyodide-runner exercises execute in the browser and post the outcome back. Backend
runner exercises execute here in a subprocess for isolation. Used by Tracks C/D/E
exercises that need real libraries (SQLAlchemy, anthropic, etc.).
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import textwrap
from pathlib import Path


WRAPPER = """\
import sys, io, json, traceback
USER = {user!r}
TEST = {test!r}

cap = io.StringIO()
old = sys.stdout
sys.stdout = cap
ns = {{"__name__": "__main__"}}
err = None
err_kind = None
try:
    exec(USER, ns)
    if TEST:
        exec(TEST, ns)
except AssertionError as e:
    err = str(e) or "una aserción falló"
    err_kind = "assert"
except Exception as e:
    err = f"{{type(e).__name__}}: {{e}}"
    err_kind = "exception"
finally:
    sys.stdout = old

print("__BATO_OUTCOME__" + json.dumps({{
    "output": cap.getvalue(),
    "error": err,
    "error_kind": err_kind,
}}))
"""


async def run_backend_exercise(
    user_code: str, test_code: str, *, timeout_s: float = 8.0
) -> dict:
    """Run user code + test code in a subprocess. Returns {passed, output, error}."""
    src = textwrap.dedent(WRAPPER.format(user=user_code, test=test_code))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError:
            proc.kill()
            return {
                "passed": False,
                "output": "",
                "error": f"timeout > {timeout_s}s",
            }
        text = out.decode(errors="replace")
        outcome = _parse(text)
        if outcome is None:
            return {
                "passed": False,
                "output": text,
                "error": err.decode(errors="replace") or "no outcome marker",
            }
        return {
            "passed": outcome["error"] is None,
            "output": outcome["output"],
            "error": outcome["error"] or "",
        }
    finally:
        os.unlink(path)


def _parse(text: str) -> dict | None:
    marker = "__BATO_OUTCOME__"
    idx = text.rfind(marker)
    if idx < 0:
        return None
    try:
        return json.loads(text[idx + len(marker):].strip())
    except json.JSONDecodeError:
        return None
