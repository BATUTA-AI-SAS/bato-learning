---
ext_id: F-CX-02
slug: resumen-llamadas-cx
track: F
dept: CX
ord: 241
title: "Resumen y next-actions de llamadas de soporte"
summary: "Pipeline que transcribe llamadas, extrae compromisos y accionables concretos, y detecta cuándo la llamada requería derivación a un especialista."
related_modules: [B02, B06, E01, E04]
industries_instanced: [salud, servicios-fin]
tenants_in_examples: [sanrafael, cooppopular]
big_corp_vendors: [Gong, Chorus.ai, Salesforce Einstein Conversation]
latam_tools: [twilio-flex, whatsapp-business, asterisk]
key_concepts: [transcripcion, action-items, sentiment, hand-off, PII-scrubbing, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

Un asesor de **Coop. Popular de Crédito** atiende 25–35 llamadas al día. Al terminar cada llamada, debe escribir en el CRM un resumen de lo que se habló y las acciones pendientes. Hoy escribe el resumen de memoria, 5 minutos después de colgar, mientras ya está en la siguiente llamada. El resultado: el resumen dice «socio consultó por crédito» cuando el socio pidió que le enviaran el estado de cuenta, que le corrigieran un error de la cuota de marzo, y que lo llamaran el viernes antes de las 11 AM. La coordinadora CX lo descubre 3 días después cuando el socio llama enojado porque nadie lo llamó. La pérdida no es solo CX — es credibilidad.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Gong** | Grabación + transcripción + análisis de llamadas de ventas/soporte; detecta temas, sentimiento, momentos clave | 1200–1600 USD/usuario/año |
| **Chorus.ai (ZoomInfo)** | Similar a Gong; fuerte en integración con Salesforce | 800–1400 USD/usuario/año |
| **Salesforce Einstein Conversation Insights** | Análisis de llamadas integrado en Service Cloud; next-best-action post-llamada | Incluido en Service Cloud Enterprise (150–300 USD/agente/mes) |

En 2026, estas herramientas generan resúmenes y next-actions automáticamente al terminar la llamada y los sincronizan al CRM. El agente solo valida. Para una PYME de 90 empleados, el costo de Gong equivale al salario de un asesor.

---

## 3. PYME LATAM realista

**Coop. Popular de Crédito** y **Clínica San Rafael** operan con:

- **Asterisk / 3CX / Twilio** para la central telefónica: graban las llamadas en MP3/WAV en un servidor local o en la nube.
- **WhatsApp Business** para llamadas de voz o mensajes de voz (el caso LATAM más frecuente): los audios llegan como archivos `.ogg`.
- El asesor anota en **HubSpot Service** o **Freshdesk** o directamente en el CRM bancario / HIS (Health Information System para salud).
- Las grabaciones se guardan por cumplimiento pero nadie las analiza excepto en caso de disputa.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Grabación de llamada | MP3/WAV/OGG (3–20 min) | Central telefónica / WhatsApp | Por llamada | 500 KB – 10 MB |
| Metadatos de llamada | JSON (agente_id, cliente_id, duración, canal, timestamp) | CRM / central | Por llamada | 1 fila |
| Perfil del cliente | JSON (nombre, productos, tickets abiertos, historial) | CRM del tenant | Por llamada | 1 fila |
| Historial de llamadas anteriores | JSON array (últimos 5 resúmenes) | CRM del tenant | Por llamada | 0–5 resúmenes |

**Ejemplo de metadata**:

```json
{
  "call_id": "CALL-20260415-0094",
  "agent_id": "AGT-012",
  "customer_id": "SOC-2241",
  "duration_sec": 487,
  "channel": "phone",
  "timestamp": "2026-04-15T10:23:00Z",
  "tenant": "cooppopular"
}
```

---

## 5. Tramos determinísticos

1. **Transcripción de audio** — Whisper (OpenAI, self-hosted) o alternativa como `faster-whisper` convierte el audio a texto. Determinístico en el sentido de que es una función del audio: mismo audio → mismo texto (con varianza mínima de Whisper). Corre en CPU/GPU propio o vía API.
2. **PII scrubbing antes del LLM** — números de cuenta, DNI, números de tarjeta, números de teléfono se detectan por regex/NER y se reemplazan por `[CUENTA]`, `[DNI]`, `[TEL]` antes de enviar al modelo. Determinístico.
3. **Segmentación de turnos** — identificación de quién habla cuándo (diarización): `speaker_0` (agente) vs. `speaker_1` (cliente). Whisper con diarización o pyannote.audio. Determinístico.
4. **Extracción de hechos objetivos** — duración, hora, canal, agente, cliente: metadata pura del sistema.
5. **Verificación de compromisos explícitos** — regex sobre la transcripción para frases de compromiso directo: «le voy a enviar», «lo llamo el viernes», «queda pendiente». Captura los compromisos literales como primer paso antes del LLM.

---

## 6. Tramos agénticos

1. **Extracción de next-actions accionables** — el modelo lee la transcripción completa y extrae acciones con: quién hace qué, para cuándo, con qué medio. «Le voy a enviar el estado de cuenta» → `{owner: "agente", action: "enviar estado de cuenta", medium: "email", deadline: null, customer: "SOC-2241"}`. _Por qué no es regla_: el compromiso puede estar implícito («sí, claro, con mucho gusto lo revisamos» sin decir explícitamente «yo lo llamo»), o el deadline se menciona en lenguaje natural («antes del fin de semana»); necesita comprensión contextual.

2. **Evaluación del sentimiento y satisfacción** — el modelo evalúa el tono del cliente a lo largo de la llamada: ¿empezó frustrado y terminó tranquilo? ¿escaló? ¿no se resolvió? _Por qué no es regla_: el sentimiento en audio transcrito es contextual («sí, claro» puede ser sarcástico o genuino; solo el contexto previo lo aclara).

3. **Detección de derivación necesaria** — el modelo detecta si la llamada trataba un tema que debía haber sido atendido por un especialista (asesor de crédito, médico, abogado) y no lo fue. _Por qué no es regla_: «tengo una duda sobre mi seguro» puede resolverlo el asesor general o puede requerir al área de seguros según el detalle; el modelo lo distingue del contexto.

4. **Generación del resumen para el CRM** — párrafo de 3–5 líneas que describe qué se trató, qué se comprometió, y cuál es el estado. _Por qué no es regla_: un resumen útil no es una transcripción comprimida — es una interpretación del propósito y el resultado de la llamada.

> [!nota]
> El agente nunca envía el resumen al CRM sin que el agente humano lo revise y confirme. El flujo es: llamada termina → resumen + next-actions aparecen en la pantalla del agente en < 30 segundos → el agente edita si es necesario → confirma → el sistema lo sincroniza al CRM.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[receive_audio] → descarga grabación desde storage del tenant (determinístico)
  ↓
[transcribe] → Whisper → texto con diarización (determinístico)
  ↓
[scrub_pii] → regex + NER → reemplaza datos sensibles (determinístico)
  ↓
[enrich_context] → perfil del cliente + historial de llamadas (determinístico, tool: sql_query)
  ↓
[extract_actions] → next-actions accionables (agéntico)
  ↓
[evaluate_sentiment] → tono + satisfacción del cliente (agéntico)
  ↓
[detect_escalation] → ¿requería derivación? (agéntico)
    sí → [flag_escalation] → notifica supervisor (tool: post_slack_message)
  ↓
[draft_summary] → resumen para CRM (agéntico)
  ↓
[human_review] → agente revisa en su pantalla (siempre — interrupt)
  ↓
[sync_crm] → persiste resumen + next-actions en CRM (determinístico)
  ↓
END
```

### Activities Temporal

- `transcribe_audio(tenant, call_id)` — CPU-intensivo; con retry y timeout 5 min.
- `run_summary_agent(tenant, call_id)` — corre el grafo; timeout 60 seg.
- `sync_to_crm(tenant, call_id, summary)` — escritura idempotente al CRM.

### Tools necesarias

- `sql_query` — perfil del cliente + historial de llamadas del tenant.
- `post_slack_message` — alerta de escalación al supervisor.
- `write_report` — reporte semanal de KPIs de llamadas.

---

## 8. Salida y entrega

**Panel del agente post-llamada** (aparece en < 30 segundos):

```
## Resumen — Llamada CALL-20260415-0094 · 8:07 min

**Socio**: [SOC-2241] | Canal: teléfono | Agente: AGT-012

**Motivo**: Solicitud de estado de cuenta (producto: Cuenta de ahorros #[CUENTA]).
Además: discrepancia en cuota de marzo 2026 (cobro de [MONTO] vs. esperado [MONTO-2]).

**Estado de la llamada**: Resuelto parcialmente. El agente verificó el cobro de marzo
y confirmó que fue un cargo de administración aplicado desde enero. El socio no lo tenía claro.
Se comprometió a enviar el estado de cuenta por email.

**Sentimiento del cliente**: comenzó confundido y con tono elevado; terminó tranquilo
después de la explicación. Sin riesgo de escalación.

**Next-actions**:
| # | Quién | Acción | Medio | Deadline |
|---|-------|--------|-------|---------|
| 1 | AGT-012 | Enviar estado de cuenta 2026 | Email | Hoy antes de las 17h |
| 2 | AGT-012 | Registrar la duda sobre cargo de admin en FAQ | CRM | Esta semana |

**¿Requería derivación?**: No.

[✓ Confirmar y sincronizar al CRM]  [✎ Editar antes de guardar]
```

---

## 9. Cómo se vende

**Gancho**: «Tus asesores escriben el resumen de la llamada de memoria, 5 minutos después. Nosotros lo tenemos en 30 segundos, con cada compromiso detallado y sin olvidar nada».

**Propuesta de valor**: cero compromisos perdidos, 5–8 minutos/llamada ahorrados en documentación, trazabilidad completa para disputas y auditorías de calidad.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 500 llamadas/mes, 1 agente | 150–300 USD/mes |
| Growth | ≤ 3000 llamadas/mes, ≤ 10 agentes | 400–800 USD/mes |
| Enterprise | > 3000 llamadas/mes + integración CRM completa | 800–2000 USD/mes |
| Setup | Integración con central telefónica/WhatsApp + calibración | 1500–5000 USD |

---

## 10. Riesgos

**1. PII en la transcripción que llega al LLM.**
*Síntoma*: el número de cuenta del socio (mencionado durante la llamada) aparece en el payload enviado al modelo.
*Mitigación*: el nodo `scrub_pii` es obligatorio y corre antes de cualquier llamada al LLM. Lista de patrones (números de 16 dígitos, DNI formato país, teléfonos) + NER para nombres propios. En salud, aplica además el scrubbing de diagnósticos y nombres de medicamentos antes del modelo. En Colombia, los datos bancarios son datos sensibles bajo Ley 1581.

**2. Transcripción de baja calidad (ruido, acento, español regional).**
*Síntoma*: Whisper transcribe «cuota de marzo» como «cuota de marzo» en un caso y «cuota de marzo» en otro, pero en casos con acento costeño o fondo ruidoso comete errores que el LLM amplifica.
*Mitigación*: Whisper `large-v3` funciona bien con español latinoamericano; en entornos con mucho ruido usar `faster-whisper` con VAD (Voice Activity Detection). Incluir un paso de confianza de transcripción: si `avg_logprob < -0.5`, marcar la transcripción como «baja confianza» y no generar resumen automático — el agente la revisa manualmente.

**3. Consentimiento del cliente para grabación y procesamiento.**
*Síntoma*: se graban llamadas sin informar al cliente, infringiendo Ley 1581 o LGPD.
*Mitigación*: el IVR de entrada debe incluir el aviso de grabación y procesamiento automatizado. Este requisito es del tenant, no del sistema; el harness incluye un checklist de configuración que el tenant debe confirmar.

**4. Alucinación de next-actions que no se dijeron.**
*Síntoma*: el modelo inventa un compromiso («el agente prometió devolver el dinero en 24h») que no está en la transcripción.
*Mitigación*: el prompt exige que cada next-action tenga una cita textual de la transcripción (entre comillas); el harness verifica que las citas existan en el texto. Si una next-action no tiene cita, se marca como `inferred` y se destaca en el panel para que el agente la revise con más cuidado.

**5. Costo de transcripción para volúmenes altos.**
*Síntoma*: 3000 llamadas/mes × 8 min promedio = 400 horas de audio. Whisper API cobra $0.006/min → $144/mes manejable. Pero si se usa LLM para transcripción además del análisis, los costos se duplican.
*Mitigación*: usar Whisper self-hosted (faster-whisper en CPU) para transcripción; solo el LLM de análisis usa API externa. El costo del análisis con Sonnet 4.6 para 3000 llamadas × ~2000 tokens/llamada ≈ 6M tokens → ~$18/mes.

---

## 11. Variantes por industria

### Instancia 1 — Servicios financieros (`cooppopular`)

**Datos típicos**: 25–35 llamadas/agente/día; temas financieros con vocabulario técnico (cuotas, aportes, CDAT, crédito de libranza); socios con bajo nivel de alfabetización financiera; canal principal teléfono + WhatsApp voz.

**Delta determinístico**: además del PII estándar, scrubbing de números de cuenta, saldo, y monto de crédito. Los compromisos de fecha tienen valor legal en disputas — se guardan con timestamp y hash del audio de referencia.

**Delta agéntico**: el modelo detecta si el socio tomó una decisión financiera sin entender completamente los términos («sí, acepto» después de una explicación compleja de tasas). Estos casos se marcan para auditoría de calidad y posible contacto de seguimiento. La Superfinanciera puede exigir esto en auditorías de suitability.

**Regulación**: grabaciones de llamadas en sector financiero Colombia deben conservarse mínimo 5 años (Circular Básica Jurídica Superfinanciera). El pipeline de almacenamiento debe cumplir este retention.

**Precio orientativo**: 400–800 USD/mes; setup con integración core bancario 3000–8000 USD.

### Instancia 2 — Salud privada (`sanrafael`)

**Datos típicos**: 15–25 llamadas/día en call center de citas y urgencias; contenido sensible (síntomas, diagnósticos, medicamentos mencionados); alta carga emocional; WhatsApp Business para mensajes de voz de pacientes.

**Delta determinístico**: scrubbing de nombres de diagnósticos (CIE-10 términos), medicamentos, y cualquier mención de condición de salud antes del LLM. Esto es obligatorio bajo Ley 1581 para datos de salud (categoría especial de protección).

**Delta agéntico**: el modelo detecta si la llamada contiene indicios de urgencia médica no atendida («dijo que le duele mucho y no pudo dormir en 3 días») que requieren seguimiento inmediato. No hace diagnóstico — solo eleva la prioridad para revisión humana del área clínica.

**Regulación**: datos de salud son categoría especial bajo Ley 1581 (Colombia), LGPD (Brasil), y normativa sectorial de cada país. La transcripción se almacena cifrada; acceso restringido al área médica + RRHH; no disponible para marketing ni ventas.

**Precio orientativo**: 300–600 USD/mes; setup 2000–5000 USD (certificación de cumplimiento adicional).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **B06** — SSE + chat | El resumen post-llamada se entrega en streaming al panel del agente via SSE; el mismo patrón `EventSourceResponse` del módulo B06 funciona aquí, con el agente como «cliente» del stream. |
| **B02** — FastAPI routing | El endpoint `POST /calls/{call_id}/process` recibe el evento de fin de llamada del sistema de telefonía y dispara el pipeline; auth por `tenant_id` en el header. |
| **E01** — Anthropic SDK | El nodo `draft_summary` usa `cache_control: ttl:"1h"` sobre el system prompt con las instrucciones de formato de resumen del tenant (estático); la transcripción va sin cache (dinámica por llamada). |
| **E04** — Memoria de sesión | El historial de llamadas anteriores del cliente se inyecta como contexto; el agente recuerda si el mismo cliente llamó la semana pasada con el mismo problema y lo menciona en el resumen. |
| **D04** — Observabilidad | Cada llamada procesada genera un span en Phoenix con latencia de transcripción vs. latencia de análisis; si la transcripción tarda > 2 min, la traza lo alerta. El costo por llamada (tokens + Whisper) se acumula en el ledger por tenant. |

## 13. Errores típicos

**1. PII del cliente en el texto enviado al LLM antes del scrubbing.**
*Síntoma*: el número de cuenta del socio («mi cuenta 0034-5678-9012 tiene un error») aparece en el payload del nodo `extract_actions` y queda en las trazas del LLM.
*Causa raíz*: el orden de los nodos en el grafo coloca `enrich_context` antes de `scrub_pii`, y el texto enriquecido con datos del CRM nunca pasa por el scrubber.
*Cómo evitarlo*: `scrub_pii` debe correr inmediatamente después de la transcripción y antes de cualquier llamada al LLM, sin excepciones. En Colombia, los datos bancarios son datos sensibles bajo Ley 1581; en Brasil, datos financieros son datos personales protegidos por la LGPD. Una fuga en el log del LLM proveedor es una violación notificable.

**2. Next-action alucinada que el agente humano aprueba sin leer.**
*Síntoma*: el resumen indica «el agente se comprometió a hacer una devolución de COP 80.000» cuando en la llamada nunca se dijo eso; el agente humano confirma sin revisar y el CRM queda con un compromiso falso.
*Causa raíz*: el prompt no exige cita textual de la transcripción para cada next-action; el modelo infiere compromisos que parecen razonables pero no fueron explícitos.
*Cómo evitarlo*: cada next-action debe incluir un campo `quote` con la frase exacta de la transcripción. El harness verifica que el `quote` exista en el texto; si no existe, la next-action se marca `inferred` y se resalta en rojo en el panel del agente.

**3. Transcripción de baja calidad usada para generar resumen sin alerta.**
*Síntoma*: el resumen generado es incoherente porque la transcripción tenía `avg_logprob < -0.8` (mucho ruido de fondo en la llamada), pero el pipeline continuó sin advertir al agente.
*Causa raíz*: el nodo `transcribe` no verifica la métrica de confianza de Whisper antes de continuar.
*Cómo evitarlo*: validar `avg_logprob > -0.5` como gate. Si no pasa, el pipeline marca la transcripción como `low_confidence` y el panel del agente muestra una advertencia explícita; el agente debe revisar la transcripción completa antes de confirmar el resumen.

**4. Resumen sincronizado al CRM sin revisión del agente humano.**
*Síntoma*: por un error de configuración, el paso `human_review` tiene `timeout = 0` y el sistema sincroniza automáticamente si el agente no actúa en 0 segundos.
*Causa raíz*: el timeout del interrupt no fue configurado apropiadamente en el harness.
*Cómo evitarlo*: el interrupt de `human_review` no tiene timeout automático; el resumen permanece en estado `pending_review` hasta que el agente confirma o edita. La sincronización al CRM es siempre un paso posterior al confirm explícito.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué el PII scrubbing debe correr antes del LLM y no después, y qué pasa si lo hago al revés en un entorno de producción con un proveedor de LLM externo.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si mis llamadas son mensajes de voz de WhatsApp de 30 segundos en lugar de llamadas telefónicas grabadas de 8 minutos, y si muchos de mis clientes hablan en español con acento costeño colombiano.»
3. **Por qué falló**: «El resumen de la llamada CALL-20260415-0094 inventó una next-action de devolución que el agente aprobó. ¿En qué nodo del workflow ocurrió el fallo y cómo lo prevengo con un cambio mínimo en el prompt y en el harness de validación?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline completo de transcripción, scrubbing de PII y extracción de next-actions con la separación correcta de tramos determinísticos y agénticos.
- Implementar el PII scrubbing con regex y NER antes de cualquier llamada al LLM, cumpliendo los requisitos de Ley 1581 y LGPD.
- Configurar el interrupt de revisión humana de forma que el resumen nunca se sincronice al CRM sin confirmación explícita del agente.
- Evaluar la calidad de la transcripción con la métrica `avg_logprob` de Whisper y decidir cuándo detener el pipeline.
- Dimensionar el costo de transcripción y análisis para volúmenes de 500–3000 llamadas mensuales con Whisper self-hosted más Anthropic API.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK + tools | Los nodos `extract_actions` y `draft_summary` usan `cache_control` sobre el system prompt estático; sin E01, el estudiante no configura correctamente el caching ni el tool calling con respuesta estructurada. |
| **E04** — Memoria y sesiones | El historial de llamadas anteriores del mismo cliente se inyecta como contexto de sesión; E04 enseña a gestionar este estado sin contaminar llamadas de otros clientes. |
| **B06** — SSE + streaming | El resumen se entrega en streaming al panel del agente en < 30 segundos via `EventSourceResponse`; sin B06, el estudiante implementa polling en lugar de streaming. |
| **D04** — Observabilidad y trazas auditables | La latencia de transcripción vs. análisis y el costo por llamada se acumulan en Phoenix; D04 enseña a construir dashboards de costo y calidad sobre estas trazas. |
