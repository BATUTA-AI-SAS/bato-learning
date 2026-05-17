/* app.js — base wiring + gamification UX.
 *
 * Responsibilities:
 *   - Tab in textarea editors, auto-resize.
 *   - Quiz click-to-answer, surface XP awarded by the server.
 *   - Chat toggle.
 *   - XP toast stack (when the server reports `xp_awarded > 0` or new unlocks).
 *   - "Modo Excel" toggle persisted in localStorage; only flips a `data-excel`
 *     attribute on <html> so the CSS can show/hide `.excel-bridge` blocks.
 *
 * Graceful degradation:
 *   - All toast/animation behaviour is best-effort. If JS fails or is
 *     disabled, the app still renders progress data server-side (header,
 *     bars, achievements grid). Nothing here is required for correctness.
 */

const ACHIEVEMENTS_BY_CODE = (() => {
  const m = {};
  for (const a of (window.__BL_ACHIEVEMENTS || [])) m[a.code] = a;
  return m;
})();

// === EDITOR ================================================================
function wireEditors() {
  document.querySelectorAll("textarea.code-editor").forEach((ta) => {
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const s = ta.selectionStart, en = ta.selectionEnd;
        ta.value = ta.value.substring(0, s) + "    " + ta.value.substring(en);
        ta.selectionStart = ta.selectionEnd = s + 4;
      }
    });
    autoResize(ta);
    ta.addEventListener("input", () => autoResize(ta));
  });
}
function autoResize(ta) {
  ta.style.height = "auto";
  ta.style.height = (ta.scrollHeight + 4) + "px";
}

// === XP TOAST + HEADER BAR =================================================
function toast(message, opts = {}) {
  const stack = document.getElementById("xp-toast-stack");
  if (!stack) return;
  const el = document.createElement("div");
  el.className = "xp-toast" + (opts.unlock ? " unlock" : "");
  el.innerHTML = `
    <span class="value">${opts.value || ""}</span>
    <span class="label">${message}</span>
  `;
  stack.appendChild(el);
  // remove after the animation finishes
  setTimeout(() => el.remove(), 4200);
}

function bumpXpBar() {
  const bar = document.getElementById("xp-bar");
  if (!bar) return;
  bar.classList.remove("gain");
  // force reflow so the animation can be re-triggered
  void bar.offsetWidth;
  bar.classList.add("gain");
}

function announceXp(points, label) {
  if (!points) return;
  toast(label || "XP ganado", { value: `+${points} XP` });
  bumpXpBar();
}

function announceUnlocks(codes) {
  for (const code of codes || []) {
    const a = ACHIEVEMENTS_BY_CODE[code];
    if (!a) continue;
    toast(`Logro: ${a.title}`, { unlock: true, value: a.icon || "★" });
  }
}

// === QUIZZES ===============================================================
function wireQuizzes() {
  document.querySelectorAll(".quiz").forEach((quiz) => {
    const kind = quiz.dataset.kind || "radio";
    if (kind === "match")   { wireMatchQuiz(quiz);   return; }
    if (kind === "predict") { wirePredictQuiz(quiz); return; }
    if (kind === "tf")      { wireTfQuiz(quiz);      return; }

    // Default: radio
    const quizId = parseInt(quiz.dataset.quizId);
    const opts = quiz.querySelectorAll("button.opt");
    const fb = quiz.querySelector(".feedback");
    const ex = quiz.querySelector(".explanation");

    opts.forEach((btn) => {
      btn.addEventListener("click", async () => {
        const optionId = parseInt(btn.dataset.optionId);
        opts.forEach((b) => (b.disabled = true));
        let data;
        try {
          const r = await fetch(`/api/quizzes/${quizId}/answer`, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ option_id: optionId }),
          });
          data = await r.json();
        } catch (e) {
          opts.forEach((b) => (b.disabled = false));
          return;
        }
        btn.classList.add(data.correct ? "correct" : "wrong");
        if (!data.correct && data.correct_option_id) {
          opts.forEach((b) => {
            if (parseInt(b.dataset.optionId) === data.correct_option_id) {
              b.classList.add("correct");
            }
          });
        }
        if (data.selected_feedback_md) {
          fb.hidden = false;
          fb.innerHTML = data.selected_feedback_md;
        }
        if (ex) ex.hidden = false;
        if (data.xp_awarded) announceXp(data.xp_awarded, "Quiz acertado");
        announceUnlocks(data.newly_unlocked);
      });
    });
  });
}

// === MATCH QUIZ ============================================================
function wireMatchQuiz(quiz) {
  const quizId = parseInt(quiz.dataset.quizId);
  const pairs = quiz.querySelectorAll(".pair");
  const submitBtn = quiz.querySelector(".submit-match");
  const fb = quiz.querySelector(".feedback");
  const ex = quiz.querySelector(".explanation");
  const selections = {};

  pairs.forEach((pair) => {
    const pairIdx = parseInt(pair.dataset.index);
    pair.querySelectorAll(".right-opt").forEach((btn) => {
      btn.addEventListener("click", () => {
        pair.querySelectorAll(".right-opt").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        selections[pairIdx] = parseInt(btn.dataset.pairIdx);
        if (submitBtn) submitBtn.disabled = Object.keys(selections).length < pairs.length;
      });
    });
  });

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.addEventListener("click", async () => {
      const pairsPayload = Object.entries(selections).map(([li, ri]) => ({
        left_idx: parseInt(li), right_idx: parseInt(ri),
      }));
      submitBtn.disabled = true;
      let data;
      try {
        const r = await fetch(`/api/quizzes/${quizId}/answer`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ match_pairs: pairsPayload }),
        });
        data = await r.json();
      } catch (e) { submitBtn.disabled = false; return; }

      const allCorrect = data.correct === true;
      pairs.forEach((pair) => {
        const sel = pair.querySelector(".right-opt.selected");
        if (sel) sel.classList.add(allCorrect ? "correct" : "wrong");
        pair.querySelectorAll(".right-opt:not(.selected)").forEach((b) => (b.disabled = true));
      });
      if (fb) {
        fb.hidden = false;
        fb.innerHTML = allCorrect
          ? "Todos los pares correctos."
          : (data.selected_feedback_md || "Algunos pares incorrectos. Revisa la explicación.");
      }
      if (ex) ex.hidden = false;
      if (data.xp_awarded) announceXp(data.xp_awarded, "Quiz acertado");
      announceUnlocks(data.newly_unlocked);
    });
  }
}

// === PREDICT QUIZ ==========================================================
function wirePredictQuiz(quiz) {
  const quizId = parseInt(quiz.dataset.quizId);
  const input = quiz.querySelector(".predict-input");
  const revealBtn = quiz.querySelector(".reveal-btn");
  const fb = quiz.querySelector(".feedback");
  const ex = quiz.querySelector(".explanation");

  if (!revealBtn) return;
  revealBtn.addEventListener("click", async () => {
    const answer = input ? input.value.trim() : "";
    revealBtn.disabled = true;
    if (input) input.disabled = true;
    let data = { xp_awarded: 0, newly_unlocked: [] };
    try {
      const r = await fetch(`/api/quizzes/${quizId}/answer`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ predict_answer: answer }),
      });
      data = await r.json();
    } catch (_) {}
    if (ex) ex.hidden = false;
    if (fb && data.selected_feedback_md) { fb.hidden = false; fb.innerHTML = data.selected_feedback_md; }
    if (data.xp_awarded) announceXp(data.xp_awarded, "Respuesta registrada");
    announceUnlocks(data.newly_unlocked);
  });
}

// === TF QUIZ ===============================================================
function wireTfQuiz(quiz) {
  const quizId = parseInt(quiz.dataset.quizId);
  const bonusMs = parseInt(quiz.dataset.bonusMs || "5000");
  const opts = quiz.querySelectorAll("button.tf-opt");
  const fb = quiz.querySelector(".feedback");
  const ex = quiz.querySelector(".explanation");
  const countdownEl = quiz.querySelector(".countdown-value");

  const startTime = Date.now();
  let countdownTimer = null;

  if (countdownEl) {
    let remaining = Math.ceil(bonusMs / 1000);
    countdownEl.textContent = remaining;
    countdownTimer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(countdownTimer);
        countdownEl.textContent = "0";
        countdownEl.classList.add("urgent");
      } else {
        countdownEl.textContent = remaining;
        if (remaining <= 2) countdownEl.classList.add("urgent");
      }
    }, 1000);
  }

  opts.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const elapsed = Date.now() - startTime;
      const withinBonus = elapsed <= bonusMs;
      if (countdownTimer) clearInterval(countdownTimer);
      if (countdownEl) countdownEl.textContent = withinBonus ? "BONUS" : "—";

      const optionId = parseInt(btn.dataset.optionId);
      opts.forEach((b) => (b.disabled = true));
      let data;
      try {
        const r = await fetch(`/api/quizzes/${quizId}/answer`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ option_id: optionId, within_bonus: withinBonus }),
        });
        data = await r.json();
      } catch (e) { opts.forEach((b) => (b.disabled = false)); return; }

      btn.classList.add(data.correct ? "correct" : "wrong");
      if (!data.correct && data.correct_option_id) {
        opts.forEach((b) => {
          if (parseInt(b.dataset.optionId) === data.correct_option_id) b.classList.add("correct");
        });
      }
      if (data.selected_feedback_md) { fb.hidden = false; fb.innerHTML = data.selected_feedback_md; }
      if (ex) ex.hidden = false;
      const xpLabel = withinBonus && data.correct ? "Quiz acertado + bonus" : "Quiz acertado";
      if (data.xp_awarded) announceXp(data.xp_awarded, xpLabel);
      announceUnlocks(data.newly_unlocked);
    });
  });
}

// === CHAT DOCK =============================================================
function wireChatToggle() {
  const layout = document.getElementById("layout");
  const dock = document.getElementById("chat-dock");
  const btn = document.getElementById("chat-toggle");
  if (dock && layout) layout.classList.add("with-chat");
  if (btn && layout) {
    btn.addEventListener("click", () => layout.classList.toggle("chat-collapsed"));
  }
}

// === EXCEL MODE ============================================================
function wireExcelToggle() {
  const btn = document.getElementById("excel-toggle");
  if (!btn) return;
  const sync = () => {
    const on = document.documentElement.getAttribute("data-excel") === "on";
    btn.classList.toggle("on", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  };
  sync();
  btn.addEventListener("click", () => {
    const on = document.documentElement.getAttribute("data-excel") === "on";
    if (on) {
      document.documentElement.removeAttribute("data-excel");
      try { localStorage.setItem("blearn.excel", "off"); } catch (_) {}
    } else {
      document.documentElement.setAttribute("data-excel", "on");
      try { localStorage.setItem("blearn.excel", "on"); } catch (_) {}
    }
    sync();
  });
}

// === PAGE-LOAD XP FEEDBACK =================================================
function announceFirstVisitXp() {
  const pts = window.__BL_XP_ON_LOAD || 0;
  const unlocks = window.__BL_NEWLY_UNLOCKED || [];
  if (pts > 0) announceXp(pts, "Módulo abierto");
  if (unlocks.length) announceUnlocks(unlocks);
}

// === INLINE EXERCISE HOIST =================================================
function hoistInlineExercises() {
  // Delegate to the per-page hoist function injected by module.html, if present.
  if (typeof window.__BL_hoist === "function") {
    window.__BL_hoist();
  }
}

// === G10: Floating "+X XP" near an element =================================
function spawnXpFloat(anchorEl, points) {
  if (!anchorEl || !points) return;
  const rect = anchorEl.getBoundingClientRect();
  const span = document.createElement("span");
  span.className = "xp-float";
  span.textContent = `+${points} XP`;
  // position relative to viewport using fixed positioning
  span.style.cssText = `
    left: ${rect.left + rect.width / 2}px;
    top: ${rect.top + window.scrollY - 4}px;
    position: absolute;
  `;
  document.body.appendChild(span);
  // remove after animation finishes (1.2s)
  setTimeout(() => span.remove(), 1300);
}

// === G11: Module-complete confetti overlay ==================================
let _moduleXpAccumulated = 0;

function showModuleCompleteOverlay() {
  const overlay = document.getElementById("module-complete-overlay");
  if (!overlay) return;

  // Build confetti particles
  const colors = ["#4f6df3", "#f5a524", "#34d399", "#a78bfa", "#2dd4bf", "#ef6c4a", "#ffc868", "#93b1ff"];
  const particles = [];
  const count = 16;
  for (let i = 0; i < count; i++) {
    const p = document.createElement("div");
    p.className = "confetti-particle";
    const startX = 20 + Math.random() * 60; // vw %
    const startY = 10 + Math.random() * 80; // vh %
    const endX = startX + (Math.random() - 0.5) * 40;
    const endY = startY - 20 - Math.random() * 40;
    const rot = Math.random() * 720 - 360;
    const delay = Math.random() * 0.5;
    const color = colors[i % colors.length];
    p.style.cssText = `
      left: ${startX}vw;
      top: ${startY}vh;
      background: ${color};
      border-radius: ${Math.random() > 0.5 ? "50%" : "2px"};
      animation: confettiParticle_${i} 1.8s ${delay}s ease-out forwards;
    `;
    // inject unique keyframe for each particle
    const style = document.createElement("style");
    style.textContent = `
      @keyframes confettiParticle_${i} {
        0%   { opacity: 1; transform: translate3d(0,0,0) rotate(0deg) scale(1); }
        80%  { opacity: .8; transform: translate3d(${(endX - startX) * 1}vw,${(endY - startY) * 1}vh,0) rotate(${rot}deg) scale(.9); }
        100% { opacity: 0; transform: translate3d(${(endX - startX) * 1.1}vw,${(endY - startY) * 1.1}vh,0) rotate(${rot * 1.2}deg) scale(.7); }
      }
    `;
    document.head.appendChild(style);
    document.body.appendChild(p);
    particles.push({ el: p, style });
  }

  // Build center card
  const xpText = _moduleXpAccumulated > 0 ? ` · +${_moduleXpAccumulated} XP` : "";
  const nextCard = document.querySelector(".next-module-card");
  const nextHref = nextCard ? nextCard.getAttribute("href") : null;
  const nextTitle = nextCard ? (nextCard.querySelector("h2")?.textContent || "siguiente módulo") : null;

  overlay.innerHTML = `
    <div class="mod-complete-card">
      <h2>Módulo listo${xpText}</h2>
      ${nextHref ? `<a class="cta-next" href="${nextHref}">continuar: ${nextTitle} →</a>` : ""}
      <p class="dismiss-hint">Haz clic en cualquier parte o presiona Esc para cerrar</p>
    </div>
  `;
  overlay.removeAttribute("hidden");

  // highlight next-module-card
  if (nextCard) {
    nextCard.classList.add("highlight");
    nextCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // dismiss helpers
  const dismiss = () => {
    overlay.classList.add("fade-out");
    setTimeout(() => {
      overlay.setAttribute("hidden", "");
      overlay.classList.remove("fade-out");
      overlay.innerHTML = "";
      particles.forEach(({ el, style }) => { el.remove(); style.remove(); });
    }, 400);
  };

  overlay.addEventListener("click", dismiss, { once: true });
  document.addEventListener("keydown", function onEsc(e) {
    if (e.key === "Escape") { dismiss(); document.removeEventListener("keydown", onEsc); }
  });
  // auto-fade after 2s
  setTimeout(dismiss, 2000);
}

// === CHECKPOINT XP =========================================================
function wireCheckpoints() {
  const checkpoints = document.querySelectorAll(".checkpoint[data-checkpoint-id]");
  if (!checkpoints.length) return;

  const moduleId = document.querySelector("[data-module-id]")?.dataset?.moduleId;
  if (!moduleId) return;

  // G9: progress bar setup
  const progressBar = document.getElementById("mod-progress-bar");
  const progressLabel = document.getElementById("mod-progress-label");
  const totalCheckpoints = checkpoints.length;
  let reachedCount = 0;

  function updateProgressBar() {
    if (!progressBar) return;
    const pct = totalCheckpoints > 0 ? Math.round((reachedCount / totalCheckpoints) * 100) : 0;
    progressBar.style.width = pct + "%";
    if (progressLabel) {
      progressLabel.textContent = `${reachedCount}/${totalCheckpoints} secciones leídas`;
    }
  }
  updateProgressBar();

  const reported = new Set();

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const cpId = el.dataset.checkpointId;
        if (reported.has(cpId)) return;

        // Must be visible for > 5 s before rewarding
        const timer = setTimeout(async () => {
          if (!document.contains(el)) return;
          reported.add(cpId);
          observer.unobserve(el);

          // G9: increment bar immediately on intersection confirmation
          reachedCount++;
          updateProgressBar();

          // G11: check for module complete
          if (reachedCount === totalCheckpoints) {
            document.dispatchEvent(new CustomEvent("module-complete", { bubbles: true }));
          }

          try {
            const r = await fetch(`/api/checkpoints/${moduleId}/${cpId}`, {
              method: "POST",
              headers: { "content-type": "application/json" },
            });
            if (!r.ok) return;
            const data = await r.json();
            if (data.xp_awarded) {
              announceXp(data.xp_awarded, "Sección leída");
              _moduleXpAccumulated += data.xp_awarded;
              // G10: spawn floating XP near the heading
              spawnXpFloat(el, data.xp_awarded);
            }
            announceUnlocks(data.newly_unlocked);
          } catch (_) {}
        }, 5000);

        // Cancel if the element leaves the viewport before 5 s
        el._cpTimer = timer;
      });

      // Cancel pending timers for elements that left viewport
      entries.forEach((entry) => {
        if (entry.isIntersecting) return;
        const el = entry.target;
        if (el._cpTimer) {
          clearTimeout(el._cpTimer);
          el._cpTimer = null;
        }
      });
    },
    { threshold: 0.6 }
  );

  checkpoints.forEach((el) => observer.observe(el));
}

// === G11: listen for module-complete =======================================
document.addEventListener("module-complete", () => {
  showModuleCompleteOverlay();
});

// === NEAR-UNLOCK CHIP (G13) ================================================
function wireNearUnlockChip() {
  const nearUnlocks = window.__BL_NEAR_UNLOCKS || [];
  if (!nearUnlocks.length) return;

  const chip = document.getElementById("near-unlock-chip");
  if (!chip) return;
  const link = chip.querySelector("a");
  if (!link) return;

  let idx = 0;

  function showEntry(entry) {
    link.textContent = entry.missing_label;
    chip.removeAttribute("hidden");
    chip.classList.remove("chip-out");
    chip.classList.add("chip-in");
  }

  function rotateChip() {
    if (nearUnlocks.length <= 1) return;
    chip.classList.remove("chip-in");
    chip.classList.add("chip-out");
    setTimeout(() => {
      idx = (idx + 1) % nearUnlocks.length;
      showEntry(nearUnlocks[idx]);
    }, 500);
  }

  showEntry(nearUnlocks[0]);
  if (nearUnlocks.length > 1) {
    setInterval(rotateChip, 8000);
  }
}

// === BOOT ==================================================================
document.addEventListener("DOMContentLoaded", () => {
  hoistInlineExercises();
  wireEditors();
  wireQuizzes();
  wireChatToggle();
  wireExcelToggle();
  announceFirstVisitXp();
  wireCheckpoints();
  wireNearUnlockChip();
});

// Exposed for pyodide_runner.js to call after a passed attempt.
window.__BL = {
  announceXp,
  announceUnlocks,
  bumpXpBar,
};
