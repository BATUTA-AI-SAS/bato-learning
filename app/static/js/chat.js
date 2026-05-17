/* chat.js — SSE tutor chat per module. */

function renderMd(text) {
  // tiny escape; the server is the source of safe markdown rendering for stored content
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");
}

function appendMessage(log, role, text) {
  const el = document.createElement("div");
  el.className = "chat-msg " + role;
  el.innerHTML = `<span class="role">${role === "user" ? "tú" : "tutor"}</span><span class="content"></span>`;
  el.querySelector(".content").innerHTML = renderMd(text);
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el.querySelector(".content");
}

async function loadHistory(moduleId, log) {
  try {
    const r = await fetch(`/api/chat/${moduleId}/history`);
    if (!r.ok) return;
    const data = await r.json();
    for (const m of data.messages) appendMessage(log, m.role, m.content);
  } catch (_) { /* ignore */ }
}

function currentEditorCode() {
  // try the last focused exercise editor; fall back to first
  const editors = Array.from(document.querySelectorAll(".code-editor"));
  if (editors.length === 0) return null;
  const focused = document.activeElement;
  if (focused && focused.classList && focused.classList.contains("code-editor")) {
    return focused.value;
  }
  return editors[0].value;
}

async function sendMessage(moduleId, text, log, costEl) {
  const userEl = appendMessage(log, "user", text);
  const assistEl = appendMessage(log, "assistant", "");
  let acc = "";

  const editor_code = currentEditorCode();

  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ module_id: moduleId, message: text, editor_code }),
  });
  if (!resp.ok) {
    assistEl.innerHTML = `<em>error ${resp.status}</em>`;
    return;
  }
  const reader = resp.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const evMatch = block.match(/^event:\s*(.+)$/m);
      const dataMatch = block.match(/^data:\s*(.+)$/m);
      if (!evMatch || !dataMatch) continue;
      const ev = evMatch[1].trim();
      let payload = {};
      try { payload = JSON.parse(dataMatch[1]); } catch (_) {}
      if (ev === "delta" && payload.text) {
        acc += payload.text;
        assistEl.innerHTML = renderMd(acc);
        log.scrollTop = log.scrollHeight;
      } else if (ev === "done") {
        if (costEl && typeof payload.cost_usd === "number") {
          costEl.textContent = `$${payload.cost_usd.toFixed(6)}`;
        }
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const dock = document.getElementById("chat-dock");
  if (!dock) return;
  const moduleId = parseInt(dock.dataset.moduleId);
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const costEl = document.getElementById("chat-cost");

  loadHistory(moduleId, log);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await sendMessage(moduleId, text, log, costEl);
  });

  document.querySelectorAll(".chat-suggested button").forEach((b) => {
    b.addEventListener("click", () => {
      input.value = b.dataset.prompt;
      input.focus();
    });
  });
});
