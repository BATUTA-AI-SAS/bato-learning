/* pyodide_runner.js — execute Python exercises in the browser.
 * For exercises with runner="backend", POST to /api/exercises/{id}/backend. */

let pyodide = null;
let pyodideReady = null;
const status = document.getElementById("py-status");

async function initPyodide() {
  if (!status) return;
  status.textContent = "cargando Python (~10 MB)…";
  status.className = "py-status loading";
  try {
    pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.0/full/",
    });
    status.textContent = "cargando pyyaml…";
    try { await pyodide.loadPackage("pyyaml"); } catch (_) { /* opcional */ }
    status.textContent = "✓ Python listo";
    status.className = "py-status ready";
  } catch (e) {
    status.textContent = "✗ Python no cargó (revisa internet)";
    status.className = "py-status err";
    throw e;
  }
}

async function runPyodide(userCode, testCode) {
  await pyodideReady;
  pyodide.globals.set("__USER_CODE", userCode);
  pyodide.globals.set("__TEST_CODE", testCode || "");
  pyodide.runPython(`
import sys, io
__cap = io.StringIO()
__old = sys.stdout
sys.stdout = __cap
__ns = {'__name__': '__main__'}
__err = None
try:
    exec(__USER_CODE, __ns)
    if __TEST_CODE:
        exec(__TEST_CODE, __ns)
except AssertionError as e:
    __err = str(e) or 'una aserción falló'
except Exception as e:
    __err = f'{type(e).__name__}: {e}'
finally:
    sys.stdout = __old
__captured = __cap.getvalue()
`);
  return {
    output: pyodide.globals.get("__captured") || "",
    error: pyodide.globals.get("__err"),
  };
}

async function runBackend(exerciseId, userCode) {
  const r = await fetch(`/api/exercises/${exerciseId}/backend`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code: userCode }),
  });
  if (!r.ok) throw new Error(`backend ${r.status}`);
  return await r.json();
}

async function reportAttempt(exerciseId, payload) {
  const r = await fetch(`/api/exercises/${exerciseId}/pyodide`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) return null;
  return await r.json();
}

function celebrate(passed, exerciseEl, result) {
  if (!passed) return;
  exerciseEl.classList.add("passed");
  const badge = exerciseEl.querySelector(".ex-header .badge");
  if (badge && !badge.classList.contains("passed")) badge.classList.add("passed");
  if (window.__BL && result) {
    if (result.xp_awarded) window.__BL.announceXp(result.xp_awarded, "Ejercicio pasado");
    if (result.newly_unlocked) window.__BL.announceUnlocks(result.newly_unlocked);
  }
}

function wireExercises() {
  document.querySelectorAll(".exercise").forEach((ex) => {
    const id = parseInt(ex.dataset.exerciseId);
    const runner = ex.dataset.runner || "pyodide";
    const editor = ex.querySelector(".code-editor");
    const initial = editor.value;
    const out = ex.querySelector(".output");
    const runBtn = ex.querySelector(".run-ex");
    const solBtn = ex.querySelector(".show-sol");
    const resetBtn = ex.querySelector(".reset-ex");
    const testEl = ex.querySelector(".test-code");
    const solEl = ex.querySelector(".solution");

    runBtn?.addEventListener("click", async () => {
      out.textContent = "ejecutando…";
      out.className = "output";
      const started = performance.now();
      try {
        if (runner === "backend") {
          const r = await runBackend(id, editor.value);
          out.textContent = (r.output || "") + (r.error ? "\n✗ " + r.error : "\n✓ tests pasan");
          out.className = "output " + (r.passed ? "ok" : "err");
          celebrate(r.passed, ex, r);
        } else {
          const r = await runPyodide(editor.value, testEl?.textContent || "");
          const passed = !r.error;
          out.textContent = (r.output || "") + (r.error ? "\n✗ " + r.error : "\n✓ tests pasan");
          out.className = "output " + (passed ? "ok" : "err");
          const reported = await reportAttempt(id, {
            code: editor.value,
            passed,
            output: r.output || "",
            error: r.error || "",
            duration_ms: Math.round(performance.now() - started),
          });
          celebrate(passed, ex, reported);
        }
      } catch (e) {
        out.textContent = "Error: " + e.message;
        out.className = "output err";
      }
    });

    solBtn?.addEventListener("click", () => {
      if (solEl) {
        editor.value = solEl.textContent.trim();
        editor.dispatchEvent(new Event("input"));
        solBtn.textContent = "solución cargada";
        solBtn.disabled = true;
        setTimeout(() => { solBtn.textContent = "Ver solución"; solBtn.disabled = false; }, 2200);
      }
    });

    resetBtn?.addEventListener("click", () => {
      editor.value = initial;
      editor.dispatchEvent(new Event("input"));
      out.textContent = "";
      out.className = "output";
    });
  });
}

pyodideReady = initPyodide();
document.addEventListener("DOMContentLoaded", wireExercises);
