---
ext_id: F-RH-04
slug: analisis-turnover
track: F
dept: RH
ord: 223
title: "Análisis de turnover y detección de banderas tempranas"
summary: "Pipeline que calcula tasas de rotación por cohorte, estima el costo de reposición, y detecta señales tempranas de salida en datos operativos y cualitativos."
related_modules: [A06, C01, D04, E01]
industries_instanced: [hospitalidad, logistica]
tenants_in_examples: [mesonurbano, expreslog]
big_corp_vendors: [Visier, Workday Prism, Eightfold AI]
latam_tools: [excel, looker-studio]
key_concepts: [turnover-voluntario, cohort, leading-indicators, costo-de-reposicion, fallback-humano]
estimated_minutes: 45
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

El gerente de operaciones de **Logística Express** pierde en promedio 3 conductores al mes sobre una flota de 40. No lo sabe hasta que alguien renuncia el viernes por la tarde para el lunes. El costo de reposición (reclutamiento + selección + entrenamiento + 4 semanas de productividad reducida) ronda los 2000–3500 USD por conductor. En un año, el problema le cuesta 70–100 k USD y él no tiene el dato claro porque está en tres hojas de Excel distintas y ninguna le dice «este empleado tiene riesgo alto de irse en 60 días». Las señales estaban ahí —ausentismo creciente, rendimiento variable en las últimas rutas, cero participación en la última encuesta de clima— pero nadie las leyó juntas.

---

## 2. Hoy en big corps

| Vendor | Qué hace | Precio orientativo |
|--------|----------|--------------------|
| **Visier** | People analytics completo: turnover, diversidad, compensation equity, predictive attrition | 15–40 USD/empleado/mes; impl. 50–200 k USD |
| **Workday Prism Analytics** | Combina datos de Workday HCM con fuentes externas; dashboards y predicción de attrition | Incluido en tier avanzado de Workday; impl. adicional |
| **Eightfold AI** | Talent intelligence: predict flight risk basado en perfil profesional + señales de mercado laboral | 150–400 k USD/año enterprise |

Estas plataformas requieren que todos los datos de RRHH estén en un sistema estructurado y limpio. Para una PYME con datos dispersos en Excel, el prerequisito de migración de datos hace la implementación inviable sin un proyecto de 6 meses.

---

## 3. PYME LATAM realista

**Mesón Urbano** (F&B, 80 empleados, alta rotación en cocina y servicio) y **Logística Express** (transporte/3PL, 95 empleados operativos) operan con:

- **Nómina en Siigo o Aspel**: tiene fechas de entrada/salida, cargo, salario. Exportable en CSV pero sin historial de cambios limpio.
- **Marcación de asistencia** en reloj biométrico o app: exportable diario/semanal, sin análisis.
- **Google Sheets** para KPIs operativos (rutas completadas, pedidos procesados) que nadie cruza con los datos de RRHH.
- **Encuesta eNPS** semestral (si la hacen): analizada separado, nunca cruzada con turnover.
- Zero data engineer. Los datos los procesa la misma persona que maneja la nómina.

---

## 4. Datos típicos

| Campo | Formato | Fuente | Frecuencia | Volumen |
|-------|---------|--------|------------|---------|
| Historial de empleados | CSV (entrada, salida, cargo, área, salario) | Siigo / Aspel / nómina | Mensual | 1 fila/empleado, histórico desde inicio |
| Marcación de asistencia | CSV (empleado_id, fecha, hora_entrada, hora_salida, ausencias) | Reloj biométrico | Diario | ~100 filas/día |
| KPIs operativos | CSV / Sheets (rutas completadas, errores, incidentes) | ERP operativo | Semanal | 1 fila/empleado/semana |
| Notas de 1:1 / evaluaciones | Texto libre (DOCX, Notion, notas en nómina) | Managers | Ad hoc | 0–5 por empleado/mes |
| eNPS por empleado (anonimizado) | Score + área | Pipeline F-RH-02 | Semestral | 1 fila/empleado |

**Ejemplo de registro de empleado**:

```json
{
  "employee_id": "EXP-0091",
  "hire_date": "2023-11-14",
  "role": "conductor",
  "area": "distribución_norte",
  "salary_band": "B2",
  "absences_last_30d": 3,
  "routes_completed_last_4w": [41, 38, 29, 22],
  "enps_score_last": 5,
  "enps_delta": -3,
  "manager_notes_last_60d": "Llegó tarde dos veces esta semana. Dijo que tiene problemas de transporte."
}
```

---

## 5. Tramos determinísticos

1. **Cálculo de tasa de turnover** — `salidas_voluntarias / headcount_promedio` por período, por área, por rol. Sin LLM. Distingue entre voluntario (renuncia) e involuntario (despido, fin de contrato) según la causa de salida registrada en nómina.
2. **Cálculo de costo de reposición estimado** — `(días_vacante × costo_día_productividad) + costo_reclutamiento_promedio_por_rol + (semanas_rampa × salario_diario × factor_productividad)`. Configurado por rol en el tenant.
3. **Cohorte analysis** — agrupa empleados por período de ingreso (Q1-2024, Q2-2024…) y calcula la curva de supervivencia por cohorte. Identifica si hay cohortes con retención sistémicamente peor.
4. **Features de riesgo estructurado** — calcula features determinísticas por empleado: `tenure_meses`, `ausencias_últimos_30d`, `delta_kpi_4_semanas` (tendencia del KPI operativo), `delta_enps`, `días_sin_feedback`. Estas features alimentan el tramo agéntico pero no son el modelo — son datos.
5. **Ranking de riesgo por regla** — empleados con `ausencias > umbral AND delta_kpi < -20%` se marcan como `riesgo_alto_determinístico` sin necesidad del LLM. Umbral configurable por tenant.

---

## 6. Tramos agénticos

1. **Lectura de notas de 1:1 y evaluaciones de desempeño** — el modelo lee el texto de las notas del manager y detecta cambios de tono, señales implícitas de desenganche («pidió menos proyectos», «mencionó que está buscando opciones», «llegó tarde pero no explicó»). _Por qué no es regla_: las señales de desenganche en texto son implícitas y contextuales; no hay regex que identifique «está buscando opciones» de «está pensando en opciones para el proyecto».

2. **Síntesis de señales múltiples en un perfil de riesgo** — el modelo combina las features determinísticas con las señales cualitativas para producir una evaluación narrativa de por qué un empleado tiene riesgo elevado. _Por qué no es regla_: la combinación de «ausencias moderadas + delta_kpi neutro + nota de 1:1 con tono de cierre» puede ser más señal que cada factor solo; el peso relativo depende del contexto del rol.

3. **Recomendación de acción por empleado en riesgo** — el modelo sugiere una acción concreta para cada empleado marcado como riesgo (conversación de carrera, ajuste de compensación, reasignación de ruta, etc.). _Por qué no es regla_: la acción correcta depende de la razón inferred, el historial del empleado, y las palancas disponibles del manager — no hay una tabla de acción por combinación de factores.

> [!cuidado]
> El agente **nunca recomienda despedir** a un empleado. La sección de «acción recomendada» solo contiene acciones de retención. Si el análisis indica riesgo de bajo desempeño que requiere medidas disciplinarias, el sistema redirige a RRHH con un flag específico.

---

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[load_data] → CSV nómina + asistencia + KPIs (determinístico, tools: fetch_csv, fetch_excel)
  ↓
[compute_metrics] → turnover rate + costo reposición + cohortes (determinístico)
  ↓
[compute_features] → features por empleado (determinístico, tool: sql_query)
  ↓
[rule_based_risk] → riesgo alto por umbrales fijos (determinístico)
  ↓
[load_qualitative] → notas de 1:1 y evaluaciones (determinístico, tool: fetch_excel)
  ↓
[analyze_signals] → señales en texto por empleado (agéntico)
  ↓
[synthesize_risk] → perfil de riesgo narrativo por empleado (agéntico)
  ↓
[recommend_actions] → acción concreta por empleado en riesgo (agéntico)
  ↓
[human_review?] → interrupt_before: RRHH valida la lista de riesgo alto
  ↓
[write_report] → reporte mensual de turnover + lista de riesgo (tool: write_report)
  ↓
[send_email] → a gerencia RRHH + managers relevantes (tool: send_email)
  ↓
END
```

### Activities Temporal

- `load_hr_data(tenant, period)` — carga datos de nómina y asistencia; idempotente por `period`.
- `run_turnover_agent(tenant, period)` — corre el grafo; actividad con timeout 10 min.
- `persist_risk_scores(tenant, period, scores)` — guarda scores con `idempotency_key = "turnover:{tenant}:{period}"`.
- Schedule: primer día hábil de cada mes para el período anterior.

### Tools necesarias

- `fetch_csv` — datos de asistencia y KPIs operativos.
- `fetch_excel` — notas de 1:1 si están en Sheets.
- `sql_query` — historial de empleados y scores anteriores del tenant.
- `write_report` — reporte PDF/MD mensual.
- `send_email` — distribución a gerencia.

---

## 8. Salida y entrega

**Reporte mensual de turnover** (extracto):

```
## Turnover — Logística Express · Abril 2026

**Tasa de turnover voluntario: 8.3%** (3/36 conductores; promedio industria LATAM 3PL: ~5%)
Costo estimado período: 9,600 USD (3 reposiciones × 3,200 USD promedio).
Acumulado 2026: 24,800 USD.

### Cohortes con mayor riesgo
| Cohorte ingreso | Headcount inicial | % retenido a 12 meses |
|-----------------|-------------------|-----------------------|
| Q3-2024         | 12                | 58%                   |
| Q4-2024         | 9                 | 78%                   |

→ Cohorte Q3-2024: deserción 2× mayor al promedio. Contexto: ingresaron durante expansión de rutas; manager cambiado dos veces.

### Empleados con riesgo alto (requieren acción esta semana)
| ID       | Señales determinísticas           | Señal cualitativa                          | Acción sugerida |
|----------|-----------------------------------|--------------------------------------------|-----------------|
| EXP-0091 | Ausencias +3, KPI -37% en 4 sem  | Notas: menciona «otras opciones» 2 veces  | Conversación 1:1 + revisar ruta asignada |
| EXP-0047 | eNPS cayó de 8 a 3 en 6 meses    | Sin notas de 1:1 en 60 días               | Feedback urgente; manager no tiene visibilidad |

⚠ Este análisis es una señal, no una evaluación de desempeño. La acción la decide el manager con RRHH.
```

---

## 9. Cómo se vende

**Gancho**: «Cada conductor que se va te cuesta 3000 USD y 4 semanas de desorden. Nosotros te decimos quién tiene riesgo de irse antes de que renuncie».

**Propuesta de valor**: anticipación (señales 30–60 días antes de la renuncia), cuantificación del costo real de turnover (el gerente lo ve en USD), y acciones concretas en lugar de dashboards decorativos.

| Tier | Condiciones | Precio |
|------|-------------|--------|
| Starter | Análisis mensual, ≤ 100 empleados, solo datos estructurados | 250–500 USD/mes |
| Growth | Análisis mensual + notas cualitativas, ≤ 300 empleados | 500–900 USD/mes |
| Setup | Integración Siigo/Aspel + calibración umbrales por rol | 1500–4000 USD |

---

## 10. Riesgos

**1. PII de empleados en el análisis agéntico.**
*Síntoma*: el modelo recibe notas de 1:1 con nombre, cargo y salario del empleado y los incluye en el reporte distribuido a managers.
*Mitigación*: las notas se anonimiza con `employee_id` antes de entrar al LLM; el reporte final mapea IDs a nombres solo en la capa de presentación, con acceso restringido por rol. Ley 1581 (Colombia) y LGPD (Brasil): el empleado tiene derecho a saber que su desempeño se analiza con herramientas automatizadas.

**2. Discriminación indirecta por features de riesgo.**
*Síntoma*: empleadas con permisos de maternidad acumulan «ausencias» y aparecen en la lista de riesgo alto por un algoritmo que no distingue ausencia protegida de ausencia injustificada.
*Mitigación*: el cálculo de features excluye ausencias legalmente protegidas (maternidad, paternidad, incapacidad médica, permisos sindicales). Estos tipos se etiquetan en la exportación de Siigo/Aspel; el pipeline los filtra antes del cálculo.

**3. Alucinación de señales en notas vacías.**
*Síntoma*: para un empleado sin notas de 1:1, el modelo inventa señales de desenganche basándose solo en los features numéricos.
*Mitigación*: si el campo de notas está vacío, el nodo `analyze_signals` devuelve `signal: null` y el modelo no recibe el bloque de notas. La ausencia de notas es en sí una señal (manager sin visibilidad), que se reporta como tal.

**4. Falsos positivos que dañan la relación con el empleado.**
*Síntoma*: RRHH llama a un empleado para «verificar su compromiso» basándose en el análisis, y el empleado — que estaba perfectamente bien — se preocupa y empieza a buscar trabajo.
*Mitigación*: la lista de riesgo se entrega a RRHH con la instrucción explícita de que las acciones recomendadas son «abrir una conversación natural», no confrontar con el análisis. El reporte no se distribuye directamente a managers sin filtro de RRHH.

**5. Datos de nómina mal etiquetados.**
*Síntoma*: salidas involuntarias (despidos) se clasifican como renuncias en el CSV de Siigo, inflando el turnover voluntario.
*Mitigación*: el pipeline solicita que el tenant etiquete la causa de salida en el CSV de exportación (`type: voluntary | involuntary | end_contract`). Si el campo está vacío, el análisis lo marca como `unknown` y alerta a RRHH para corregir.

---

## 11. Variantes por industria

### Instancia 1 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: turnover voluntario 40–80% anual (norma en el sector); 80% de empleados en roles operativos (cocina, servicio); contratos a tiempo parcial frecuentes; datos de nómina en Siigo o planilla manual.

**Delta determinístico**: la tasa de turnover «normal» del sector hace que el umbral de alerta sea muy diferente al de otros sectores; el sistema se calibra con benchmarks de F&B LATAM, no con el promedio general. Además, la rotación estacional (alta en diciembre, baja en febrero) debe separarse del turnover estructural.

**Delta agéntico**: en F&B, los comentarios de los empleados suelen ser verbales y el manager los anota (o no). El agente detecta patrones en la ausencia de notas: si un empleado operativo nunca tiene notas de 1:1, es porque nunca se hacen 1:1s, no porque no hay señales. Esto se reporta como riesgo de gestión, no de empleado.

**Regulación**: trabajadores de restauración en Colombia o México pueden tener sindicato o representación colectiva; cualquier análisis de riesgo individual debe manejarse con asesoría legal antes de tomar acción.

**Precio orientativo**: 200–450 USD/mes (volumen de empleados moderado, datos más simples).

### Instancia 2 — Logística / 3PL (`expreslog`)

**Datos típicos**: conductores y operadores de bodega; KPIs operativos ricos (rutas, tiempos, incidentes, combustible); marcación biométrica estricta; nómina en Aspel o Contpaq.

**Delta determinístico**: los KPIs operativos son predictores más potentes que en otros sectores; una caída de > 15% en rutas completadas en 4 semanas tiene alta correlación con renuncia en los siguientes 45 días (calibrar con datos históricos del tenant). El análisis de cohortes por temporada de contratación (pico navideño vs. resto del año) revela patrones de retención distintos.

**Delta agéntico**: notas de 1:1 de conductores suelen ser escasas; el agente usa los registros de incidentes de tránsito y las comunicaciones de despacho (si están disponibles en texto) como señales cualitativas alternativas. Detectar cambios de patrón («antes reportaba cualquier problema, ahora no reporta nada») es más agéntico que contar incidentes.

**Regulación**: conductores en México están bajo la NOM-087 de fatiga; en Colombia bajo el Decreto 1072 de seguridad vial. Los datos de KPI de ruta pueden cruzarse con regulación de seguridad, no solo con RRHH.

**Precio orientativo**: 400–800 USD/mes (datos más ricos, integración con ERP operativo).

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de él |
|--------|-----------------|
| **A06** — Pydantic + tipos | Los schemas `EmployeeRecord`, `AttendanceRow`, `OperationalKPI` validan cada fuente de datos antes del pipeline; si Siigo exporta un campo con tipo inesperado, el validador lo rechaza con error claro. |
| **C01** — SQLAlchemy async | La tabla `turnover_scores` persiste los features y scores por período; `sql_query` los recupera para comparar con períodos anteriores y calcular deltas. |
| **D04** — Observabilidad | Cada run del pipeline se traza en Phoenix; si el nodo `analyze_signals` genera una respuesta sin ningún fragmento de nota de empleado (posible alucinación), la traza lo detecta y alerta. |
| **E01** — Anthropic SDK | El nodo `synthesize_risk` usa `cache_control: ttl:"1h"` sobre el system prompt con el contexto de la empresa y los umbrales configurados (estáticos); los features dinámicos por empleado van sin cache. |
| **E05** — Temporal | El workflow de turnover mensual corre como schedule en Temporal: primer día hábil del mes, con retry policy en `load_hr_data` (la exportación de Siigo a veces falla en horario pico). |

## 13. Errores típicos

**1. Ausencias protegidas contabilizadas como señal de riesgo.**
*Síntoma*: una empleada en permiso de maternidad aparece en la lista de riesgo alto porque acumuló 20 días de ausencia en el último mes.
*Causa raíz*: el cálculo de `ausencias_últimos_30d` no excluye las ausencias legalmente protegidas etiquetadas en Siigo/Aspel.
*Cómo evitarlo*: el pipeline filtra explícitamente las causas de ausencia protegidas antes del cálculo de features; si el campo de causa no existe en la exportación, el pipeline interrumpe y pide al tenant que etiquete el CSV antes de continuar.

**2. Salidas involuntarias contadas como turnover voluntario.**
*Síntoma*: el reporte muestra una tasa de rotación voluntaria del 12%, pero la mitad son despidos registrados incorrectamente en Siigo.
*Causa raíz*: el campo `type` de la exportación de nómina está vacío para la mayoría de las salidas.
*Cómo evitarlo*: el pipeline solicita que el tenant etiquete la causa de salida (`voluntary | involuntary | end_contract`); si el campo está vacío en > 20% de las salidas, el análisis se detiene y alerta a RRHH para completar el dato.

**3. Alucinación de señales en notas vacías.**
*Síntoma*: para un empleado sin notas de 1:1, el modelo genera una evaluación narrativa con señales de desenganche que no están respaldadas en ningún texto.
*Causa raíz*: el nodo `analyze_signals` recibió el perfil del empleado con los features numéricos pero el campo de notas estaba vacío; el modelo llenó el gap con inferencias.
*Cómo evitarlo*: si el campo de notas está vacío, el nodo devuelve `signal: null` y el modelo no recibe el bloque de análisis cualitativo; la ausencia de notas se reporta como «manager sin visibilidad», no como señal de desenganche del empleado.

**4. El agente recomienda acción disciplinaria o de despido.**
*Síntoma*: el nodo `recommend_actions` genera para un empleado de bajo desempeño la sugerencia «evaluar continuidad en el cargo».
*Causa raíz*: el prompt no restringe explícitamente las acciones recomendadas a acciones de retención.
*Cómo evitarlo*: el prompt especifica que la sección de acciones solo puede contener retención (conversación, ajuste de ruta, revisión de compensación, feedback); cualquier output que contenga lenguaje de desvinculación es filtrado por el harness y redirigido a RRHH con un flag específico. El agente nunca recomienda despedir ni evaluar la continuidad de un empleado.

**5. Falso positivo que daña la relación con el empleado.**
*Síntoma*: RRHH confronta a un empleado con el análisis («vimos que tu rendimiento bajó y tus ausencias subieron»), el empleado se preocupa y decide irse.
*Causa raíz*: la lista de riesgo se distribuyó directamente al manager sin filtro de RRHH y sin instrucciones de uso.
*Cómo evitarlo*: el reporte se entrega solo a RRHH con la instrucción explícita de que las acciones son «abrir una conversación natural», no confrontar con el análisis; el reporte no se distribuye a managers sin revisión de RRHH.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «¿Cuál es la diferencia entre el `ranking de riesgo por regla` (determinístico) y la `síntesis de señales múltiples` (agéntica)? Dame un ejemplo con un conductor de Logística Express donde una lleva a una conclusión diferente a la otra.»
2. **Aplícalo a mi caso**: «¿Cómo adaptaría el pipeline si la empresa no tiene ningún registro de notas de 1:1 y los únicos datos disponibles son la marcación de asistencia y los KPIs operativos?»
3. **Por qué falló**: «El reporte del mes pasado marcó como riesgo alto a tres empleados que siguen en la empresa y marcó sin riesgo a uno que renunció la semana siguiente. ¿Qué features debo revisar primero?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de análisis de turnover desde la ingesta de datos de nómina, asistencia y KPIs hasta el reporte mensual con lista de empleados en riesgo.
- Separar los tramos determinísticos (cálculo de tasas, cohortes, features de riesgo) de los agénticos (lectura de notas, síntesis de señales, recomendación de acción).
- Implementar el filtro de ausencias protegidas y el bloqueo de acciones disciplinarias en el prompt y en el harness.
- Configurar el pipeline para que el reporte llegue exclusivamente a RRHH, no directamente a managers, con instrucciones de uso explícitas.
- Dimensionar y cotizar este servicio para F&B con alta rotación y para logística con KPIs operativos ricos.

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|--------------------------------|
| **C02** — Multitenancy y RLS | Los datos de nómina, asistencia y notas de 1:1 son los datos más sensibles del tenant; sin RLS bien implementado, el riesgo de exposición cruzada entre empresas es crítico. |
| **C01** — SQLAlchemy async | La tabla `turnover_scores` persiste features y scores por período; entender el repositorio async es prerequisito para implementar el delta vs período anterior y la comparación de cohortes. |
| **A06** — Pydantic + tipos | Los schemas `EmployeeRecord` y `AttendanceRow` validan cada fuente de datos antes del pipeline; sin validación estricta, un campo de tipo inesperado en la exportación de Siigo puede silenciar errores de cálculo. |
| **D04** — Observabilidad | Detectar alucinaciones en el nodo `analyze_signals` (respuestas sin fragmento de nota real) requiere trazas en Phoenix; sin observabilidad no hay forma de auditar la calidad de las señales cualitativas. |
