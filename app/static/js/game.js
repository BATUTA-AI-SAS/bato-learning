/* game.js — Puzzle engine for bato-learning game UI.
 *
 * Loaded on level_player pages. Reads window.__BL_LEVEL_PAYLOAD and
 * window.__BL_LEVEL_KIND to pick the correct widget renderer.
 *
 * Puzzle kinds implemented:
 *   order_steps   — native HTML5 drag-and-drop sortable list
 *   multi_choice  — radio cards; single correct answer with feedback
 *   predict       — show code block + textarea; compare with expected_output
 *   fill_blank    — inline input fields embedded in code template
 *   tf            — true/false buttons with optional countdown
 *   code          — monospace textarea + Pyodide runner + test runner
 *   boss          — sequential sub-puzzles (one per step)
 *   decision      — option cards with tradeoff reveal; all choices valid
 */

"use strict";

// ---------------------------------------------------------------------------
// Globals set by the template
// ---------------------------------------------------------------------------
const LEVEL_SLUG   = window.__BL_LEVEL_SLUG  || "";
const LEVEL_KIND   = window.__BL_LEVEL_KIND  || "";
const LEVEL_PAYLOAD = window.__BL_LEVEL_PAYLOAD || {};
const NEXT_LEVEL_URL = window.__BL_NEXT_LEVEL_URL || "/game";

// ---------------------------------------------------------------------------
// Concept popup queue
// ---------------------------------------------------------------------------
function runConceptPopups(concepts, onDone) {
  const overlay = document.getElementById("concept-overlay");
  if (!overlay || !concepts || concepts.length === 0) { onDone(); return; }

  const titleEl    = overlay.querySelector(".concept-modal h2");
  const analogyEl  = overlay.querySelector(".concept-analogy");
  const exampleEl  = overlay.querySelector(".concept-example");
  const progressEl = overlay.querySelector(".concept-progress");
  const doneBtn    = overlay.querySelector(".btn-concept-done");

  let idx = 0;

  function showConcept(i) {
    const c = concepts[i];
    titleEl.textContent    = c.title;
    analogyEl.innerHTML    = c.analogy_md || "";
    exampleEl.textContent  = c.example_md || "";
    if (!c.example_md) exampleEl.style.display = "none";
    else               exampleEl.style.display = "";
    progressEl.textContent = `${i + 1} de ${concepts.length}`;
    doneBtn.textContent    = (i < concepts.length - 1) ? "Siguiente" : "Entendido";
    overlay.classList.remove("hidden");

    // Mark concept seen (fire-and-forget)
    fetch("/api/game/concept-seen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ concept_slug: c.slug }),
    }).catch(() => {});
  }

  doneBtn.addEventListener("click", () => {
    idx++;
    if (idx < concepts.length) {
      showConcept(idx);
    } else {
      overlay.classList.add("hidden");
      onDone();
    }
  });

  showConcept(0);
}

// ---------------------------------------------------------------------------
// Submit attempt to API
// ---------------------------------------------------------------------------
function submitAttempt({ passed, hintUsed, payload, durationSeconds }) {
  return fetch("/api/game/attempt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      level_slug:       LEVEL_SLUG,
      passed:           passed,
      hint_used:        hintUsed,
      payload:          payload,
      duration_seconds: durationSeconds,
    }),
  }).then((r) => r.json());
}

// ---------------------------------------------------------------------------
// Show success / failure
// ---------------------------------------------------------------------------
function showSuccess(xp, nextUrl) {
  const el = document.getElementById("success-overlay");
  if (!el) return;
  el.querySelector(".success-xp").textContent  = `+${xp} XP`;
  const nextBtn = el.querySelector(".btn-next-level");
  if (nextBtn) nextBtn.href = nextUrl || NEXT_LEVEL_URL;
  el.classList.add("visible");
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showWrong(msg) {
  const el = document.getElementById("wrong-feedback");
  if (!el) return;
  el.textContent = msg || "Respuesta incorrecta. Revisa la pista e inténtalo de nuevo.";
  el.classList.add("visible");
  setTimeout(() => el.classList.remove("visible"), 4000);
}

// ---------------------------------------------------------------------------
// Hint toggle
// ---------------------------------------------------------------------------
function wireHint(hintUsedRef) {
  const btn  = document.getElementById("hint-btn");
  const panel = document.getElementById("hint-panel");
  if (!btn || !panel) return;
  btn.addEventListener("click", () => {
    panel.classList.toggle("visible");
    if (panel.classList.contains("visible")) {
      hintUsedRef.value = true;
      btn.textContent = "Ocultar pista";
    } else {
      btn.textContent = "Ver pista";
    }
  });
}

// ---------------------------------------------------------------------------
// Timer
// ---------------------------------------------------------------------------
function startTimer() {
  const start = Date.now();
  return () => Math.round((Date.now() - start) / 1000);
}

// ===========================================================================
// PUZZLE RENDERERS
// ===========================================================================

// ---------------------------------------------------------------------------
// order_steps
// ---------------------------------------------------------------------------
function renderOrderSteps(container, payload) {
  const steps = payload.steps || [];
  const correctOrder = payload.correct_order || steps.map((_, i) => i);

  // Shuffle for display
  const indices = steps.map((_, i) => i);
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();

  const ul = document.createElement("ul");
  ul.className = "steps-list";
  ul.setAttribute("id", "steps-sortable");

  indices.forEach((origIdx, pos) => {
    const li = document.createElement("li");
    li.className = "step-item";
    li.draggable = true;
    li.dataset.origIdx = origIdx;

    li.innerHTML = `
      <span class="drag-handle" aria-hidden="true">&#8597;</span>
      <span class="step-index">${pos + 1}</span>
      <span class="step-text">${escapeHtml(steps[origIdx])}</span>
    `;
    ul.appendChild(li);
  });

  // Native drag-and-drop
  let dragSrc = null;

  ul.addEventListener("dragstart", (e) => {
    dragSrc = e.target.closest(".step-item");
    if (dragSrc) dragSrc.classList.add("dragging");
  });
  ul.addEventListener("dragend", () => {
    document.querySelectorAll(".step-item").forEach((el) => {
      el.classList.remove("dragging", "drag-over");
    });
    dragSrc = null;
    reindex(ul);
  });
  ul.addEventListener("dragover", (e) => {
    e.preventDefault();
    const target = e.target.closest(".step-item");
    if (!target || target === dragSrc) return;
    document.querySelectorAll(".step-item.drag-over").forEach((el) => el.classList.remove("drag-over"));
    target.classList.add("drag-over");
    const rect = target.getBoundingClientRect();
    const mid  = rect.top + rect.height / 2;
    if (e.clientY < mid) {
      ul.insertBefore(dragSrc, target);
    } else {
      ul.insertBefore(dragSrc, target.nextSibling);
    }
  });
  ul.addEventListener("dragleave", (e) => {
    const t = e.target.closest(".step-item");
    if (t) t.classList.remove("drag-over");
  });

  container.innerHTML = `<div class="widget-title">Ordena los pasos</div>`;
  container.appendChild(ul);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Verificar orden";
  container.appendChild(verifyBtn);

  const successEl = document.createElement("div");
  successEl.id = "success-overlay";
  successEl.className = "success-overlay";
  successEl.innerHTML = `
    <div class="success-xp"></div>
    <div class="success-msg">Orden correcto.</div>
    <a class="btn-next-level" href="${NEXT_LEVEL_URL}">Siguiente nivel &rarr;</a>
  `;
  container.appendChild(successEl);

  const wrongEl = document.createElement("div");
  wrongEl.id = "wrong-feedback";
  wrongEl.className = "wrong-feedback";
  wrongEl.textContent = "Ese orden no es correcto. Revisa la pista e inténtalo de nuevo.";
  container.appendChild(wrongEl);

  verifyBtn.addEventListener("click", () => {
    const current = Array.from(ul.querySelectorAll(".step-item")).map((li) => parseInt(li.dataset.origIdx, 10));
    const correct = arraysEqual(current, correctOrder);
    submitAttempt({
      passed: correct,
      hintUsed: hintUsed.value,
      payload: { submitted_order: current },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (correct) {
        showSuccess(data.xp_awarded, NEXT_LEVEL_URL);
        verifyBtn.disabled = true;
      } else {
        showWrong("Ese orden no es correcto. Revisa la lógica paso a paso.");
      }
    });
  });
}

function reindex(ul) {
  ul.querySelectorAll(".step-item .step-index").forEach((el, i) => {
    el.textContent = i + 1;
  });
}

// ---------------------------------------------------------------------------
// multi_choice
// ---------------------------------------------------------------------------
function renderMultiChoice(container, payload) {
  const options = payload.options || [];
  const letters = "ABCDE";

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();
  let selected = null;
  let answered = false;

  container.innerHTML = `<div class="widget-title">Selecciona la respuesta correcta</div>`;

  const listEl = document.createElement("div");
  listEl.className = "choice-list";

  const cards = options.map((opt, i) => {
    const card = document.createElement("button");
    card.className = "choice-card";
    card.innerHTML = `
      <span class="choice-letter">${letters[i]}</span>
      <span class="choice-text">${escapeHtml(opt.text || opt.label || "")}</span>
    `;
    card.addEventListener("click", () => {
      if (answered) return;
      listEl.querySelectorAll(".choice-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      selected = i;
    });
    listEl.appendChild(card);
    return card;
  });

  container.appendChild(listEl);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Verificar";
  container.appendChild(verifyBtn);

  const feedbackEl = document.createElement("div");
  feedbackEl.className = "choice-feedback";
  container.appendChild(feedbackEl);

  const successEl = buildSuccessEl();
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  verifyBtn.addEventListener("click", () => {
    if (selected === null) { showWrong("Selecciona una opción primero."); return; }
    if (answered) return;
    answered = true;

    const opt = options[selected];
    const correct = !!(opt.correct || opt.is_correct);

    cards.forEach((c, i) => {
      if (options[i].correct || options[i].is_correct) c.classList.add("correct");
    });
    if (!correct) cards[selected].classList.add("wrong");

    if (opt.feedback) {
      feedbackEl.textContent = opt.feedback;
      feedbackEl.className   = `choice-feedback visible ${correct ? "correct" : "wrong"}`;
    }

    submitAttempt({
      passed: correct,
      hintUsed: hintUsed.value,
      payload: { selected_index: selected },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (correct) showSuccessEl(successEl, data.xp_awarded);
      else         showWrongEl(wrongEl, "Respuesta incorrecta.");
      verifyBtn.disabled = true;
    });
  });
}

// ---------------------------------------------------------------------------
// predict
// ---------------------------------------------------------------------------
function renderPredict(container, payload) {
  const code           = payload.code || "";
  const expectedOutput = (payload.expected_output || "").trim();

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();

  container.innerHTML = `<div class="widget-title">¿Qué imprime este código?</div>`;

  const codeBlock = document.createElement("pre");
  codeBlock.className = "predict-code";
  codeBlock.textContent = code;
  container.appendChild(codeBlock);

  const label = document.createElement("div");
  label.className = "predict-label";
  label.textContent = "Escribe la salida exacta:";
  container.appendChild(label);

  const textarea = document.createElement("textarea");
  textarea.className = "predict-input";
  textarea.placeholder = "Salida esperada...";
  textarea.rows = 3;
  container.appendChild(textarea);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Verificar";
  container.appendChild(verifyBtn);

  const revealEl = document.createElement("div");
  revealEl.className = "reveal-result";
  revealEl.innerHTML = `<div class="label">Salida correcta:</div><div class="value"></div>`;
  container.appendChild(revealEl);

  const successEl = buildSuccessEl();
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  verifyBtn.addEventListener("click", () => {
    const answer  = textarea.value.trim();
    const correct = answer === expectedOutput;

    revealEl.querySelector(".value").textContent = expectedOutput;
    revealEl.classList.add("visible");

    submitAttempt({
      passed: correct,
      hintUsed: hintUsed.value,
      payload: { answer },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (correct) showSuccessEl(successEl, data.xp_awarded);
      else         showWrongEl(wrongEl, `Salida esperada: "${expectedOutput}"`);
      verifyBtn.disabled = true;
    });
  });
}

// ---------------------------------------------------------------------------
// fill_blank
// ---------------------------------------------------------------------------
function renderFillBlank(container, payload) {
  const codeTemplate = payload.code_template || "";
  const blanks       = payload.blanks || [];

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();
  let blankInputs = [];

  container.innerHTML = `<div class="widget-title">Completa los espacios en blanco</div>`;

  // Build the code block with inline inputs replacing ___
  const codeEl = document.createElement("div");
  codeEl.className = "blank-code";

  let blankCount = 0;
  const parts = codeTemplate.split("___");
  parts.forEach((part, idx) => {
    codeEl.appendChild(document.createTextNode(part));
    if (idx < parts.length - 1) {
      const inp = document.createElement("input");
      inp.type      = "text";
      inp.className = "blank-input";
      inp.dataset.blankIdx = blankCount;
      if (blanks[blankCount]) {
        inp.placeholder = blanks[blankCount].label || `Espacio ${blankCount + 1}`;
        inp.size = Math.max(10, (blanks[blankCount].label || "").length);
      }
      blankInputs.push(inp);
      codeEl.appendChild(inp);
      blankCount++;
    }
  });
  container.appendChild(codeEl);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Verificar";
  container.appendChild(verifyBtn);

  const successEl = buildSuccessEl();
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  verifyBtn.addEventListener("click", () => {
    let allCorrect = true;
    const answers = blankInputs.map((inp, i) => {
      const val    = inp.value.trim();
      const blank  = blanks[i];
      const valid  = blank && blank.correct
        ? blank.correct.map((c) => c.trim()).includes(val)
        : false;
      inp.classList.toggle("correct", valid);
      inp.classList.toggle("wrong",   !valid);
      if (!valid) allCorrect = false;
      return val;
    });

    submitAttempt({
      passed: allCorrect,
      hintUsed: hintUsed.value,
      payload: { answers },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (allCorrect) showSuccessEl(successEl, data.xp_awarded);
      else            showWrongEl(wrongEl, "Algún espacio no es correcto. Los correctos están en verde.");
      verifyBtn.disabled = allCorrect;
    });
  });
}

// ---------------------------------------------------------------------------
// tf (true/false)
// ---------------------------------------------------------------------------
function renderTF(container, payload) {
  const statement    = payload.statement || "";
  const correct      = payload.correct;      // true or false
  const countdown    = payload.countdown_seconds || 0;

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();
  let selected  = null;
  let answered  = false;

  container.innerHTML = `<div class="widget-title">Verdadero o Falso</div>`;

  if (statement) {
    const stEl = document.createElement("p");
    stEl.style.cssText = "font-size:14px;line-height:1.65;margin-bottom:12px;color:var(--fg-soft);";
    stEl.textContent = statement;
    container.appendChild(stEl);
  }

  // Countdown if needed
  let countdownEl = null;
  let countdownTimer = null;
  if (countdown > 0) {
    countdownEl = document.createElement("div");
    countdownEl.className = "tf-countdown";
    countdownEl.textContent = `${countdown}s`;
    container.appendChild(countdownEl);
    let remaining = countdown;
    countdownTimer = setInterval(() => {
      remaining--;
      countdownEl.textContent = `${remaining}s`;
      if (remaining <= 5) countdownEl.classList.add("urgent");
      if (remaining <= 0) {
        clearInterval(countdownTimer);
        if (!answered) autoSubmit();
      }
    }, 1000);
  }

  const tfRow = document.createElement("div");
  tfRow.className = "tf-buttons";

  const trueBtn  = document.createElement("button");
  const falseBtn = document.createElement("button");
  trueBtn.className  = "tf-btn";
  falseBtn.className = "tf-btn";
  trueBtn.textContent  = "Verdadero";
  falseBtn.textContent = "Falso";
  tfRow.appendChild(trueBtn);
  tfRow.appendChild(falseBtn);
  container.appendChild(tfRow);

  function select(val) {
    selected = val;
    trueBtn.classList.toggle("selected",  val === true);
    falseBtn.classList.toggle("selected", val === false);
  }
  trueBtn.addEventListener("click",  () => { if (!answered) { select(true);  verify(); } });
  falseBtn.addEventListener("click", () => { if (!answered) { select(false); verify(); } });

  function autoSubmit() {
    if (!answered) { select(null); verify(true); }
  }

  const successEl = buildSuccessEl();
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  function verify(timeout = false) {
    answered = true;
    if (countdownTimer) clearInterval(countdownTimer);
    const isCorrect = (selected === correct);
    trueBtn.classList.toggle("correct", correct === true);
    trueBtn.classList.toggle("wrong",   selected === true && !isCorrect);
    falseBtn.classList.toggle("correct", correct === false);
    falseBtn.classList.toggle("wrong",   selected === false && !isCorrect);

    submitAttempt({
      passed: isCorrect,
      hintUsed: hintUsed.value,
      payload: { selected, timeout },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (isCorrect) showSuccessEl(successEl, data.xp_awarded);
      else           showWrongEl(wrongEl, "Incorrecto. Revisa el razonamiento.");
    });
  }
}

// ---------------------------------------------------------------------------
// code (Pyodide runner + test suite)
// ---------------------------------------------------------------------------
function renderCode(container, payload) {
  const starter  = payload.starter  || "";
  const tests    = payload.tests    || "";

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();
  let pyodideReady = false;
  let pyodide = null;

  container.innerHTML = `<div class="widget-title">Escribe tu solución</div>`;

  const editorWrap = document.createElement("div");
  editorWrap.className = "code-editor-wrap";
  editorWrap.innerHTML = `
    <textarea class="code-editor" spellcheck="false" autocorrect="off" autocapitalize="off">${escapeHtml(starter)}</textarea>
    <div class="run-bar">
      <button class="btn-run" id="run-btn" disabled>Ejecutar</button>
      <span class="run-status" id="run-status">Cargando Pyodide...</span>
    </div>
  `;
  container.appendChild(editorWrap);

  const ta       = editorWrap.querySelector("textarea");
  const runBtn   = editorWrap.querySelector("#run-btn");
  const runStatus = editorWrap.querySelector("#run-status");

  // Tab support
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const s = ta.selectionStart, en = ta.selectionEnd;
      ta.value = ta.value.substring(0, s) + "    " + ta.value.substring(en);
      ta.selectionStart = ta.selectionEnd = s + 4;
    }
  });

  const outputEl = document.createElement("div");
  outputEl.className = "code-output";
  container.appendChild(outputEl);

  const testResultsEl = document.createElement("div");
  testResultsEl.className = "test-results";
  container.appendChild(testResultsEl);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Verificar";
  verifyBtn.style.marginTop = "8px";
  container.appendChild(verifyBtn);

  const successEl = buildSuccessEl();
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  // Load Pyodide
  (async () => {
    try {
      if (window.loadPyodide) {
        pyodide = await window.loadPyodide();
        pyodideReady = true;
        runBtn.disabled = false;
        runStatus.textContent = "Listo";
      } else {
        runStatus.textContent = "Pyodide no disponible";
      }
    } catch (err) {
      runStatus.textContent = "Error cargando Pyodide";
      console.error(err);
    }
  })();

  async function runCode(code) {
    if (!pyodideReady) return { output: "Pyodide no listo", error: true };
    let output = "";
    pyodide.setStdout({ batched: (s) => { output += s + "\n"; } });
    pyodide.setStderr({ batched: (s) => { output += s + "\n"; } });
    try {
      await pyodide.runPythonAsync(code);
      return { output: output.trim(), error: false };
    } catch (err) {
      return { output: err.message, error: true };
    }
  }

  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    runStatus.textContent = "Ejecutando...";
    outputEl.textContent = "";
    outputEl.classList.remove("visible", "error", "success");
    testResultsEl.innerHTML = "";
    testResultsEl.classList.remove("visible");

    const { output, error } = await runCode(ta.value);
    outputEl.textContent = output || "(sin salida)";
    outputEl.classList.add("visible", error ? "error" : "success");
    runStatus.textContent = error ? "Error" : "OK";
    runBtn.disabled = false;
  });

  verifyBtn.addEventListener("click", async () => {
    if (!pyodideReady) { showWrongEl(wrongEl, "Pyodide no disponible."); return; }
    verifyBtn.disabled = true;
    runBtn.disabled    = true;
    runStatus.textContent = "Verificando...";
    outputEl.classList.remove("visible");
    testResultsEl.innerHTML = "";
    testResultsEl.classList.remove("visible");

    // Run user code + test suite
    const fullCode = ta.value + "\n\n" + tests;
    const testLines = tests.split("\n").filter((l) => l.trim().startsWith("assert"));
    let passed = 0;
    let failed = 0;
    const pillsEl = testResultsEl;

    // Run each assert individually for granular feedback
    // First run the user code to define functions
    const setupResult = await runCode(ta.value);
    if (setupResult.error) {
      outputEl.textContent = setupResult.output;
      outputEl.classList.add("visible", "error");
      runStatus.textContent = "Error de sintaxis";
      showWrongEl(wrongEl, "El código tiene errores. Corrígelos y vuelve a intentar.");
      verifyBtn.disabled = false;
      runBtn.disabled    = false;
      return;
    }

    for (const line of testLines) {
      const res = await runCode(ta.value + "\n" + line);
      const pill = document.createElement("div");
      if (!res.error) {
        pill.className = "test-pill pass";
        pill.textContent = `✓  ${line.trim()}`;
        passed++;
      } else {
        pill.className = "test-pill fail";
        pill.textContent = `✗  ${line.trim()}`;
        failed++;
      }
      pillsEl.appendChild(pill);
    }

    if (testLines.length > 0) {
      pillsEl.classList.add("visible");
    }

    const allPassed = failed === 0 && passed > 0;
    runStatus.textContent = allPassed ? "Todos los tests pasan" : `${failed} test(s) fallando`;

    submitAttempt({
      passed: allPassed,
      hintUsed: hintUsed.value,
      payload: { code: ta.value, passed_tests: passed, failed_tests: failed },
      durationSeconds: elapsed(),
    }).then((data) => {
      if (allPassed) showSuccessEl(successEl, data.xp_awarded);
      else           showWrongEl(wrongEl, `${failed} test(s) no pasan. Revisa tu lógica.`);
      verifyBtn.disabled = allPassed;
      runBtn.disabled    = false;
    });
  });
}

// ---------------------------------------------------------------------------
// decision
// ---------------------------------------------------------------------------
function renderDecision(container, payload) {
  const promptMd = payload.prompt_md || "";
  const options  = payload.options   || [];

  const hintUsed = { value: false };
  wireHint(hintUsed);
  const elapsed = startTimer();
  let chosen = null;
  let answered = false;

  container.innerHTML = `<div class="widget-title">Toma una decisión de arquitectura</div>`;

  if (promptMd) {
    const promptEl = document.createElement("div");
    promptEl.className = "decision-prompt";
    promptEl.textContent = promptMd;
    container.appendChild(promptEl);
  }

  const optsEl = document.createElement("div");
  optsEl.className = "decision-options";

  const cards = options.map((opt, i) => {
    const card = document.createElement("button");
    card.className = "decision-card";
    card.innerHTML = `
      <div class="option-label">${escapeHtml(opt.label || opt.text || `Opción ${i + 1}`)}</div>
      <div class="tradeoff">${escapeHtml(opt.tradeoff_md || opt.tradeoff || "")}</div>
    `;
    card.addEventListener("click", () => {
      if (answered) return;
      cards.forEach((c) => c.classList.remove("chosen"));
      card.classList.add("chosen");
      chosen = i;
    });
    optsEl.appendChild(card);
    return card;
  });
  container.appendChild(optsEl);

  const verifyBtn = document.createElement("button");
  verifyBtn.className = "btn-verify";
  verifyBtn.textContent = "Confirmar decisión";
  container.appendChild(verifyBtn);

  const successEl = buildSuccessEl("Decisión registrada. No hay respuesta incorrecta — cada opción tiene sus tradeoffs.");
  container.appendChild(successEl);
  const wrongEl = buildWrongEl();
  container.appendChild(wrongEl);

  verifyBtn.addEventListener("click", () => {
    if (chosen === null) { showWrongEl(wrongEl, "Selecciona una opción primero."); return; }
    if (answered) return;
    answered = true;

    submitAttempt({
      passed: true,  // decision levels are always "passed" once a choice is made
      hintUsed: hintUsed.value,
      payload: { chosen_index: chosen },
      durationSeconds: elapsed(),
    }).then((data) => {
      showSuccessEl(successEl, data.xp_awarded);
      verifyBtn.disabled = true;
    });
  });
}

// ---------------------------------------------------------------------------
// boss (sequential sub-puzzles)
// ---------------------------------------------------------------------------
function renderBoss(container, payload) {
  const steps = payload.steps || [];
  let currentStep = 0;
  let totalXP = 0;
  const stepsPassed = Array(steps.length).fill(false);

  const elapsed = startTimer();
  const hintUsed = { value: false };
  wireHint(hintUsed);

  container.innerHTML = `
    <div class="widget-title boss-title">Nivel Jefe</div>
    <div class="boss-header">
      <div class="boss-step-label" id="boss-step-label">Paso 1 de ${steps.length}</div>
      <div class="boss-progress-dots" id="boss-dots">
        ${steps.map((_, i) => `<div class="boss-dot${i === 0 ? " active" : ""}" data-step="${i}"></div>`).join("")}
      </div>
    </div>
    <div id="boss-step-container"></div>
  `;

  function updateDots() {
    container.querySelectorAll(".boss-dot").forEach((dot, i) => {
      dot.className = "boss-dot" + (stepsPassed[i] ? " done" : i === currentStep ? " active" : "");
    });
    container.querySelector("#boss-step-label").textContent = `Paso ${currentStep + 1} de ${steps.length}`;
  }

  function renderStep(idx) {
    const step = steps[idx];
    const stepContainer = document.createElement("div");
    stepContainer.className = "boss-step-body";
    stepContainer.style.cssText = "border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;margin-top:12px;";

    if (step.title) {
      const h3 = document.createElement("h3");
      h3.style.cssText = "font-size:14px;font-weight:700;margin:0 0 12px;color:var(--fg);";
      h3.textContent = step.title;
      stepContainer.appendChild(h3);
    }
    if (step.scenario_md) {
      const p = document.createElement("p");
      p.style.cssText = "font-size:13px;color:var(--fg-soft);margin-bottom:14px;";
      p.textContent = step.scenario_md;
      stepContainer.appendChild(p);
    }

    // Delegate to sub-renderer
    const subKind = step.kind || "multi_choice";
    // Sub-step needs its own verify logic that advances to next boss step
    const innerContainer = document.createElement("div");
    innerContainer.className = "puzzle-widget";
    innerContainer.style.border = "none";
    innerContainer.style.padding = "0";

    // Build a minimal sub-payload
    const subPayload = { ...step };

    // Temporarily override NEXT_LEVEL_URL for sub-steps
    const origNextUrl = window.__BL_NEXT_LEVEL_URL;

    switch (subKind) {
      case "order_steps":
        renderOrderSteps(innerContainer, subPayload);
        break;
      case "multi_choice":
        renderMultiChoice(innerContainer, subPayload);
        break;
      case "predict":
        renderPredict(innerContainer, subPayload);
        break;
      case "fill_blank":
        renderFillBlank(innerContainer, subPayload);
        break;
      case "tf":
        renderTF(innerContainer, subPayload);
        break;
      case "code":
        renderCode(innerContainer, subPayload);
        break;
    }

    stepContainer.appendChild(innerContainer);

    // Intercept the success overlay in the sub-step to advance boss
    const observer = new MutationObserver(() => {
      const successEl = innerContainer.querySelector(".success-overlay.visible");
      if (successEl) {
        observer.disconnect();
        stepsPassed[idx] = true;

        // Extract XP from the displayed text if available
        const xpEl = successEl.querySelector(".success-xp");
        const xpVal = xpEl ? parseInt(xpEl.textContent.replace(/[^0-9]/g, ""), 10) || 0 : 0;
        totalXP += xpVal;

        // Hide old sub-step "next level" link
        const nextBtn = successEl.querySelector(".btn-next-level");
        if (nextBtn) nextBtn.style.display = "none";

        updateDots();

        if (idx < steps.length - 1) {
          currentStep++;
          const advBtn = document.createElement("button");
          advBtn.className = "btn-verify";
          advBtn.style.cssText = "margin-top:12px;background:linear-gradient(135deg,var(--g-green),var(--g-green-2));";
          advBtn.textContent = `Continuar — Paso ${currentStep + 1}`;
          innerContainer.appendChild(advBtn);
          advBtn.addEventListener("click", () => {
            const sc = document.getElementById("boss-step-container");
            sc.innerHTML = "";
            renderStep(currentStep);
            updateDots();
          });
        } else {
          // All boss steps done — show final success
          submitAttempt({
            passed: true,
            hintUsed: hintUsed.value,
            payload: { steps_passed: stepsPassed },
            durationSeconds: elapsed(),
          }).then((data) => {
            const finalEl = document.createElement("div");
            finalEl.className = "success-overlay visible";
            finalEl.style.marginTop = "16px";
            finalEl.innerHTML = `
              <div class="success-xp">+${data.xp_awarded} XP</div>
              <div class="success-msg">Nivel Jefe completado. Bien hecho.</div>
              <a class="btn-next-level" href="${NEXT_LEVEL_URL}">Siguiente nivel &rarr;</a>
            `;
            const sc = document.getElementById("boss-step-container");
            sc.appendChild(finalEl);
          });
        }
      }
    });
    observer.observe(innerContainer, { attributes: true, subtree: true, attributeFilter: ["class"] });

    document.getElementById("boss-step-container").appendChild(stepContainer);
  }

  renderStep(0);
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
function buildSuccessEl(msg) {
  const el = document.createElement("div");
  el.className = "success-overlay";
  el.innerHTML = `
    <div class="success-xp"></div>
    <div class="success-msg">${escapeHtml(msg || "Correcto.")}</div>
    <a class="btn-next-level" href="${NEXT_LEVEL_URL}">Siguiente nivel &rarr;</a>
  `;
  return el;
}

function buildWrongEl() {
  const el = document.createElement("div");
  el.className = "wrong-feedback";
  return el;
}

function showSuccessEl(el, xp) {
  el.querySelector(".success-xp").textContent = `+${xp} XP`;
  el.classList.add("visible");
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showWrongEl(el, msg) {
  el.textContent = msg || "Respuesta incorrecta.";
  el.classList.add("visible");
  setTimeout(() => el.classList.remove("visible"), 4500);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function arraysEqual(a, b) {
  if (a.length !== b.length) return false;
  return a.every((v, i) => v === b[i]);
}

// ---------------------------------------------------------------------------
// Mentor chat
// ---------------------------------------------------------------------------
function wireMentor() {
  const form   = document.getElementById("mentor-form");
  const input  = document.getElementById("mentor-input");
  const msgs   = document.getElementById("mentor-messages");
  if (!form || !input || !msgs) return;

  const levelSlug = LEVEL_SLUG;

  function appendMsg(text, role) {
    const el = document.createElement("div");
    el.className = `mentor-msg ${role}`;
    el.textContent = text;
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
    return el;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question) return;
    input.value = "";
    input.disabled = true;
    form.querySelector(".btn-mentor-send").disabled = true;

    appendMsg(question, "user");
    const thinking = appendMsg("...", "thinking");

    try {
      const response = await fetch("/api/game/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          context: `Nivel: ${document.title}`,
          level_slug: levelSlug,
        }),
      });

      thinking.remove();

      if (response.body) {
        // SSE / streaming
        const reader  = response.body.getReader();
        const decoder = new TextDecoder();
        const botMsg  = appendMsg("", "assistant");
        let buffer    = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();
          // Parse event: delta / done pairs
          let currentEvent = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const raw = line.slice(6).trim();
              if (raw === "[DONE]") break;
              try {
                const obj = JSON.parse(raw);
                if (currentEvent === "delta" && obj.text) {
                  botMsg.textContent += obj.text;
                }
                if (currentEvent === "done") break;
              } catch (_) {
                if (raw) botMsg.textContent += raw;
              }
            }
          }
          msgs.scrollTop = msgs.scrollHeight;
        }
      } else {
        const data = await response.json().catch(() => ({}));
        appendMsg(data.text || data.message || "Sin respuesta del mentor.", "assistant");
      }
    } catch (err) {
      thinking.remove();
      appendMsg("El mentor no está disponible en este momento.", "assistant");
    } finally {
      input.disabled = false;
      form.querySelector(".btn-mentor-send").disabled = false;
      input.focus();
    }
  });

  // Ctrl/Cmd+Enter to submit
  input.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
  });
}

// ---------------------------------------------------------------------------
// Journal tabs
// ---------------------------------------------------------------------------
function wireJournalTabs() {
  const tabs   = document.querySelectorAll(".game-tab");
  const panels = document.querySelectorAll(".tab-panel");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.panel);
      if (target) target.classList.add("active");
    });
  });
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Level player
  const widget = document.getElementById("level-widget");
  if (widget && LEVEL_KIND) {
    const conceptsRaw = window.__BL_CONCEPTS_TO_SHOW || [];

    function mountWidget() {
      switch (LEVEL_KIND) {
        case "order_steps":  renderOrderSteps(widget, LEVEL_PAYLOAD);  break;
        case "multi_choice": renderMultiChoice(widget, LEVEL_PAYLOAD); break;
        case "predict":      renderPredict(widget, LEVEL_PAYLOAD);     break;
        case "fill_blank":   renderFillBlank(widget, LEVEL_PAYLOAD);   break;
        case "tf":           renderTF(widget, LEVEL_PAYLOAD);          break;
        case "code":         renderCode(widget, LEVEL_PAYLOAD);        break;
        case "boss":         renderBoss(widget, LEVEL_PAYLOAD);        break;
        case "decision":     renderDecision(widget, LEVEL_PAYLOAD);    break;
        default:
          widget.innerHTML = `<p style="color:var(--muted)">Tipo de puzzle desconocido: <code>${LEVEL_KIND}</code></p>`;
      }
    }

    runConceptPopups(conceptsRaw, mountWidget);
  }

  wireMentor();
  wireJournalTabs();
});
