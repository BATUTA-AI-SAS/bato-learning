---
ext_id: F-OPS-04
slug: capacidad-staffing
track: F
dept: OPS
ord: 164
title: "Planeación de capacidad y staffing (turnos, picos)"
summary: "Calcula FTE necesario por turno con ratio de servicio declarado y restricciones laborales; el agente propone ajustes ante eventos no-recurrentes y redacta la comunicación al equipo."
related_modules: [B02, C01, E01, E05]
industries_instanced: [logistica, hospitalidad]
tenants_in_examples: [expreslog, mesonurbano]
big_corp_vendors: [Kronos / UKG, Quinyx, Workday Scheduling]
latam_tools: [excel, alegra-nomina, siigo-nomina]
key_concepts: [FTE, ratio-de-servicio, forecast-tráfico, restricciones-laborales, turno, what-if-staffing]
estimated_minutes: 45
deterministic_share: 0.55
version: 1
---

## 1. Problema operativo

El coordinador de operaciones de Logística Express planifica los turnos semanales de sus 45 operadores de bodega y 12 conductores de last mile. Lo hace en un Excel con las horas proyectadas de llegada de camiones y las rutas del día siguiente, estimando cuántas personas necesita por franja horaria. La semana pasada un cliente grande añadió 200 paquetes extra el miércoles sin aviso; el coordinador no tenía margen en el turno y tuvo que llamar a 3 personas en su día libre. Mesón Urbano tiene el mismo problema: el jefe de sala planifica el personal de servicio para la semana, pero el viernes llegó un grupo de 30 personas que no reservó. El costo: horas extra no presupuestadas y servicio degradado.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **Kronos / UKG Pro Workforce Management** | Forecast de demanda de trabajo, scheduling automático respetando sindicatos y legislación laboral, time & attendance integrado | 6–22 USD/empleado/mes; impl. 50k–200k USD |
| **Quinyx** | WFM cloud, forecast de tráfico desde POS/historiales, scheduling automático con optimización, app móvil del empleado | 4–15 USD/empleado/mes |
| **Workday Scheduling** | Integrado con Workday HCM, scheduling predictivo, gestión de disponibilidad, compliance laboral | Dentro del bundle Workday, 30–100 USD/empleado/mes |

El modelo big corp: forecast de tráfico automático desde el POS o el WMS, scheduling optimizado considerando legislación laboral, sindicatos, preferencias del empleado. PYME tiene un Excel y la memoria del coordinador.

## 3. PYME LATAM realista

Expreslog usa Alegra Nómina para pagar pero no para planificar turnos; los turnos están en un Excel compartido en WhatsApp. La legislación laboral colombiana (o mexicana, o peruana) impone restricciones que el coordinador conoce de memoria pero no tiene sistematizadas: máximo 8 horas por turno sin horas extra, descanso de 1 hora, máximo 2 horas extra permitidas, descanso dominical por semana, recargo nocturno a partir de las 9pm. Ninguna herramienta PYME respeta estas reglas automáticamente.

El agente no es un WFM enterprise — es el primer paso: calcular cuántas personas se necesitan, respetando las restricciones legales, y comunicarlo en lenguaje de operaciones.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Forecast de tráfico / demanda de trabajo | Excel del planificador (paquetes/hora para Expreslog, reservas para Mesón) | Semanal | 24–48 franjas horarias × 7 días |
| Roster de empleados disponibles | Excel de RRHH / nómina | Semanal | 10–80 empleados con disponibilidad y contratos |
| Ratio de servicio declarado | Configuración del tenant | Estático | ej: «1 operador por cada 25 paquetes/hora» |
| Restricciones laborales | Configuración del tenant por país | Estático | Colombia / México / Perú — distintas reglas |
| Calendario de eventos especiales | Excel / notas del coordinador | Ad hoc | feriados, eventos, lanzamientos |

**Ejemplo de franja horaria:**

| dia | franja | paquetes_forecast | FTE_necesario | FTE_disponible | gap |
|-----|--------|-------------------|---------------|----------------|-----|
| Lun | 08:00–12:00 | 520 | 21 | 22 | ✓ |
| Mié | 14:00–18:00 | 680 | 28 | 24 | ⚠ Faltantes: 4 |
| Vie | 20:00–00:00 | 890 | 36 | 30 | 🔴 Faltantes: 6 (turno nocturno) |

## 5. Tramos determinísticos

1. **Cálculo de FTE necesario por franja**: `FTE = ceil(tráfico_forecast / ratio_servicio)`. Si el ratio es «1 operador por 25 paquetes/hora» y el forecast dice 520 paquetes/hora, necesitas `ceil(520/25) = 21` operadores. Aritmética pura.
2. **Validación de restricciones laborales**: para cada asignación propuesta, verificar:
   - Horas del turno ≤ 8h (sin declarar HE).
   - Si HE: ≤ 2h adicionales permitidas (configurable por país).
   - Descanso mínimo entre turnos: 11 horas (estándar Colombia/México).
   - Descanso dominical: 1 día/semana garantizado.
   - Recargo nocturno: franja 9pm–6am → flag para cálculo de costo diferencial.
   Todo esto es un check binario por regla. Sin modelo.
3. **Identificación de gaps de cobertura**: comparar `FTE_necesario` vs `FTE_disponible` por franja. Marcar las franjas con déficit, cuantificar el gap.
4. **Cálculo de costo de cobertura**: dado el plan de turnos, calcular `costo_semana = Σ(horas_normales × tarifa_normal) + Σ(HE × tarifa_HE) + Σ(nocturno × recargo_nocturno)`. Todo aritmético dado las tarifas declaradas.
5. **Generación de horario propuesto**: asignar empleados disponibles a turnos respetando restricciones, priorizando por horas ya trabajadas en la semana (para distribuir equitativamente). Algoritmo greedy sin modelo.

## 6. Tramos agénticos

1. **Propuesta de ajuste ante eventos no-recurrentes**: el coordinador dice «el cliente X añadirá 300 paquetes extra el jueves». El modelo recalcula la necesidad de personal para ese día, evalúa qué opciones tiene: horas extra de empleados actuales (costo y legalidad), llamar a un pool de eventuales (costo y disponibilidad habitual), redistribuir carga a otro día. Propone la opción con mejor balance costo/servicio. Justificación: la mejor opción depende de contexto del negocio (margen del cliente, relación laboral, presupuesto de HE restante) que no está en los datos numéricos.
2. **Comunicación al equipo**: el modelo redacta el mensaje de ajuste de turno a los empleados afectados: explica el cambio, el motivo (en la medida permitida), y la expectativa. El tono es directo y respetuoso. Justificación: la comunicación operativa contextual no es una plantilla fija — depende de si es un ajuste voluntario, si hay HE compensadas, si el empleado ya tuvo cambios esa semana.
3. **Análisis de what-if de staffing**: «¿Qué pasa si contrato 3 personas más para el turno de tarde?». El modelo recalcula la cobertura, el costo semanal, y el margen de capacidad disponible para absorber variabilidad de demanda. Justificación: la interpretación del resultado en términos de decisión de contratación requiere razonamiento sobre el trade-off costo/servicio.

> [!nota]
> Ningún turno se comunica a los empleados sin que el coordinador lo revise y apruebe en la app. El `send_email` o `post_slack_message` al empleado tiene `requires_confirmation: true`.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_inputs] → tráfico forecast, roster de empleados, restricciones laborales (determinístico, tools: fetch_excel, sql_query)
  ↓
[compute_fte_needed] → FTE por franja según ratio de servicio (determinístico)
  ↓
[validate_labor_constraints] → verificar restricciones legales por empleado y turno (determinístico)
  ↓
[identify_gaps] → franjas con déficit de cobertura (determinístico)
  ↓
[compute_schedule_cost] → costo semanal del plan propuesto (determinístico)
  ↓
[propose_event_adjustments] → opciones de cobertura para eventos no-recurrentes (agéntico, tool: sql_query pool eventuales)
  ↓
[draft_team_communication] → mensaje de ajuste para empleados afectados (agéntico)
  ↓
[human_review] → coordinador revisa y aprueba el plan y los mensajes (siempre)
  ↓
[publish_schedule + notify_team] → publicar horario + notificar empleados (determinístico, tools: write_report, send_email)
  ↓
END
```

**Activities Temporal:**

- `ingest_weekly_traffic(tenant, week)` — pull del forecast de tráfico. Retry con backoff.
- `compute_weekly_schedule(tenant, week)` — scheduling + validación. Determinístico, no necesita LLM.
- `run_adjustment_agent(tenant, event_id)` — solo cuando hay evento no-recurrente. LLM call dentro de actividad.

**Tools necesarias:**

- `fetch_excel` — forecast de tráfico, roster de empleados
- `sql_query` — historial de turnos, pool de eventuales, restricciones declaradas
- `write_report` — horario semanal en PDF para afichado
- `send_email` o `post_slack_message` — notificación a empleados (requiere confirmación)

## 8. Salida y entrega

1. **Horario semanal** por empleado (tabla con nombre, día, franja horaria, turno, HE si aplica).
2. **Reporte de cobertura** por franja (FTE necesario vs. FTE asignado, gaps identificados).
3. **Costo estimado de la semana** (horas normales + HE + recargos nocturnos).
4. **Opciones de cobertura** para eventos no-recurrentes con costo y disponibilidad de cada opción.
5. **Mensajes para el equipo** listos para revisión y envío.

Canal: PDF de horario descargable para afichado + notificaciones individuales vía Slack/email tras aprobación.

**Mockup de reporte de cobertura:**

| Día | Franja | FTE Needed | FTE Assigned | Gap | Costo franja |
|-----|--------|-----------|-------------|-----|-------------|
| Lun | 08–12 | 21 | 22 | ✓ | $420.000 |
| Mié | 14–18 | 28 | 24 | ⚠ -4 | $480.000 |
| Vie | 20–00 | 36 | 30 | 🔴 -6 | $780.000 (incl. recargo) |
| **Total semana** | | | | **Déficit: 3 franjas** | **$14.280.000** |

## 9. Cómo se vende

**Gancho**: «Tu plan de turnos actual lo armas en Excel el domingo y el miércoles ya está desactualizado. El agente te da el plan en 10 minutos, con las restricciones laborales ya verificadas y los mensajes al equipo listos para enviar.»

**Diferencial LATAM**: cumplimiento automático de la legislación laboral del país (Colombia, México, Perú) — el coordinador no tiene que memorizar las reglas; el sistema las aplica siempre.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 30 empleados, FTE por franja, gaps, horario PDF | 100–200 USD/mes |
| Estándar | Hasta 100 empleados, restricciones laborales configurables, costo semanal, mensajes al equipo | 200–450 USD/mes |
| Avanzado | Ilimitado, what-if de contratación, integración Alegra Nómina, pool de eventuales | 450–900 USD/mes + setup 3–6k USD |

## 10. Riesgos

**1. Restricciones laborales del país mal configuradas.**
*Síntoma*: el sistema asigna un turno que viola el límite de horas semanales o el descanso mínimo entre turnos; la empresa queda expuesta a sanción.
*Mitigación*: las reglas laborales están en la configuración del tenant, revisadas por el responsable de RRHH en el onboarding. Cualquier cambio a las reglas requiere aprobación de dos usuarios con rol `hr_admin`. El sistema nunca modifica reglas laborales unilateralmente.

**2. Forecast de tráfico muy equivocado — el plan no cubre la demanda real.**
*Síntoma*: el plan calcula 21 FTE para el turno del lunes; llegan 800 paquetes en vez de 520; no hay personal para procesarlos a tiempo.
*Mitigación*: el sistema no puede corregir un mal forecast. El coordinador debe entender que el plan es tan bueno como el forecast. En el UI, mostrar el margen de capacidad disponible para absorber variabilidad: «Si la demanda sube 20%, sigues cubierto; si sube 35%, hay déficit en esta franja.»

**3. Mensajes enviados a empleados antes de aprobación del coordinador.**
*Síntoma*: el agente envió la notificación de cambio de turno antes de que el coordinador revisara el plan; el empleado ya reorganizó su vida personal basado en información no aprobada.
*Mitigación*: `send_email` y `post_slack_message` son herramientas con `requires_confirmation: true`. Sin excepción. El flujo de UI tiene un paso explícito de «Revisar y enviar» que es diferente de «Guardar plan».

**4. Pool de eventuales desactualizado.**
*Síntoma*: el agente propone llamar a 3 eventuales del pool; 2 ya no están disponibles porque se contrató uno y el otro se mudó.
*Mitigación*: el pool de eventuales es una lista mantenida por el coordinador en la app. El agente consulta la lista pero el coordinador confirma disponibilidad real antes de comprometerse.

## 11. Variantes por industria

### Instancia 1 — Logística / 3PL (`expreslog`)

**Datos típicos**: 40–80 empleados entre operadores de bodega, montacarguistas y conductores. Turnos rotativos (mañana/tarde/noche). Picos de demanda predecibles (temporadas) e impredecibles (cliente que añade volumen sin aviso). Alta regulación laboral (Colombia: Código Sustantivo del Trabajo; México: LFT).

**Delta determinístico**: montacarguistas requieren certificación vigente. El sistema valida que el empleado asignado a un turno de montacargas tenga su certificación activa en el registro del tenant. Regla binaria — sin certificación, no asignar.

**Delta agéntico**: cliente de logística llama el martes a las 3pm para añadir 200 envíos para el día siguiente. El agente evalúa en tiempo real: cuánto personal tiene disponible para HE esa noche (respetando el límite semanal de cada empleado), si hay eventuales en el pool, y si tiene sentido redistribuir parte de la carga a la tarde del mismo día. Produce la propuesta en 2 minutos.

**Regulación**: en Colombia, recargo nocturno (35% extra) a partir de las 9pm; dominical (75% extra); festivo (100% extra). El sistema calcula estos recargos automáticamente y los incluye en el costo del turno.

**Precio orientativo**: 200–450 USD/mes.

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 15–40 empleados entre cocineros, meseros y personal de limpieza. Demanda basada en reservas + walk-in. Alta variabilidad viernes–sábado. Rotación de personal alta (LATAM F&B: 60–80% anual). Propinas que afectan la satisfacción por asignación de turno.

**Delta determinístico**: la demanda de trabajo se estima como `covers_forecast × minutos_servicio_por_cover / 60 = horas_mesero_necesarias`. El `minutos_servicio_por_cover` es configurable por tipo de servicio (almuerzo express: 35 min; cena: 75 min). Aritmética.

**Delta agéntico**: llega una reserva de grupo de 30 personas para el sábado a las 8pm — 2 horas antes del cierre de la cocina. El agente evalúa si es viable (capacidad de cocina, personal disponible esa noche, impacto en otros clientes) y propone si aceptar con condiciones (menú cerrado, descorche, no más meseros disponibles) o rechazar con alternativa (domingo a las 7pm). Justificación: la decisión involucra múltiples trade-offs de negocio.

**Regulación**: en Colombia, trabajo en día de descanso obligatorio (domingo) requiere compensatorio o recargo del 75% según Código Laboral. El sistema alerta antes de asignar un domingo sin compensatorio disponible.

**Precio orientativo**: 100–250 USD/mes.

## 12. Módulos técnicos relacionados

- **B02** (4 capas FastAPI): `POST /schedules/generate` llama al servicio de scheduling; `GET /schedules/{week}/coverage` devuelve el reporte de cobertura. El servicio valida restricciones laborales antes de retornar el plan.
- **C01** (SQLAlchemy async): tabla `schedules` con `tenant_id`, `week`, `employee_id`, `shift_start`, `shift_end`, `is_overtime`, `approved_by`. Índice compuesto `(tenant_id, week, employee_id)`.
- **E01** (Anthropic SDK + tools): el what-if de contratación es el ejemplo de razonamiento multi-paso: el modelo consulta el costo actual, consulta el gap histórico de cobertura, calcula el impacto de añadir 3 personas, y produce la recomendación con justificación estructurada.
- **E05** (Temporal): `WeeklyScheduleWorkflow` — genera el plan cada semana de forma durable. Si el proceso falla a mitad, Temporal lo retoma desde el último punto completado sin recalcular todo.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Cálculo de FTE necesario por franja | determinístico | `ceil(tráfico / ratio)` — aritmética pura. |
| Validación de restricciones laborales | determinístico | Reglas fijas por país/contrato; check binario. |
| Identificación de gaps de cobertura | determinístico | Comparación numérica FTE needed vs. FTE assigned. |
| Cálculo de costo semanal con recargos | determinístico | Aritmética con tarifas y recargos declarados. |
| Propuesta de opciones para evento no-recurrente | agéntico | Trade-offs entre costo, legalidad y relación laboral — depende del contexto. |
| Redacción de comunicación al equipo | agéntico | Tono y especificidad dependen del tipo de cambio y del historial del empleado. |
| Análisis de what-if de contratación | agéntico | La interpretación del resultado en términos de decisión estratégica requiere contexto. |

## 13. Errores típicos

**1. Ratio de servicio hardcodeado sin revisar.**
*Síntoma*: el sistema calcula que necesita 21 operadores para 520 paquetes porque alguien configuró «1 operador por 25 paquetes» hace 2 años; la productividad mejoró y hoy 1 operador maneja 30.
*Causa*: el ratio de servicio es una constante en la configuración que nadie revisó.
*Arreglo*: mostrar en el dashboard el ratio declarado vs. el ratio real observado (calculado de `paquetes_procesados / horas_trabajadas` del período anterior). Si difieren > 20%, alerta para revisión.

**2. Asignación de turno sin verificar el límite de horas semanales acumuladas.**
*Síntoma*: el sistema asigna un turno extra el sábado a un empleado que ya tiene 44 horas en la semana; 46 horas superan el máximo legal (Colombia: 47h incluyendo HE, pero hay que verificar el contrato individual).
*Causa*: el check de restricción laboral no acumuló las horas de los otros turnos de la semana antes de asignar.
*Arreglo*: calcular `horas_acumuladas_semana` por empleado antes de asignar cualquier turno. La asignación de HE solo es posible si `horas_acumuladas + horas_turno_nuevo ≤ max_horas_semana_tenant`.

**3. Mensaje al empleado enviado con información incorrecta del turno.**
*Síntoma*: el mensaje dice «Turno el miércoles 14:00–22:00» pero el plan se actualizó a «14:00–20:00» después de que alguien lo editó; el empleado llegó preparado para 8 horas.
*Causa*: el mensaje se generó con la versión del plan antes de la última edición.
*Arreglo*: el mensaje se genera siempre a partir del plan en estado `aprobado`, no del borrador. El botón «Enviar mensajes» solo aparece después de que el coordinador marca el plan como aprobado definitivo.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame cómo el ratio de servicio se convierte en FTE necesario con un ejemplo de Logística Express un lunes de pico.»
2. **Aplícalo a mi caso**: «Mi empresa opera en México con turno mixto (6am–2pm, 2pm–10pm, 10pm–6am). ¿Cómo configuro las restricciones de la LFT mexicana en el sistema?»
3. **Por qué falló**: «El agente asignó un turno nocturno a un empleado que ya tenía 46 horas en la semana. ¿En qué validación falló?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el cálculo de FTE necesario desde el forecast de tráfico y el ratio de servicio declarado.
- Implementar la validación de restricciones laborales (descanso, HE, recargo nocturno) como reglas configurables por país.
- Separar el scheduling determinístico del ajuste agéntico para eventos no-recurrentes.
- Configurar el flujo de aprobación obligatoria antes de comunicar cualquier cambio de turno al empleado.
- Cotizar y dimensionar el servicio para logística o hospitalidad LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| B03   | El dashboard de cobertura semanal (FTE needed vs. assigned por franja, gaps, costo) es una vista HTMX que se actualiza sin recargar la página; B03 enseña el patrón Jinja + HTMX que esta ficha instancia en el reporte de turnos. |
| C01   | La tabla `schedules` con `tenant_id`, `employee_id`, `is_overtime` y `approved_by`, y el índice compuesto `(tenant_id, week, employee_id)` para validar horas acumuladas, siguen el patrón de SQLAlchemy async que C01 establece. |
| D04   | El ratio de servicio declarado vs. el ratio real observado (`paquetes_procesados / horas_trabajadas`) se traza en Phoenix; si difieren más del 20%, la alerta aparece en el dashboard antes de que el coordinador planifique con un ratio incorrecto. |
| E01   | El what-if de contratación — el modelo consulta costo actual, gap histórico e impacto de añadir FTE en un loop multi-herramienta con justificación estructurada — es el patrón de razonamiento encadenado que E01 introduce. |
| E05   | `WeeklyScheduleWorkflow` con `ingest_weekly_traffic` y `compute_weekly_schedule` como actividades separadas, retomable desde el último punto completado sin recalcular, es el patrón de workflow durable que E05 enseña. |
