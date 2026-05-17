# Track S — Seguridad aplicada a agentes IA

Cuatro módulos. Audiencia: lector que terminó hasta Track E y construye agentes en producción. Sabe FastAPI, Postgres, SDK Anthropic, LangGraph. **No sabe que su agente es atacable ni cómo.**

## Módulos

| ext_id | slug | título | ord | min | estado |
|--------|------|--------|-----|-----|--------|
| S01 | `owasp-api-top10-fastapi` | OWASP API Security Top 10 aplicado a FastAPI | 220 | 75 | done |
| S02 | `prompt-injection-jailbreak` | Prompt injection, jailbreak, e indirect prompt injection | 221 | 60 | done |
| S03 | `tool-security-sandboxing` | Tool security: allowlist, sandbox, dry-run, human-in-the-loop | 222 | 60 | done |
| S04 | `threat-modeling-agentic-saas` | Threat modeling para SaaS agéntico multitenant | 223 | 75 | done |

## Posición en el roadmap

```
B (Web full-stack)
  └─ B10 (auth + JWT)
       ↓
C (Datos)
  └─ C03 (RLS multitenant)
       ↓
S (Seguridad) ← este track
  ├─ S01 OWASP API Top 10
  ├─ S02 Prompt injection / IPI
  ├─ S03 Tool security
  └─ S04 Threat modeling
       ↓
D (Operación)
  └─ D01 Docker (ya con superficie asegurada)
```

## Dependencias entre módulos del track

- S01 no depende de S02/S03/S04 — entrada al track, solo necesita B10 y C03.
- S02 necesita E01 (loop de agente) y E03 (skills) para que el contexto de IPI tenga sentido.
- S03 necesita E02 (LangGraph, interrupt_before) y S02 (concepto de tool comprometida).
- S04 sintetiza S01+S02+S03 y se conecta hacia E05 (Temporal con workflow ya modelado).

## Conceptos nuevos introducidos

Añadidos al glosario de `_team/SHARED.md` al completar este track:

| Término | Definición | Módulo |
|---------|-----------|--------|
| `BOLA` | Broken Object Level Authorization — acceso a objetos de otro tenant por ID directo | S01 |
| `prompt injection` | Instrucciones en el input del usuario que intentan anular el system prompt | S02 |
| `indirect prompt injection (IPI)` | Instrucciones maliciosas en datos externos que el agente procesa | S02 |
| `spotlighting` | Técnica de envolver datos externos con tags que los marcan como no confiables | S02 |
| `jailbreak` | Técnica de romper las restricciones del modelo atacando su identidad o rol | S02 |
| `dry-run` | Modo de simulación de una tool destructiva sin ejecutar el side-effect | S03 |
| `HITL` | Human-in-the-loop — pausa del agente hasta recibir confirmación humana | S03 |
| `STRIDE` | Marco de threat modeling: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege | S04 |
| `Confused Deputy` | Forma de Elevation of Privilege donde el agente actúa con más privilegios que el principal que lo invocó | S04 |

## Relación con tracks existentes

| Track | Módulo | Conexión con Track S |
|-------|--------|---------------------|
| B | B10 auth | S01 extiende la dependency de auth con scope check y rate limit |
| C | C03 RLS | S01 usa RLS como segunda línea de defensa contra BOLA; S04 lo cita como control de I1 |
| E | E01 SDK | S02 usa el array de mensajes del SDK para spotlighting |
| E | E02 LangGraph | S03 usa `interrupt_before` para HITL |
| E | E05 Temporal | S04 construye el threat model que E05 asume resuelto |
| D | D04 Phoenix | S04 identifica Phoenix como superficie de IPI y propone PII scrubbing |
