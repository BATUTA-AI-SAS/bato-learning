"""Build the system string + messages payload for the tutor chat.

Layout:
  system  = tutor identity/rules + module body (single string for OpenAI-compatible API)
  messages = dynamic: recent attempts summary + chat history + new user turn
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ChatMessage, Module
from ..repos import progress as progress_repo
from ..settings import settings

TUTOR_RULES = """\
Eres el mentor del juego learning.batutaai.com. El jugador está atrapado en un
nivel y te pidió ayuda. Tu rol es enseñar, NUNCA resolver.

Reglas duras:
- NO escribas la solución. NUNCA. Si la respuesta correcta es código, no lo
  escribas, ni completo ni parcial, ni en bloque, ni en línea.
- Una pregunta socrática por turno. Una sola.
- La pregunta debe partir de lo que el jugador escribió (su intento), no de la
  consigna ideal. Si no hay intento, pregunta primero "¿qué crees que hace
  falta antes que nada?".
- Si necesitas referenciar un concepto: nombra la página del diario donde vive
  ("revisa la página *El umbral* sobre condiciones"), no expliques el concepto
  en chat.
- Si el jugador pega código y pregunta "¿está bien?", responde con UNA pregunta
  diagnóstica ("¿qué pasa si `amount` es exactamente 1000?"), no con corrección.
- Si el jugador pide la respuesta directamente, responde: "te quemarías el
  músculo que vinimos a entrenar; dime qué intentaste hasta ahora".
- Máximo 3 oraciones por respuesta.
- Habla en español.

Estás prohibido de:
- Pegar bloques ``` con la solución.
- Escribir `def`, `for`, `if` seguido de su cuerpo completo.
- Dar más de una pista útil por turno.
"""


def _system_string(module: Module) -> str:
    module_section = (
        f"=== Módulo actual: {module.ext_id} — {module.title} ===\n\n"
        f"{module.body_md}"
    )
    return TUTOR_RULES + "\n\n" + module_section


async def build_payload(
    session: AsyncSession,
    *,
    module: Module,
    user_id: int,
    history: list[ChatMessage],
    new_user_text: str,
    editor_code: str | None = None,
) -> tuple[str, list[dict]]:
    attempts = await progress_repo.recent_attempts_for_module(
        session, user_id=user_id, module_id=module.id, limit=5
    )

    dyn_summary: list[str] = []
    if attempts:
        dyn_summary.append("Intentos recientes del lector en este módulo:")
        for a in attempts:
            verdict = "OK" if a.passed else "fallo"
            err = a.error[:200] if a.error else ""
            dyn_summary.append(
                f"- ejercicio={a.exercise_id} {verdict} runner={a.runner} {err}"
            )

    if editor_code:
        dyn_summary.append("\nCódigo actual en su editor:")
        dyn_summary.append(f"```python\n{editor_code[:4000]}\n```")

    history_msgs: list[dict] = []
    for h in history[-settings.chat_max_history_messages :]:
        if h.role in ("user", "assistant"):
            history_msgs.append({"role": h.role, "content": h.content_md})

    composed_user = new_user_text
    if dyn_summary:
        composed_user = (
            "Contexto dinámico:\n"
            + "\n".join(dyn_summary)
            + "\n\nPregunta del lector:\n"
            + new_user_text
        )

    messages = history_msgs + [{"role": "user", "content": composed_user}]
    return _system_string(module), messages
