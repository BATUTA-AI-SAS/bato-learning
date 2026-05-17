---
ext_id: F-LEG-02
slug: due-diligence-kyc-aml
track: F
dept: LEG
ord: 261
title: "Due diligence preliminar (KYC/AML básico)"
summary: "Agente que verifica a una persona natural o jurídica contra listas de sanción, PEP y riesgo reputacional, genera un expediente preliminar y escala al oficial de cumplimiento si hay señales."
estimated_minutes: 60
industries_instanced: [servicios-fin, salud]
tenants_in_examples: [cooppopular, sanrafael]
---

## 1. Problema operativo

El oficial de cumplimiento de Coop. Popular de Crédito debe revisar a cada nuevo asociado antes de aprobar una cuenta o un crédito. La regulación colombiana (SARLAFT / SAGRILAFT) exige un proceso documentado de conocimiento del cliente. Hoy el proceso es: buscar manualmente el nombre en la lista Clinton, en OFAC, en el RUT, pedir documentos por email, esperar, archivar en PDF. Un proceso que debería tomar 30 min toma 3 días porque nadie lo hace de inmediato.

Clínica San Rafael tiene el mismo problema para contratar proveedores: la regulación de salud exige verificar habilitaciones, antecedentes disciplinarios y, en algunos contratos, listas de inhabilitados del sector público.

El agente no es el oficial de cumplimiento. Hace el legwork; el oficial decide.

---

## 2. Hoy en big corps

Los bancos grandes y las multilaterales usan plataformas de screening dedicadas con bases de datos propias actualizadas en tiempo real.

| Vendor | Capacidad | Precio orientativo |
|--------|-----------|-------------------|
| **LSEG World-Check** (ex-Refinitiv) | PEP, sanciones, watchlists de +240 países; estándar en banca corresponsal | Enterprise; típicamente 5 000–50 000 USD/año según volumen de consultas |
| **ComplyAdvantage** | API-first, actualización en tiempo real con NLP sobre medios; fuerte en fintechs | API desde ~500 USD/mes (starter), escala por hit |
| **Dow Jones Risk & Compliance** | PEP, adverse media, ownership; integración SWIFT | Enterprise, cotización directa |
| **Truora** (LATAM) | Validación de identidad + listas en Colombia, México, Brasil | Desde 1–3 USD por consulta; planes desde 200 USD/mes |

La PYME no puede pagar World-Check. Puede pagar Truora o ComplyAdvantage starter. O puede construir su propio crawler sobre listas públicas.

---

## 3. PYME LATAM realista

Coop. Popular de Crédito trabaja con:
- Lista Clinton (OFAC SDN) — descargable en CSV, actualización diaria.
- Listas ONU (Comité 1267) — XML público.
- Lista de inhabilitados SECOP II (Colombia) — portal público, sin API oficial.
- RUT (DIAN) — verificación de NIT, también sin API limpia.
- Consulta manual en Google de noticias negativas ("nombre + fraude / lavado / sanción").

Clínica San Rafael añade:
- RETHUS (Registro del Talento Humano en Salud) para verificar habilitación de médicos y enfermeros.
- Lista de inhabilitados del MEN para proveedores de capacitación.

El proceso es manual, lento y sin trazabilidad. Cuando la Superintendencia Financiera (SFC) pide evidencia del proceso KYC, se busca el email donde alguien dijo "lo revisé".

---

## 4. Datos típicos

| Atributo | Detalle |
|----------|---------|
| Sujeto | Persona natural (nombre, CC/CE, fecha nacimiento, país) o jurídica (razón social, NIT, representante legal) |
| Fuentes determinísticas | OFAC SDN CSV (diario), ONU XML (semanal), SECOP inhabilitados CSV, Truora API (si se contrata) |
| Fuentes agénticas | Google News, portales de medios regionales, LinkedIn (reputación) |
| Volumen | 10–100 consultas/mes para cooperativa media; picos al inicio de mes (apertura de cuentas) |
| Formato de salida | Expediente JSON + PDF resumen; almacenado en tabla `kyc_reviews` con `tenant_id` |
| Ejemplo de registro | `{subject_id: "CC-12345678", name: "Carlos Rodríguez Mora", nationality: "CO", dob: "1975-03-12", lists_checked: ["OFAC","ONU","SECOP"], hits: [], risk_score: "LOW", escalated: false}` |

---

## 5. Tramos determinísticos

1. **Normalización del nombre**: `unidecode` + strip de tildes + tokenización. Genera variantes: iniciales, orden invertido (Mora Carlos Rodríguez). Esto reduce falsos negativos por tipografía.
2. **Match exacto contra listas**: búsqueda en tabla local de listas descargadas (`ofac_sdn`, `un_1267`, `secop_inhabilitados`). Match si `jaro_winkler(name_normalized, list_entry) > 0.92`.
3. **Extracción de campos documentales**: leer CC/NIT desde el documento adjunto con regex sobre texto extraído (OCR si es imagen).
4. **Verificación RUT activo**: llamada a API de tercero (Truora o similar) o scraping controlado del portal DIAN. Retorna `estado: activo|inactivo|cancelado`.
5. **Scoring de riesgo inicial**: `risk_score = weighted_sum(country_risk, sector_risk, pep_flag, list_hits)`. Regla cerrada documentada en el playbook del tenant.
6. **Archivado del expediente**: guardar todas las evidencias (JSON de cada fuente, timestamps, versión de lista usada) en storage inmutable para auditoría SFC.

---

## 6. Tramos agénticos

1. **Desambiguación de hits en listas** — "Juan Pérez" aparece en la lista OFAC pero la persona es colombiana, nacida en 1975, sin conexión con el país o sector del listado. El modelo recibe el hit completo (nombre, alias, fecha, país, descripción) y el perfil del sujeto, y decide si es `match_real`, `match_probable` o `false_positive`, con justificación.

   *Por qué no es regla*: los nombres hispanos son altamente repetidos. Una regla de similitud de nombres genería un volumen de falsos positivos inaceptable. El contexto (país, fecha de nacimiento, sector) no cabe en un threshold numérico único.

2. **Análisis de adverse media** — búsqueda en Google News y portales regionales por `"{nombre}" AND (fraude OR lavado OR sanción OR condena OR investigado)`. El modelo lee los resultados, filtra ruido (artículos de deporte, homónimos), y clasifica: `no_adverse`, `informativo`, `preocupante`, `crítico`.

   *Por qué no es regla*: la relevancia de una noticia depende del tiempo (una noticia de 2005 sin seguimiento es diferente a una de 2026 activa), de la fuente, y de si toca al sujeto directamente o a una empresa asociada.

3. **Redacción del expediente narrativo** — el modelo sintetiza todos los hallazgos en un párrafo ejecutivo ("El señor Rodríguez Mora no presenta coincidencias en listas de sanción. Se detectó una nota periodística de 2021 en El Colombiano sobre una investigación preliminar de la Contraloría que fue archivada en 2022. Riesgo residual: bajo.").

   *Por qué no es regla*: la narrativa debe integrar múltiples fuentes con matices temporales. Una concatenación automática de campos produce texto inútil para el oficial de cumplimiento.

4. **Fallback humano obligatorio**: cualquier `match_probable` o `match_real`, cualquier adverse media `preocupante` o `crítico`, escala automáticamente al oficial de cumplimiento con una tarea en el sistema. El agente **no aprueba ni rechaza** al sujeto. Solo clasifica y escala. Esta regla es no-negociable y está hardcodeada en el workflow, no en el prompt.

---

## 7. Blueprint del workflow

```
[INGEST]
  subject_data (nombre, doc, nationality, sector)
      |
[NORMALIZE]
  name_normalizer → variantes (determinístico)
      |
  ┌────────────────────────────────────┐
  │  PARALLEL DETERMINISTIC CHECKS     │
  │  ├─ ofac_matcher                   │
  │  ├─ un_1267_matcher                │
  │  ├─ secop_matcher                  │
  │  └─ rut_verifier (API)             │
  └────────────────┬───────────────────┘
                   │
[RISK_SCORE]                     (determinístico — regla cerrada del playbook)
  risk_score: LOW / MEDIUM / HIGH
      │
[DISAMBIGUATE_HITS]              ← agéntico (solo si hay hits)
  LLM: (hit_data, subject_profile) → {match_type, confidence, rationale}
      │
[ADVERSE_MEDIA_SEARCH]           ← agéntico
  search_tool → LLM: classifies relevance → adverse_media_level
      │
[DRAFT_NARRATIVE]                ← agéntico
  LLM: (all_findings) → expediente_paragraph
      │
[ESCALATION GATE]                (determinístico — regla dura)
  match_probable | match_real | adverse_media >= "preocupante"
  → crear tarea para oficial de cumplimiento (obligatorio, no bypasseable)
      │
[ARCHIVE]
  guardar expediente completo con evidencias + versión de listas usadas
```

**Tools necesarias**:
- `search_sanction_list(name_variants: list[str], list_id: str) -> list[SanctionHit]`
- `verify_rut(nit: str, tenant_id: str) -> RUTStatus`
- `search_news(query: str, date_from: str) -> list[NewsResult]`
- `disambiguate_hit(hit: SanctionHit, subject: SubjectProfile) -> DisambiguationResult` (LLM)
- `classify_adverse_media(results: list[NewsResult], subject: SubjectProfile) -> AdverseMediaLevel` (LLM)
- `draft_narrative(findings: KYCFindings) -> str` (LLM)
- `escalate_to_officer(subject_id: str, tenant_id: str, reason: str) -> TaskID`

---

## 8. Salida y entrega

**Expediente KYC** (PDF + JSON archivado):

```
EXPEDIENTE KYC — Persona Natural
Tenant: Coop. Popular de Crédito | Fecha: 2026-05-16 | Sujeto: CC-12345678

RESUMEN
  Nombre: Carlos Rodríguez Mora | DOB: 1975-03-12 | Nacionalidad: CO
  Riesgo inicial: BAJO | Listas chequeadas: OFAC SDN v20260516, ONU 1267 v20260510, SECOP
  Hits en listas: 0 coincidencias directas, 1 coincidencia homónima descartada
  Adverse media: NINGUNO relevante encontrado
  Resultado: APROBADO PRELIMINARMENTE — Oficial de cumplimiento puede proceder

DETALLE DE HITS DESCARTADOS
  OFAC SDN: "Juan Carlos Rodriguez" (Venezolano, 1943) — descartado (diferente DOB y país)

NARRATIVE
  El señor Carlos Rodríguez Mora no presenta coincidencias en listas de sanción internacionales
  ni nacionales. La búsqueda de adverse media no arroja noticias relevantes vinculadas al
  sujeto. Se recomienda proceder con la apertura de cuenta sujeto a verificación presencial
  de documentos.

EVIDENCIAS ARCHIVADAS
  ofac_sdn_v20260516.json | un_1267_v20260510.json | rut_dian_20260516.json
```

---

## 9. Cómo se vende

**Gancho**: "El proceso KYC que hoy te toma 3 días y lo hace un humano buscando en Google, lo hace el agente en 4 minutos y deja trazabilidad para la SFC."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | 50 consultas/mes, listas públicas (OFAC, ONU), sin adverse media | 300–500 USD/mes |
| Profesional | 200 consultas/mes, + Truora API, adverse media básico | 600–1 200 USD/mes |
| Compliance-ready | 500 consultas/mes, expediente PDF archivado, integración SFC-reporting | 1 000–2 500 USD/mes |

Setup (configuración del playbook de riesgo por tenant, calibración de umbrales): 1 500–4 000 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Falso negativo en lista de sanción** (match real no detectado) | Multa SFC, responsabilidad penal del oficial de cumplimiento | (1) Usar siempre la versión más reciente de la lista (descarga automática diaria). (2) Umbral de similitud conservador (Jaro-Winkler > 0.92 + review humano de todos los borderline). (3) Nunca solo el modelo decide: la clasificación del modelo sobre hits es revisada por el oficial. |
| **El agente no reemplaza al oficial de cumplimiento — riesgo regulatorio** | Si se usa como aprobación final, hay responsabilidad legal sin respaldo | Disclaimer en el expediente: "Este documento es un insumo de revisión preliminar. La decisión final de KYC corresponde al oficial de cumplimiento del tenant. No constituye aprobación regulatoria." |
| **PII de los sujetos consultados** | Violación de Ley 1581/2012 (Habeas Data, Colombia) y leyes equivalentes | Datos del sujeto procesados bajo la cláusula de obligación legal (art. 10c, Ley 1581). No se usa para entrenamiento. Retención máxima definida por regulación sectorial. `tenant_id` aísla completamente los datos. |
| **Falso positivo** (persona inocente marcada como riesgo) | Daño reputacional, demanda del sujeto | El expediente siempre muestra la evidencia completa para que el oficial pueda contradecir al agente. El sujeto no recibe un rechazo automático — recibe revisión humana. |
| **Costo por consulta de medios** | Si el modelo hace búsquedas extensas por sujeto, el costo sube | Cap de 5 búsquedas de noticias por sujeto; si ninguna es relevante, se reporta "no adverse media encontrado" sin más iteraciones. |

---

## 11. Variantes por industria

| Delta | Servicios financieros (Coop. Popular) | Salud (Clínica San Rafael) |
|-------|---------------------------------------|---------------------------|
| Marco regulatorio | SARLAFT/SAGRILAFT, Circular Básica Jurídica SFC | Resolución 3280/2018 Minsalud, Código de Ética Médica |
| Listas adicionales | UIAF (reportes), listas PEP colombianas (DNI) | RETHUS (habilitación profesional), inhabilitados MEN |
| Sujeto típico | Persona que abre cuenta / solicita crédito | Proveedor de suministros médicos, médico contratista |
| Frecuencia | Alta (10–100/mes) | Baja-media (5–30/mes, picos en licitaciones) |
| Escalación | Oficial de cumplimiento SARLAFT | Dirección Jurídica + Jefe de Compras |
| Precio tier profesional | 800–1 200 USD/mes (volumen + regulación dura) | 400–700 USD/mes (menor volumen, regulación diferente) |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **B02** — FastAPI routers y deps | Endpoint `POST /kyc/check` con autenticación por `tenant_id`; rate limiting por tenant para controlar costos. |
| **C03** — Multitenancy | Tabla `kyc_reviews` con `tenant_id` en cada fila; RLS para que cada cooperativa solo vea sus expedientes. |
| **D04** — Observabilidad Phoenix | Traza completa por expediente: span por cada lista verificada, span de LLM para desambiguación, costo total por consulta. Alerta si costo > 1 USD/sujeto. |
| **E01** — Anthropic SDK tool loop | El loop de desambiguación y adverse media: el modelo itera llamando `search_sanction_list` y `search_news` hasta tener suficiente evidencia o alcanzar el límite de iteraciones. |
| **E05** — Temporal | Workflow durable para el proceso KYC: si la API de Truora cae, el workflow reinicia desde el último checkpoint sin re-verificar listas ya chequeadas. |

## 13. Errores típicos

**1. El agente aprueba o rechaza al sujeto directamente sin escalar al oficial de cumplimiento.**
*Síntoma*: se configura el workflow para que si `risk_score == LOW` y no hay hits en listas, el sistema marque automáticamente al sujeto como «aprobado» y avance el proceso de apertura de cuenta sin intervención humana.
*Causa raíz*: el agente no reemplaza al oficial de cumplimiento. La decisión de KYC/AML es una responsabilidad regulatoria personal del oficial; delegarla al sistema implica que el oficial asume responsabilidad sin haber ejercido el juicio.
*Cómo evitarlo*: el nodo `ESCALATION GATE` es no-negociable y no tiene bypass. El expediente siempre llega al oficial con el resultado del análisis; el oficial hace clic en «aprobar», «rechazar» o «solicitar más información». El sistema nunca avanza el proceso sin esa acción humana explícita.

**2. Dependencia ciega del LLM para desambiguar hits en listas sin revisar la evidencia.**
*Síntoma*: el modelo dice «false_positive» para un hit de OFAC con confianza 0.78 y el oficial acepta el resultado sin leer el expediente; el sujeto es en realidad la misma persona con alias diferente.
*Causa raíz*: el oficial confía en la clasificación del modelo porque tiene alta confianza, pero «confianza» mide coherencia del razonamiento del modelo, no certeza factual sobre el mundo real.
*Cómo evitarlo*: cualquier hit en lista, independientemente de la clasificación del modelo, llega al oficial con la evidencia completa (campos del listado, foto si está disponible, descripción del entry). El oficial revisa la evidencia, no solo la clasificación. Los hits nunca se descartan sin revisión humana.

**3. Lista de sanciones desactualizada por fallo en la descarga automática.**
*Síntoma*: la lista OFAC SDN lleva 5 días sin actualizarse porque el job de descarga falló silenciosamente; un sujeto añadido a la lista ayer pasa el check sin hits.
*Causa raíz*: el job de descarga de listas no tiene alerta de fallo; el pipeline no verifica la fecha de la lista antes de correr la búsqueda.
*Cómo evitarlo*: antes de cualquier búsqueda, validar que `list_date >= today - 1 day` para OFAC (descarga diaria) y `list_date >= today - 7 days` para ONU. Si la lista está desactualizada, el pipeline se detiene y alerta al administrador; no hace la búsqueda con datos viejos.

**4. PII de sujetos consultados en logs de trazas accesibles a múltiples tenants.**
*Síntoma*: el nombre y número de documento de un sujeto de Coop. Popular aparece en un span de Phoenix visible para otro tenant por un error de configuración del `tenant_id` en la traza.
*Causa raíz*: los spans del nodo `DISAMBIGUATE_HITS` incluyen el perfil completo del sujeto sin filtrar por tenant.
*Cómo evitarlo*: los spans de Phoenix solo persisten `{kyc_review_id, tenant_id, lists_checked, has_hits, risk_score, cost_usd}`; ningún dato del sujeto sale de la tabla `kyc_reviews` con RLS. Los datos del sujeto son datos personales bajo Ley 1581 (Colombia) y LGPD; su exposición no intencional es una violación notificable.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué la desambiguación de hits en listas de sanción no puede resolverse solo con un threshold de similitud de nombres (Jaro-Winkler), con un ejemplo real de un nombre hispano frecuente donde la regla sola falla.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si debo verificar a personas jurídicas (empresas) en lugar de personas naturales, donde el riesgo de lavado puede estar en el beneficiario final (UBO) y no en el representante legal.»
3. **Por qué falló**: «El expediente KYC del sujeto CC-12345678 fue aprobado preliminarmente, pero la Superfinanciera encontró un hit activo en una lista regional que el pipeline no chequeó. ¿Qué faltó en la configuración del `keyword_profile` o del `search_sanction_list` tool?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline KYC/AML con separación correcta de checks determinísticos (listas, RUT) y análisis agénticos (desambiguación, adverse media), garantizando que la decisión final siempre es humana.
- Implementar la validación de frescura de listas antes de cada búsqueda para evitar falsos negativos por datos desactualizados.
- Configurar el `ESCALATION GATE` como nodo no-bypasseable en LangGraph para cualquier hit probable o adverse media preocupante.
- Evaluar el costo por consulta y dimensionar el tier correcto según el volumen de verificaciones mensuales del tenant.
- Identificar los requisitos de retención y protección de datos de sujetos bajo Ley 1581 (Colombia), SAGRILAFT y normativa equivalente en cada país.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK tool loop | El loop de desambiguación y adverse media: el modelo itera llamando `search_sanction_list` y `search_news` hasta tener suficiente evidencia; sin E01, el estudiante no implementa el límite de iteraciones correctamente. |
| **E05** — Temporal + idempotencia | Si la API de Truora cae a mitad del proceso, Temporal retoma desde el último checkpoint sin re-verificar listas ya chequeadas; E05 enseña este patrón de workflow durable. |
| **D04** — Observabilidad y trazas auditables | La traza completa por expediente (span por lista, span de LLM, costo total) es la evidencia que la Superfinanciera puede pedir en una auditoría; D04 enseña a construir estas trazas de forma que sean auditables y no expongan PII. |
| **C03** — Multitenancy | La tabla `kyc_reviews` con RLS por `tenant_id` garantiza que cada cooperativa solo vea sus expedientes; sin C03, el estudiante no implementa el aislamiento correcto. |
