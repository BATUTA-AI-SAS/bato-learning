---
ext_id: F-RH-02
slug: analisis-enps
track: F
dept: RH
ord: 221
title: "Análisis de encuestas eNPS y clima organizacional"
summary: "Pipeline que calcula el score numérico, segmenta por área y antigüedad, y extrae temas accionables de comentarios abiertos sin exponer identidades."
related_modules: [A06, C01, E01]
industries_instanced: [salud, manufactura]
tenants_in_examples: [sanrafael, acme]
big_corp_vendors: [Culture Amp, Qualtrics EX, Workday Peakon]
latam_tools: [google-forms, typeform, sharepoint]
key_concepts: [eNPS, comentarios-abiertos, anonimato, drivers-de-engagement, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

La directora de RRHH de **Clínica San Rafael** lanza una encuesta de clima cada semestre con Google Forms. Recibe 210 respuestas: un score numérico y un campo de texto libre donde el personal escribe lo que realmente piensa. Hoy procesa los números con una tabla dinámica de Excel en 2 horas, pero los 210 comentarios abiertos los lee uno por uno y produce un resumen subjetivo de 3 párrafos que llega al comité dos semanas después. El análisis llega tarde, pierde señales débiles («el jefe de urgencias tiene favoritismo» aparece en 4 comentarios dispersos), y los accionables son vagos («mejorar la comunicación interna»).

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Culture Amp** | Encuestas de engagement + benchmarking de 6000+ empresas + análisis temático con IA | 5–8 USD/empleado/mes; mínimo ~15 k USD/año |
| **Qualtrics XM (EX)** | Plataforma completa de Employee Experience; NLP sobre texto libre; dashboards por manager | 10–30 USD/empleado/mes; impl. 50–300 k USD |
| **Workday Peakon** | eNPS continuo integrado en Workday HCM; análisis de drivers automático | incluido en Workday; HRIS desde 6–15 USD/empleado/mes |

En 2026, Culture Amp entrega análisis de drivers de engagement como accionables inmediatos al cierre de la encuesta. Qualtrics tiene análisis de sentimiento multi-idioma incluyendo español latinoamericano. Fuera del alcance económico de una PYME de 200 personas.

---

## 3. PYME LATAM realista

**Clínica San Rafael** (salud privada, 210 empleados) y **ACME Manufacturing** (manufactura, ~400 empleados planta + administrativos) operan con:

- **Google Forms** o **Typeform** gratuito: formulario con la pregunta eNPS (0–10) + campos de texto libre (2–3 preguntas abiertas) + área y antigüedad.
- Respuestas exportadas como **CSV** o descargadas desde Google Sheets.
- Análisis en **Excel**: tabla dinámica para el score; lectura manual para los textos.
- RRHH no tiene analista de datos; el análisis lo hace la misma persona que lanzó la encuesta.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Score eNPS (0–10) | Entero | Google Forms CSV | Semestral o trimestral | 50–500 filas |
| Comentario abierto 1 («¿Qué mejorarías?») | Texto libre (10–300 palabras) | Google Forms CSV | Idem | 50–500 filas |
| Comentario abierto 2 («¿Qué valoras?») | Texto libre | Idem | Idem | idem |
| Área / departamento | Categórico | Formulario | Idem | 5–20 categorías |
| Antigüedad | Rango («< 1 año», «1–3», «3+») | Formulario | Idem | 3–5 categorías |

**Ejemplo de fila**:

```
score: 4
area: "Urgencias"
antiguedad: "1-3 años"
q1: "Los turnos rotativos no se comunican con suficiente anticipación. A veces me entero el día anterior."
q2: "El equipo médico es muy bueno y colabora bien."
```

> [!cuidado]
> En encuestas pequeñas (< 10 respuestas por área), la combinación área + antigüedad puede hacer identificable a un empleado específico. El pipeline bloquea el análisis de subgrupos con n < 5.

---

## 5. Tramos determinísticos

1. **Cálculo del score eNPS** — `promotores (9–10) - detractores (0–6)` / total × 100. Fórmula cerrada. Sin LLM.
2. **Segmentación por área y antigüedad** — agrupación SQL/pandas. Score por subgrupo, con flag de «n < 5 → no mostrar» para proteger anonimato.
3. **Distribución de respuestas** — histograma de scores, tasa de respuesta, delta vs periodo anterior. Todo código.
4. **Filtro de contenido explícito** — regex de palabras que indican denuncia grave (acoso, discriminación, accidente) antes de pasar al LLM; esos comentarios se routean directo a un buzón confidencial de RRHH.
5. **Estadísticas descriptivas de longitud de comentario** — correlación entre score bajo y longitud de comentario (a más texto, más crítico: dato útil antes del análisis).

---

## 6. Tramos agénticos

1. **Clasificación temática de comentarios abiertos** — el modelo agrupa comentarios en temas accionables (comunicación interna, carga de trabajo, liderazgo directo, compensación, desarrollo, seguridad). _Por qué no es regla_: la misma queja («los jefes no escuchan») puede pertenecer a «liderazgo», «comunicación» o «cultura» según el contexto del párrafo; no hay regex que distinga.

2. **Detección de señales débiles** — comentarios que individualmente parecen menores pero que, agrupados por área o supervisor, revelan un patrón. _Por qué no es regla_: el patrón emerge del contexto colectivo de varios textos; no es detectable fila a fila.

3. **Redacción del resumen ejecutivo con accionables** — el modelo produce un párrafo por tema con: magnitud (% de comentarios que lo mencionan), ejemplo ilustrativo anonimizado, y acción recomendada con dueño sugerido. _Por qué no es regla_: la redacción debe calibrar el tono para que llegue a un comité directivo sin crear pánico ni minimizar problemas reales; eso exige juicio contextual.

> [!cuidado]
> El modelo nunca ve nombres de empleados. El pipeline elimina cualquier mención de nombre propio antes del análisis agéntico, usando spaCy NER o equivalente. Si un comentario menciona un nombre («el Dr. Ramírez siempre llega tarde»), el nombre se reemplaza por `[NOMBRE]` antes de entrar al LLM.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[load_survey] → lee CSV de Google Forms / Sheets (determinístico, tool: fetch_csv)
  ↓
[compute_enps] → score global + por segmento (determinístico)
  ↓
[filter_comments] → n<5 bloqueados, palabras grave → buzón RRHH (determinístico)
  ↓
[anonymize_names] → NER + replace [NOMBRE] (determinístico)
  ↓
[classify_themes] → agrupa comentarios por tema (agéntico)
  ↓
[detect_weak_signals] → patrones por área/supervisor (agéntico)
  ↓
[draft_executive] → resumen con accionables (agéntico, tool: sql_query histórico)
  ↓
[human_review?] → interrupt_before si señales de denuncia grave detectadas
  ↓
[write_report] → reporte PDF con scores + temas + accionables (tool: write_report)
  ↓
[send_email] → a directora RRHH + comité (tool: send_email)
  ↓
END
```

### Activities Temporal

- `load_survey_csv(tenant, survey_id)` — descarga el CSV; idempotente.
- `run_analysis_agent(tenant, survey_id)` — corre el grafo.
- `archive_raw_comments(tenant, survey_id)` — guarda los comentarios crudos en storage cifrado; no en la DB principal.

### Tools necesarias

- `fetch_csv` — CSV de Google Forms.
- `sql_query` — scores históricos del tenant para delta vs anterior.
- `write_report` — PDF ejecutivo + CSV de temas por área.
- `send_email` — distribución del reporte.

---

## 8. Salida y entrega

**Reporte ejecutivo** (extracto):

```
## Análisis eNPS — Clínica San Rafael · Semestre 1-2026

**Score global: +18** (promotores 42%, pasivos 34%, detractores 24%)
Delta vs S2-2025: +4 puntos. Tasa de respuesta: 87%.

### Por área
| Área        | eNPS | n   | Alerta |
|-------------|------|-----|--------|
| Urgencias   | -12  | 38  | ⚠ bajo |
| Quirófano   | +31  | 29  | —      |
| Admin.      | +22  | 41  | —      |

### Temas principales (de comentarios abiertos)
1. **Comunicación de turnos** (34% de comentarios) — Urgencias y Hospitalización.
   Ejemplo: "A veces me entero del cambio de turno el día anterior."
   Acción sugerida: publicar cuadros de turno con 7 días de anticipación. Dueño: Jefatura Operaciones.

2. **Carga de trabajo en picos** (22%) — Urgencias exclusivamente.
   Señal débil detectada: 6 comentarios de Urgencias mencionan al supervisor de turno nocturno.
   → Requiere revisión por RRHH antes de compartir con el área.
...

⚠ Los comentarios individuales no se distribuyen. Este reporte agrega sin identificar.
```

---

## 9. Cómo se vende

**Gancho**: «Tu encuesta de clima ya existe. Solo falta convertir los comentarios en accionables en minutos, no en semanas».

**Propuesta de valor**: velocidad (análisis listo en < 2 horas del cierre de encuesta), detección de señales débiles que el análisis manual pierde, y trazabilidad (cada accionable tiene el % de comentarios que lo respalda).

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | 1 encuesta/semestre, ≤ 300 respuestas | 200–400 USD/análisis |
| Recurrente | 2–4 encuestas/año + pulsos mensuales | 300–600 USD/mes |
| Setup | Calibración de temas por industria, integración Google Forms | 800–2000 USD |

---

## 10. Riesgos

**1. Re-identificación de empleados.**
*Síntoma*: el reporte muestra el tema «supervisor de turno nocturno en Urgencias» y hay solo 1 supervisor nocturno — el empleado queda expuesto.
*Mitigación*: bloqueo de subgrupos con n < 5; revisión humana de cualquier accionable que mencione un rol específico antes de distribuir. Ley 1581 Colombia y LGPD Brasil exigen consentimiento informado sobre el uso de datos en análisis automatizados.

**2. Sesgo del modelo en clasificación temática.**
*Síntoma*: el modelo clasifica «el comedor está en mal estado» como «cultura» en lugar de «infraestructura».
*Mitigación*: el cliente define y valida el catálogo de temas al configurar; golden set de 20 comentarios etiquetados manualmente que se evalúa después de cada cambio al prompt.

**3. Pérdida de señales de denuncia grave.**
*Síntoma*: un comentario de acoso sexual pasa por el pipeline y llega al reporte ejecutivo en lugar del buzón confidencial.
*Mitigación*: el filtro determinístico de palabras clave corre antes del LLM; lista de términos no configurable por el cliente (hardcoded en el harness). Cualquier match envía el comentario a un endpoint separado y cifrado.

**4. Alucinación de tendencias.**
*Síntoma*: el modelo redacta «la mayoría de empleados menciona problemas de compensación» cuando solo 3 de 200 comentarios lo mencionan.
*Mitigación*: el prompt exige que cada tema incluya `(N comentarios, X% del total)`; el harness verifica que N y X sean calculados por el tramo determinístico, no generados por el modelo.

---

## 11. Variantes por industria

### Instancia 1 — Salud privada (`sanrafael`)

**Datos típicos**: encuesta semestral, 150–300 empleados entre médicos, enfermería y administrativos; alta dispersión de turnos; comentarios en español con terminología clínica.

**Delta determinístico**: segmentación por tipo de contrato (médico planta vs. médico externo vs. enfermería); médicos externos suelen tener menor engagement y distorsionan el score global si se mezclan.

**Delta agéntico**: detectar comentarios sobre protocolos de seguridad del paciente que no son de clima laboral sino de calidad asistencial — routear a un canal diferente (comité médico, no RRHH).

**Regulación**: datos de salud de empleados son sensibles bajo Ley 1581 (Colombia) y la Ley de Protección de Datos (Perú, Chile). El comentario puede contener información de salud de un tercero (paciente) y debe ser manejado con cuidado extra.

**Precio orientativo**: 300–600 USD/análisis semestral; 400–800 USD/mes si incluye pulsos mensuales.

### Instancia 2 — Manufactura (`acme`)

**Datos típicos**: encuesta trimestral, 200–600 empleados entre planta y administrativos; alta proporción de empleados de baja escolaridad en planta que responden en papel o tablet compartida; tasa de respuesta típica 60–75%.

**Delta determinístico**: digitalización de respuestas en papel (cámara + OCR antes de ingresar al pipeline); normalización de respuestas con errores tipográficos o en código de puntuación diferente (escala 1–5 en algunos formularios vs 0–10 en eNPS).

**Delta agéntico**: comentarios de planta suelen ser más directos y concretos («la máquina 3 hace ruido y nadie la arregla»); el modelo debe distinguir entre queja de condiciones físicas (dominio de seguridad) y queja de gestión (dominio de clima). Los temas de seguridad industrial se routean a HSE, no al reporte de clima.

**Regulación**: LFPDPPP México si la planta es en MX; trabajadores en manufactura pueden tener representación sindical — el análisis de clima nunca se comparte con el sindicato sin consentimiento explícito de RRHH y asesoría legal.

**Precio orientativo**: 200–500 USD/análisis trimestral.

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **A06** — Pydantic | El schema `SurveyRow` valida cada fila del CSV (score int 0–10, texto no vacío, área en enum); rechaza filas malformadas antes del pipeline. |
| **C01** — SQLAlchemy async + modelos | Los scores históricos se persisten en la tabla `enps_runs` por tenant; `sql_query` los recupera para calcular el delta período anterior. |
| **E01** — Anthropic SDK | El nodo `classify_themes` usa `cache_control: ttl:"1h"` sobre el catálogo de temas (estático por tenant); los comentarios van sin cache (dinámicos por run). |
| **D04** — Observabilidad | Cada run del pipeline se traza en Phoenix; si el nodo `draft_executive` alucina un porcentaje (detectable por validación cruzada), la traza lo captura para auditoría. |
| **E05** — Temporal | El analysis agent corre como activity dentro de un workflow Temporal programado para dispararse 2 horas después del cierre de la encuesta. |

## 13. Errores típicos

**1. Re-identificación por subgrupo demasiado pequeño.**
*Síntoma*: el reporte muestra un accionable sobre «el supervisor de turno nocturno en Urgencias», y hay exactamente un supervisor en ese turno: el empleado queda expuesto a pesar del anonimato declarado.
*Causa raíz*: el filtro `n < 5` opera sobre el conteo de área, pero no sobre la combinación área + rol específico mencionado en el accionable.
*Cómo evitarlo*: antes de incluir cualquier mención de un rol en el reporte, verificar que `n_empleados_en_ese_rol_y_area >= 5`; si no se cumple, generalizar («en el área de Urgencias») o suprimir el dato.

**2. Sesgo del modelo en clasificación temática hacia temas culturalmente salientes.**
*Síntoma*: en una encuesta de manufactura en México, el modelo clasifica la mayoría de los comentarios como «liderazgo» aunque muchos hablan de condiciones físicas (calor, ruido, ergonomía).
*Causa raíz*: el catálogo de temas predeterminado fue calibrado con datos de industria de servicios y subrepresenta temas de entorno físico.
*Cómo evitarlo*: el cliente define y valida el catálogo de temas al configurar el pipeline; el golden set de calibración debe incluir comentarios representativos del sector específico.

**3. Señal grave que pasa al resumen ejecutivo en lugar del buzón confidencial.**
*Síntoma*: un comentario de acoso sexual llega al reporte de directivos porque la lista de palabras clave del filtro determinístico no cubría la expresión utilizada.
*Causa raíz*: la lista de palabras clave está incompleta o el empleado usó eufemismos.
*Cómo evitarlo*: la lista de términos graves es no-configurable por el cliente y se actualiza centralmente; añadir un segundo pase del LLM exclusivo para detectar «situaciones que requieren atención urgente de RRHH» sobre los comentarios que pasaron el filtro de palabras.

**4. Alucinación de porcentajes en el resumen ejecutivo.**
*Síntoma*: el modelo redacta «la mayoría de los empleados de Urgencias menciona problemas de carga de trabajo» cuando solo 4 de 38 comentarios lo hacen.
*Causa raíz*: el modelo genera el porcentaje sin anclarlo al conteo calculado en el tramo determinístico.
*Cómo evitarlo*: el prompt exige que cada afirmación cuantitativa cite `(N comentarios, X%)` calculados por el pipeline, no generados por el modelo; el harness valida que los números en el texto del resumen coincidan con la tabla de conteos.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Por qué la clasificación temática de comentarios abiertos es agéntica y el cálculo del score eNPS es determinístico? Explícamelo con un ejemplo concreto del sector salud.»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si la encuesta se hace en papel y los comentarios se digitalizan con OCR de baja calidad?»
3. **Por qué falló**: «El modelo clasificó como 'cultura' un comentario que claramente es sobre infraestructura. ¿Cómo lo detecto en el golden set y cómo corrijo el prompt sin romper la clasificación de los otros temas?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de análisis eNPS desde la ingesta del CSV hasta el reporte ejecutivo con accionables, diferenciando los tramos determinísticos de los agénticos.
- Implementar el bloqueo de subgrupos con `n < 5` y la anonimización de nombres propios antes de cualquier llamada al LLM.
- Configurar el filtro de contenido explícito (acoso, discriminación) para routear comentarios graves a un buzón confidencial separado, antes del análisis temático.
- Validar que los porcentajes en el resumen ejecutivo provienen del tramo determinístico, no del modelo.
- Dimensionar y cotizar este servicio para una clínica o una planta de manufactura.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **C02** — Multitenancy y RLS | Los comentarios de clima organizacional son datos laborales sensibles: sin RLS, una empresa podría acceder a las respuestas de otra. Esta ficha asume que `tenant_id` filtra todas las consultas a la tabla `enps_runs`. |
| **C01** — SQLAlchemy async | Los scores históricos se persisten en la tabla `enps_runs` por tenant; entender el patrón de repositorio async es prerequisito para implementar el delta vs período anterior. |
| **E01** — Anthropic SDK | El nodo `classify_themes` usa `cache_control` sobre el catálogo de temas (estático por tenant); sin entender el caching del SDK, el costo por encuesta crece innecesariamente. |
| **D04** — Observabilidad | Detectar alucinaciones de porcentajes requiere validación cruzada entre el texto generado y los conteos calculados; las trazas en Phoenix permiten auditar ese cruce. |
