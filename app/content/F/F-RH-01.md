---
ext_id: F-RH-01
slug: screening-cvs
track: F
dept: RH
ord: 220
title: "Screening de CVs por descripción de cargo"
summary: "Agente que extrae campos estructurados de CVs y rankea candidatos según un JD, sin rechazar automáticamente a nadie."
related_modules: [A06, B02, E01, E03]
industries_instanced: [hospitalidad, serv-prof]
tenants_in_examples: [mesonurbano, consultorabc]
big_corp_vendors: [Workday Recruiting, HireVue, Eightfold AI]
latam_tools: [computrabajo, indeed-latam, linkedin-recruiter]
key_concepts: [must-have-vs-nice, sesgo-protegido, transparencia, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.3
version: 1
---

## 1. Problema operativo

La jefa de talento de **Mesón Urbano** recibe 120 CVs por semana para puestos de cocina y servicio. Los lee todos manualmente en PDF, copiando datos en una hoja de cálculo para comparar. Pierde 6–8 horas semanales y aun así se le escapan candidatos con experiencia relevante porque el CV no usa las palabras exactas del aviso. El problema no es la cantidad: es que la extracción de información y el matching son tareas de parseo + juicio, y hoy las hace una sola persona a mano.

---

## 2. Hoy en big corps

Las empresas con presupuesto dedican estas plataformas a la capa de screening:

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Workday Recruiting** | ATS completo con scoring ML integrado | 6–15 USD/empleado/mes; impl. 50–200 k USD |
| **HireVue** | Video screening + análisis conductual + scoring CV | 25–75 USD/candidato o ≥ 75 k USD/año |
| **Eightfold AI** | Matching semántico entre talent graph y JD | 150–400 k USD/año contrato enterprise |

Workday y HireVue son el estándar para empresas con > 500 empleados. Eightfold compite en el espacio de talent intelligence para corporativos que hacen decenas de miles de contrataciones al año. Ninguna de estas opciones es viable para una PYME de 80 personas.

---

## 3. PYME LATAM realista

**Mesón Urbano** (F&B, 80 empleados) y **Consultora ABC** (servicios profesionales, 35 personas) operan con:

- Avisos en **Computrabajo** o **Indeed LATAM** (plan gratuito o ≤ 50 USD/mes) que reciben CVs en PDF por email o descarga masiva.
- Una hoja de **Google Sheets** donde HR copia nombre, años de experiencia, y una nota.
- Sin ATS. El historial de candidatos se pierde entre correos.

El pipeline que propone esta ficha reemplaza la hoja de cálculo con un agente que lee los PDFs, extrae campos estructurados, y produce un ranking justificado. No reemplaza al reclutador: le entrega una lista priorizada con razones.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| CV del candidato | PDF (1–3 páginas) | Email / portal | Por proceso; 20–150 CVs | 100–500 KB/archivo |
| Job Description | Texto libre (MD o DOCX) | HR o Notion | Por proceso | 200–800 palabras |
| Criterios must-have | Lista YAML por proceso | HR al configurar | Por proceso | 3–8 ítems |
| Criterios nice-to-have | Lista YAML por proceso | HR al configurar | Por proceso | 2–5 ítems |

**Ejemplo de fila extraída** (candidato, no raw):

```json
{
  "name_hash": "sha256:a3f2...",
  "years_exp": 4,
  "languages": ["es", "en"],
  "city": "Medellín",
  "last_role": "Jefe de partida",
  "certifications": ["HACCP"],
  "raw_text_excerpt": "...lideré brigada de 6 cocineros en restaurante de 120 cubiertos..."
}
```

> [!nota]
> El `name_hash` reemplaza al nombre real antes de enviarlo al modelo. El nombre se restaura solo en la capa de presentación, con acceso restringido. Esto minimiza el riesgo de sesgo por nombre.

---

## 5. Tramos determinísticos

1. **OCR del PDF** — `pdfplumber` o `pymupdf` extrae texto. Sin LLM. Layout estable para el 90% de CVs generados por Word/Canva.
2. **Extracción de campos estructurados** — regex + heurísticas: años totales de experiencia (suma de rangos de fecha), idiomas (sección "idiomas" o marcadores "English: B2"), ciudad (última dirección o encabezado), certificaciones (lista conocida: HACCP, ServSafe, PMP, CISA…).
3. **Anonimización de PII** — eliminar nombre, email, teléfono, foto, edad, género, estado civil del payload antes de llamar al LLM.
4. **Filtro de must-haves duro** — candidatos que no cumplen un requisito marcado como `required: true` quedan en estado `disqualified_deterministic` con razón explícita. El modelo no los ve.
5. **Construcción de la cola del modelo** — los candidatos que pasan el filtro duro se serializan con `raw_text_excerpt` (≤ 500 tokens/candidato) para el tramo agéntico.

---

## 6. Tramos agénticos

1. **Lectura del match real entre experiencia narrativa y JD** — el modelo recibe el JD, los criterios nice-to-have, y el texto resumido del CV sin PII. Decide si la experiencia descrita —aunque no use las palabras exactas del JD— cubre las responsabilidades. _Por qué no es regla_: «lideré brigada de 6 cocineros» y «chef de línea con supervisión» cubren el mismo must-have «gestión de personal en cocina», pero no hay regex que los empareje sin contexto.

2. **Scoring con justificación por criterio** — el modelo asigna un score 0–10 por cada criterio nice-to-have y escribe una frase de razón por criterio. _Por qué no es regla_: el peso relativo de un criterio depende del contexto del proceso («este proceso prioriza idiomas porque es para turismo internacional»), que varía por tenant y por convocatoria.

3. **Detección de señales de riesgo de sesgo** — si la salida del modelo contiene lenguaje que correlaciona con atributos protegidos (edad inferida, género, origen), el harness lo marca y lo redirige a revisión humana antes de mostrar. _Por qué no es regla_: los sesgos lingüísticos son implícitos; detectarlos exige comprensión del lenguaje.

> [!cuidado]
> El agente **nunca rechaza** a un candidato automáticamente. Solo produce un ranking con justificación. La decisión de avanzar o no la toma un humano. Este no-negociable debe estar en los términos de servicio del cliente.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[ingest_cvs] → descarga PDFs desde carpeta/email (determinístico)
  ↓
[extract_fields] → OCR + regex por CV (determinístico)
  ↓
[anonymize] → elimina PII, genera name_hash (determinístico)
  ↓
[filter_must_haves] → descarta sin criterios requeridos (determinístico)
  ↓
[rank_agent]  → loop agéntico: score + razón por candidato
    tools: sql_query (criterios tenant), fetch_excel (criterios adicionales)
  ↓
[bias_check]  → revisa output del modelo (agéntico, tool: flag_bias)
  ↓
[human_review?] → interrupt_before si bias_check.flagged > 0
  ↓
[write_report] → ranking anonimizado + razones (determinístico, tool: write_report)
  ↓
END
```

### Activities Temporal (cuando el proceso es recurrente/masivo)

- `download_cvs(tenant, job_id)` — IO con retry; idempotente por `job_id`.
- `run_screening_agent(tenant, job_id, cv_batch)` — corre el grafo; hasta 20 CVs por batch para controlar tokens.
- `persist_ranking(tenant, job_id, ranking)` — escritura con `idempotency_key = "screen:{tenant}:{job_id}"`.

### Tools necesarias

- `fetch_excel` — criterios nice-to-have si HR los mantiene en Sheets.
- `sql_query` — historial de candidatos previos del tenant (para evitar duplicados).
- `write_report` — ranking final en PDF o MD.

---

## 8. Salida y entrega

**Formato de output** (tabla Markdown enviada por email o guardada en Drive):

```
## Ranking — Cocinero Senior · Proceso #2026-04 · Mesón Urbano

| # | ID candidato | Score total | Exp. (años) | Ciudad    | Razón principal |
|---|-------------|-------------|-------------|-----------|-----------------|
| 1 | CAND-0041   | 8.4 / 10    | 6           | Medellín  | Liderazgo brigada + HACCP confirmado |
| 2 | CAND-0019   | 7.1 / 10    | 4           | Bogotá    | Experiencia en fine dining; sin cert. |
| 3 | CAND-0073   | 6.8 / 10    | 5           | Medellín  | Perfil sólido; inglés no verificado   |
...

Candidatos descartados por requisito duro: 31 (ver anexo).
Candidatos con alerta de revisión de sesgo: 2 (ver anexo confidencial).

⚠ Este ranking es una sugerencia. La decisión de avanzar la toma RRHH.
```

**Canal de entrega**: email automático a HR + link a Drive del tenant. Nunca se envía la lista completa a un manager sin aprobación de HR.

---

## 9. Cómo se vende

**Gancho**: «Tu recruiter gasta 6 horas semanales leyendo CVs. Nosotros lo dejamos en 30 minutos de revisión de un ranking con razones».

**Propuesta de valor**: velocidad + trazabilidad (cada decisión tiene razón documentada) + reducción de sesgo inconsciente (anonimización + bias check).

**Precio orientativo**:

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | ≤ 3 procesos/mes, ≤ 50 CVs/proceso | 150–300 USD/mes |
| Growth | ≤ 10 procesos/mes, ≤ 200 CVs/proceso | 400–800 USD/mes |
| Setup (una sola vez) | Integración email/Drive, calibración criterios | 500–1500 USD |

---

## 10. Riesgos

**1. Sesgo del modelo.**
*Síntoma*: candidatos de ciertas ciudades o con nombres específicos reciben scores consistentemente menores.
*Mitigación*: anonimización de PII antes del modelo + bias check post-inferencia + auditoría mensual del ranking con golden set. En Colombia aplica **Ley 1581 de 2012** (habeas data); en México **LFPDPPP**; en Brasil **LGPD** — en todos los casos, el candidato tiene derecho a conocer los criterios de evaluación.

**2. PII en el payload del modelo.**
*Síntoma*: el campo `raw_text_excerpt` incluye nombre o foto codificada en base64.
*Mitigación*: el nodo `anonymize` corre antes de cualquier llamada al LLM. Test automático que verifica que `name`, `email`, `phone` no estén en el texto enviado al modelo.

**3. Rechazo automático percibido.**
*Síntoma*: el cliente configura el sistema para descartar automáticamente candidatos con score < 5 sin revisión humana.
*Mitigación*: el harness bloquea cualquier acción de descarte sin `human_approved: true`. Esto se documenta en el contrato de servicio y en la pantalla de configuración.

**4. Alucinación de certificaciones.**
*Síntoma*: el modelo «confirma» una certificación que el CV no menciona explícitamente.
*Mitigación*: el tramo determinístico extrae certificaciones de una lista cerrada; el LLM solo evalúa si el texto narrativo *sugiere* la competencia, no si la certifica. La columna «certificación confirmada» solo se marca si el extractor determinístico la encontró.

**5. Costo por proceso masivo.**
*Síntoma*: 200 CVs × 500 tokens = 100 K tokens de entrada; con Sonnet 4.6 a $3/MTok → ~$0.30/proceso, manejable. Si el cliente tiene 1000 CVs, sube a $1.50/proceso.
*Mitigación*: el nodo `filter_must_haves` descarta antes del LLM; típicamente reduce el batch un 40–60%. Hard limit configurable por tenant.

---

## 11. Variantes por industria

### Instancia 1 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 20–60 CVs/proceso; alta rotación (cocineros, meseros, bartenders); CVs cortos (1 página, a veces sin formato); en WhatsApp Business se reciben fotos de CV o texto plano.

**Delta determinístico**: parser de texto plano (WhatsApp forward sin PDF); normalización de títulos de cargo («ayudante de cocina» = «kitchen helper» = «auxiliar de cocina»).

**Delta agéntico**: inferir experiencia real cuando el CV dice solo «trabajé en varios restaurantes» sin fechas; puntuar la coherencia de la trayectoria para un rol operativo.

**Regulación LATAM**: Colombia — Ley 1581 (datos laborales sensibles); conservar CVs rechazados máximo 1 año si el candidato no da consentimiento explícito.

**Precio orientativo**: 150–350 USD/mes (volumen moderado, procesos frecuentes).

### Instancia 2 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 10–30 CVs/proceso; roles de consultor senior, gerente de proyecto; CVs largos (2–4 páginas); candidatos con LinkedIn estructurado + PDF formal.

**Delta determinístico**: extracción de proyectos con cliente/duración/rol del candidato; verificación de certificaciones profesionales (PMP, CISA, ITIL) contra lista cerrada.

**Delta agéntico**: evaluar si la experiencia en proyectos de mediana empresa es transferible a cliente objetivo (manufactura, banca); leer si el perfil de liderazgo encaja con cultura declarada del cliente; peso mayor en «reasoning sobre proyectos» que en títulos.

**Regulación LATAM**: México — LFPDPPP obliga a notificar al candidato que sus datos se procesan con herramientas automatizadas; incluir aviso en el formulario de postulación.

**Precio orientativo**: 300–700 USD/mes (menor volumen, mayor complejidad por CV).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **A06** — Type hints y Pydantic | El schema del CV extraído (`CVExtract`) se valida con Pydantic antes de entrar al LLM; si falla validación, el nodo `extract_fields` lanza excepción determinística. |
| **B02** — FastAPI routing + deps | El endpoint `POST /jobs/{job_id}/screen` recibe el batch de CVs y dispara el workflow; el `Depends(get_tenant)` garantiza aislamiento. |
| **E01** — Anthropic SDK + tools | El nodo `rank_agent` implementa el loop messages + tool_use; `cache_control` marca el JD y criterios (estáticos por proceso) con `ttl: "1h"` para abaratar runs masivos. |
| **E03** — Skills por tenant | Los criterios nice-to-have y el tono del ranking (formal/casual) se inyectan como skill por tenant en el system prompt; no están hardcodeados. |
| **D04** — Observabilidad | Cada llamada al LLM se traza en Phoenix con span de latencia y tokens; si un CV tarda > 10 s, la traza lo marca y alerta. |
| **E05** — Temporal | Para procesos con > 100 CVs, el workflow corre en Temporal con `run_screening_agent` como activity (retry policy + timeout); el scheduler lo puede lanzar la noche del cierre del proceso. |

## 13. Errores típicos

**1. Sesgo por nombre en el payload del modelo.**
*Síntoma*: candidatos con nombres que el modelo asocia estadísticamente a ciertos orígenes reciben scores sistemáticamente más bajos, aunque la experiencia sea equivalente.
*Causa raíz*: el nodo `anonymize` omitió algún campo (p. ej., email con nombre en el dominio, o encabezado del PDF no limpiado).
*Cómo evitarlo*: test automático que verifique que `name`, `email`, y cualquier campo derivado no aparecen en el texto enviado al LLM; ejecutar en CI antes de cada deploy.

**2. Inferencia ilegal de atributos protegidos.**
*Síntoma*: la justificación del score menciona «trayectoria no lineal» o «gap de 2 años» sin contexto, lo que puede correlacionar con maternidad, enfermedad o migración — atributos protegidos bajo Ley 1581 (Colombia) y LFPDPPP (México).
*Causa raíz*: el prompt no restringe explícitamente el razonamiento sobre continuidad temporal del CV.
*Cómo evitarlo*: añadir al system prompt `"No hagas inferencias sobre la causa de pausas en el historial laboral. Evalúa solo la experiencia documentada."` Auditar el golden set mensualmente.

**3. Candidatos descartados por el filtro duro con criterio mal configurado.**
*Síntoma*: el 80% de los CVs quedan en `disqualified_deterministic`; la lista final tiene solo 3 candidatos y ninguno es el idóneo.
*Causa raíz*: un criterio marcado como `required: true` era en realidad preferido, no excluyente.
*Cómo evitarlo*: validar con RRHH los must-haves antes de lanzar el proceso; el sistema debe mostrar cuántos candidatos descarta cada criterio duro antes de confirmar la configuración.

**4. El agente toma decisión de contratación final.**
*Síntoma*: el equipo de RRHH configura un umbral («avanzar automáticamente a candidatos con score ≥ 8») y omite la revisión humana.
*Causa raíz*: el harness no bloquea la acción de avance automático.
*Cómo evitarlo*: el agente **nunca toma la decisión de contratación final**. El nodo `human_review` es no-removible. Documentar en el contrato de servicio que el sistema es una herramienta de apoyo, no un decisor autónomo. En Colombia aplica Ley 1581; en Brasil, LGPD art. 20 exige revisión humana en decisiones automatizadas con efectos jurídicos.

**5. Alucinación de competencias no documentadas.**
*Síntoma*: el ranking justifica un score alto con «el candidato demuestra liderazgo» pero el CV solo menciona que «participó» en un proyecto de equipo.
*Causa raíz*: el modelo infiere competencias a partir de lenguaje ambiguo.
*Cómo evitarlo*: el prompt debe pedir evidencia textual explícita para cada criterio evaluado; el harness verifica que cada justificación cita un fragmento real del `raw_text_excerpt`.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre un criterio must-have determinístico y un criterio nice-to-have agéntico? Dame un ejemplo con un puesto de cocina y otro con un consultor senior.»
2. **Aplícalo a mi caso**: «Cómo adaptaría el nodo `anonymize` si los CVs llegan como fotos de WhatsApp en lugar de PDFs generados por Word.»
3. **Por qué falló**: «El modelo le dio un score alto a un candidato que claramente no cumple el requisito de idioma. ¿En qué nodo falló y cómo lo detecto en la traza de Phoenix?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de screening con anonimización de PII antes de cualquier llamada al LLM.
- Separar los tramos determinísticos (OCR, filtro de must-haves, construcción de cola) de los agénticos (match semántico, scoring con justificación, bias check).
- Configurar los criterios must-have y nice-to-have por proceso y por tenant sin hardcodear ningún valor.
- Implementar el bias check post-inferencia y el fallback humano obligatorio antes de entregar el ranking.
- Explicar por qué el agente nunca toma la decisión de contratación final y cómo documentar esa restricción en el contrato de servicio.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **C02** — Multitenancy y RLS | Los CVs y los criterios de selección son datos sensibles segregados por empresa: sin RLS bien implementado, una empresa podría ver el pipeline de candidatos de otra. Esta ficha asume que `tenant_id` filtra todos los accesos. |
| **A06** — Pydantic y type hints | El schema `CVExtract` valida la salida del nodo `extract_fields` antes de entrar al LLM; entender cómo funciona la validación es prerequisito para construir el pipeline sin sorpresas. |
| **E01** — Anthropic SDK + tools | El nodo `rank_agent` implementa el loop messages + tool_use con `cache_control`; sin entender el SDK, el costo por proceso masivo se dispara. |
| **D04** — Observabilidad | Detectar alucinaciones de certificaciones o sesgos lingüísticos requiere trazas en Phoenix; sin observabilidad no hay forma de auditar el ranking. |
