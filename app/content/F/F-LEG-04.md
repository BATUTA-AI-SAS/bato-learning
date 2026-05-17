---
ext_id: F-LEG-04
slug: poderes-vigencias
track: F
dept: LEG
ord: 263
title: "Gestión de poderes y vigencias documentales"
summary: "Agente que extrae el alcance y las fechas de vigencia de poderes notariales y documentos habilitantes, alerta antes del vencimiento, y verifica si el firmante autorizado puede suscribir una operación concreta."
estimated_minutes: 30
industries_instanced: [construccion, agro]
tenants_in_examples: [andina, cafetera]
---

## 1. Problema operativo

El gerente de contratos de Constructora Andina firma 10–20 documentos al mes: actas de obra, contratos de subcontratación, pólizas, otrosíes. Algunos los firma él directamente; otros los firma el representante legal; otros los puede firmar un apoderado. El problema: los poderes vencen, los apoderados cambian, y nadie tiene un registro centralizado de quién puede firmar qué y hasta cuándo.

Resultado: un contrato firmado por un apoderado cuyo poder venció hace 3 meses. La aseguradora rechaza la reclamación. El abogado externo cobra 6 horas para explicar qué pasó.

Cooperativa Cafetera del Valle tiene el mismo problema multiplicado: opera en 4 departamentos con representantes regionales, agentes de acopio y apoderados para trámites ante el ICA, la DIAN y notarías locales. Perder la trazabilidad de un poder en el campo es perder una cosecha o una exportación.

---

## 2. Hoy en big corps

Las empresas con departamento legal de más de 5 abogados combinan su CLM con módulos de gestión de representaciones.

| Vendor | Capacidad relevante | Precio orientativo |
|--------|--------------------|--------------------|
| **DocuSign CLM** | Almacenamiento de poderes + calendario de vencimientos + alertas | 30–80 USD/usuario/mes en plan CLM |
| **Adobe Sign Enterprise** | Firma + repositorio documental con vencimientos | Enterprise, cotización |
| **Ironclad** | Modulo de "Signatory Management" para grandes corporaciones | Incluido en plan enterprise 30k+ USD/año |
| **Legito** | CLM con gestión de documentos habilitantes; popular en Europa | 30–100 USD/usuario/mes |

Una PYME no necesita un CLM completo. Necesita una hoja de Excel que no pierda datos, un recordatorio antes de que venza el poder, y la capacidad de preguntar "¿puede Jorge Méndez firmar este contrato de COP 200 M?" sin buscar en 4 carpetas de Drive.

---

## 3. PYME LATAM realista

Andina y Cafetera tienen sus poderes en:
- Una carpeta de Drive o Dropbox sin nomenclatura consistente.
- Algunas escrituras en papel guardadas en una caja fuerte.
- El conocimiento en la cabeza de la asistente jurídica de turno.

Consultan la Cámara de Comercio (RUES) para ver el certificado de existencia y representación legal. Pero los poderes especiales otorgados por escritura pública están en notaría — no hay un sistema centralizado para consultarlos a nivel nacional.

La DIAN y el ICA (Instituto Colombiano Agropecuario) exigen poderes notariales para ciertos trámites. La fecha de vencimiento importa.

---

## 4. Datos típicos

| Atributo | Detalle |
|----------|---------|
| Documento | PDF de escritura pública de poder, certificado de existencia RUES, acta de junta con delegación de facultades |
| Fuente | Notaría (físico o digital), Cámara de Comercio (RUES), email del apoderado |
| Frecuencia de actualización | Baja: 2–10 poderes nuevos/año por tenant; muchos son plurianuales |
| Campos críticos | Nombre del apoderado, CC/NIT, facultades otorgadas (qué puede hacer), límite de cuantía (si aplica), fecha de vigencia desde/hasta, notaría y escritura |
| Ejemplo de registro | `{power_id: "EP-2025-0087", grantor: "Constructora Andina S.A.S.", grantee: "Jorge Méndez CC-8.765.432", notary: "Notaría 4 de Bogotá", escritura: "4512", valid_from: "2025-03-01", valid_until: "2026-06-30", scope: ["contratos de obra hasta COP 500.000.000", "trámites RUES", "firma de pólizas"]}` |

---

## 5. Tramos determinísticos

1. **Extracción de metadatos estructurados**: OCR + regex sobre campos estandarizados de la escritura pública: número de escritura, notaría, fecha de otorgamiento, nombre del poderdante, nombre del apoderado, cédula, fecha de vigencia. Los encabezados y cierres de escrituras en Colombia siguen formatos notariales relativamente estándar.
2. **Tracking de vigencias**: calcular `días_restantes = valid_until - today`. Clasificar: `VIGENTE`, `PRÓXIMO_A_VENCER` (< 60 días), `VENCE_MUY_PRONTO` (< 30 días), `VENCIDO`.
3. **Alertas automáticas por calendario**: T-60, T-30, T-15 días antes del vencimiento. Alerta al responsable legal del tenant + al gerente apoderado.
4. **Registro en `powers_registry` con `tenant_id`**: todos los campos extraídos, el PDF original archivado, historial de renovaciones.
5. **Verificación de quórum de firmas**: para operaciones que requieren múltiples autorizados (contratos > COP 1 000 M requieren firma del representante legal + un apoderado), validar que los dos poderes estén vigentes.

---

## 6. Tramos agénticos

1. **Extracción del alcance del poder desde texto libre** — las escrituras de poder describen las facultades en lenguaje jurídico narrativo: "para suscribir en nombre de la sociedad contratos de obra, suministro y servicios, cuyo valor individual no exceda la suma de quinientos millones de pesos moneda corriente (COP 500.000.000), así como para gestionar trámites ante entidades públicas y privadas relacionados con la actividad constructora...". Extraer de esto: `scope_tags: ["contratos_obra", "contratos_suministro", "tramites_publicos"]` y `max_amount: 500_000_000` requiere entender lenguaje jurídico con variaciones entre notarías.

   *Por qué no es regla*: el lenguaje de alcance varía enormemente entre escrituras. Una regex captura "valor de" pero no "cuantía máxima de" ni "importe que no sobrepase". El parseo exacto exige lectura comprensiva.

2. **Verificación de si un poder cubre una operación concreta** — el usuario pregunta: "¿puede Jorge Méndez firmar el contrato de alquiler de maquinaria por COP 320 M?". El modelo cruza el alcance extraído del poder contra el tipo y valor de la operación: ¿"alquiler de maquinaria" está cubierto por "contratos de suministro"? ¿COP 320 M está bajo el límite de COP 500 M?

   *Por qué no es regla*: "contratos de suministro" puede o no cubrir "alquiler de maquinaria" dependiendo del contexto jurídico y de la redacción específica del poder. Una regla de keyword matching genera falsos positivos jurídicamente costosos.

3. **Sugerencia de renovación anticipada**: cuando el modelo detecta un poder próximo a vencer para un apoderado que tiene operaciones pendientes en el pipeline, sugiere iniciar el trámite de renovación indicando: qué notaría lo otorgó originalmente, qué documento presentar, tiempo estimado del trámite notarial.

   *Por qué no es regla*: la sugerencia depende del contexto del pipeline de operaciones del tenant (qué contratos están pendientes) y del histórico del tiempo de renovación de esa notaría específica.

4. **Fallback humano**: cuando el modelo no puede determinar con certeza si el poder cubre una operación (alcance ambiguo, límites de cuantía no explícitos), responde `REQUIRES_LEGAL_REVIEW` y escala al abogado con el texto exacto de la cláusula de alcance. Nunca dice "sí, puede firmar" si hay ambigüedad.

---

## 7. Blueprint del workflow

```
[INGEST_POWER]
  PDF escritura → OCR → text (determinístico)
      |
[EXTRACT_METADATA]           (determinístico — regex sobre campos notariales)
  → {grantee, grantor, valid_from, valid_until, notary, escritura_num}
      |
[EXTRACT_SCOPE]              ← agéntico
  LLM: (scope_text) → {scope_tags, max_amount, restrictions}
  confidence < 0.75 → flag SCOPE_NEEDS_REVIEW
      |
[STORE]
  powers_registry (tenant_id, power_id, metadata, scope, raw_pdf_ref)
      |
═══════════════════════════════════════
QUERY: "¿puede X firmar operación Y?"
═══════════════════════════════════════
      |
[LOOKUP_POWERS]              (determinístico)
  filtrar poderes vigentes del apoderado X
      |
[CHECK_COVERAGE]             ← agéntico
  LLM: (power_scope, operation_type, operation_amount)
  → {covered: bool, confidence, rationale}
  confidence < 0.8 OR covered = ambiguous → REQUIRES_LEGAL_REVIEW
      |
[RESPOND]
  "Sí, cubierto" | "No, fuera de alcance" | "Requiere revisión legal"
═══════════════════════════════════════
DAILY JOB: alertas de vencimiento
═══════════════════════════════════════
  calcular días_restantes para cada poder → enviar alertas T-60/T-30/T-15
```

---

## 8. Salida y entrega

**Vista en dashboard (tabla viva)**:

```
PODERES VIGENTES — Constructora Andina (2026-05-16)
┌─────────────────────┬──────────────────────────────────────────┬────────────────┬──────────┐
│ Apoderado           │ Facultades                               │ Vence          │ Estado   │
├─────────────────────┼──────────────────────────────────────────┼────────────────┼──────────┤
│ Jorge Méndez        │ Contratos obra/suministro hasta 500M COP │ 2026-06-30     │ ⚠ 45 días│
│ María Torres        │ Trámites DIAN, RUES, firma laboral       │ 2027-01-15     │ VIGENTE  │
│ Pedro Vargas        │ Firma de pólizas de seguros              │ 2025-12-01     │ VENCIDO  │
└─────────────────────┴──────────────────────────────────────────┴────────────────┴──────────┘
```

**Respuesta a consulta puntual**:
```
Consulta: ¿Puede Jorge Méndez firmar el contrato OBR-2026-091 (alquiler maquinaria, COP 320M)?

Respuesta: SÍ, con reserva
  - Poder vigente hasta 2026-06-30 (45 días restantes).
  - COP 320M está dentro del límite de COP 500M.
  - "Alquiler de maquinaria" cubre bajo "contratos de suministro" según el alcance.
  - NOTA: el poder vence en 45 días. Si el contrato tiene vigencia mayor, revisar si el poder
    debe renovarse antes de firma.
  - Confianza del modelo: 82%. Recomendado confirmar con abogado si hay duda sobre cobertura.
```

---

## 9. Cómo se vende

**Gancho**: "¿Cuántos contratos firmaron el año pasado con un poder vencido sin saberlo? Este agente no lo deja pasar."

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Starter | Hasta 20 poderes, alertas email, consulta manual | 100–200 USD/mes |
| Profesional | Hasta 100 poderes, consultas vía API/chat, integración Drive | 250–500 USD/mes |
| Enterprise | Multi-sede, multi-país, integración con CLM existente | 500–1 200 USD/mes |

Setup (carga inicial de poderes existentes, OCR + extracción inicial del corpus): 500–1 500 USD una vez.

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Extracción incorrecta del alcance** (el modelo lee mal las facultades) | El sistema dice "sí puede firmar" cuando no puede | (1) Toda extracción de alcance pasa por revisión humana en la carga inicial (golden set). (2) Consultas con confianza < 0.8 siempre escalan al abogado. (3) El modelo nunca da una respuesta de "sí" sin mostrar la cláusula exacta de donde infirió el alcance. |
| **OCR de mala calidad en escrituras antiguas** | Campos clave no extraídos; poder no registrado | Marcar documentos con OCR confidence < 0.85 como `NEEDS_MANUAL_ENTRY`. Formulario de carga manual para el equipo legal. |
| **El agente no reemplaza el juicio jurídico** | Si el tenant firma basándose solo en la respuesta del agente sin abogado, asume riesgo legal | Disclaimer en cada respuesta de consulta: "Esta respuesta es orientativa. Para operaciones de alta cuantía o complejidad, confirmar con el abogado de la empresa." |
| **Poderes de papel no digitalizados** | El sistema tiene información incompleta | Proceso de onboarding: inventariar y escanear todos los poderes existentes antes del primer uso. Incluir en el contrato de servicio que el cliente es responsable de cargar todos sus poderes. |

---

## 11. Variantes por industria

| Delta | Construcción (Andina) | Agro / Exportación (Cafetera) |
|-------|----------------------|-------------------------------|
| Tipos de poder más frecuentes | Poder de representación para contratos de obra, pólizas, RUES | Poder para trámites ICA (fitosanitarios), DIAN (exportación), contratos de comercialización de café |
| Entidades donde se usa | RUES, aseguradoras, notarías locales | ICA, DIAN, Federación Nacional de Cafeteros, puertos |
| Alcance típico | Contratos por cuantías definidas + trámites sectoriales | Certificados de exportación, actas de entrega de cosecha, contratos de precio diferido |
| Vigencia típica | 1–2 años, renovación por escritura pública | 6–12 meses para trámites exportación; algunos por campaña de cosecha |
| Dispersión geográfica | Ciudad + obra activa | 4 departamentos + agentes de campo sin acceso digital fluido |
| Riesgo sectorial | Nulidad de póliza, retraso en obra | Rechazo de exportación por poder vencido = pérdida de la operación |
| Precio tier profesional | 250–400 USD/mes | 350–500 USD/mes |

---

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica |
|--------|-----------|
| **B02** — FastAPI routers y deps | Endpoint `POST /powers/ingest` para subir PDF; `GET /powers/check?grantee=X&operation=Y&amount=Z` para la consulta puntual. |
| **C01** — SQLAlchemy y modelos ORM | Modelo `PowerOfAttorney` con campos `valid_from`, `valid_until`, `scope_json`, `raw_pdf_path`; relación con `tenant_id`. |
| **E01** — Anthropic SDK tool loop | La verificación de cobertura: el modelo llama a `get_power_scope(power_id)` para leer el alcance extraído antes de emitir su juicio. |
| **E05** — Temporal | Workflow `power_expiry_monitor`: schedule diario que calcula días restantes y dispara actividades de notificación en T-60, T-30, T-15. |

## 13. Errores típicos

**1. El agente dice «sí puede firmar» con ambigüedad de alcance y el equipo no consulta al abogado.**
*Síntoma*: el modelo responde «SÍ, cubierto» con confianza del 65% para un alquiler de maquinaria bajo un poder que dice «contratos de suministro», y el equipo firma sin verificar con el abogado porque el sistema dijo que sí.
*Causa raíz*: el agente no reemplaza el juicio jurídico. El modelo puede equivocarse en la interpretación de términos jurídicos con variaciones entre notarías; la confianza del 65% debería haber disparado `REQUIRES_LEGAL_REVIEW`.
*Cómo evitarlo*: el umbral para `REQUIRES_LEGAL_REVIEW` es confianza < 0.80, no < 0.50. Cualquier respuesta «sí» con confianza entre 0.80 y 0.90 incluye automáticamente la frase «Confirmar con el abogado antes de firma». Para operaciones > COP 200M, la revisión del abogado es obligatoria independientemente de la confianza del modelo.

**2. Dependencia ciega del LLM para interpretar alcance de poderes sin revisión en la carga inicial.**
*Síntoma*: el poder de Jorge Méndez fue cargado al sistema y el modelo extrajo `scope_tags: ["contratos_obra"]` pero omitió `["tramites_publicos"]` porque esa facultad estaba en el segundo párrafo en un formato diferente; durante 6 meses el equipo cree que Méndez no puede hacer trámites ante la DIAN.
*Causa raíz*: la extracción del alcance en la carga inicial se aceptó sin revisión humana porque la confianza del modelo era alta.
*Cómo evitarlo*: toda extracción de alcance en la carga inicial pasa por revisión humana obligatoria del abogado o asistente jurídica, sin excepción. El sistema muestra el texto original de la cláusula junto al alcance extraído para facilitar la validación. Una vez aprobado por el revisor, se registra `scope_validated_by` y `scope_validated_at` en el expediente.

**3. Poderes físicos no digitalizados que generan un registro incompleto.**
*Síntoma*: un apoderado de Cafetera firma una exportación con un poder que está en papel en la caja fuerte de la oficina central; el ICA rechaza la operación porque el poder no está en el registro digital del sistema y nadie puede verificarlo remotamente.
*Causa raíz*: el onboarding no inventarió todos los poderes existentes; el sistema solo tiene los poderes nuevos emitidos desde que se implementó la solución.
*Cómo evitarlo*: el contrato de servicio incluye una cláusula explícita de que el cliente es responsable de cargar todos los poderes vigentes durante el onboarding. El proceso de onboarding incluye un inventario físico y la digitalización de todos los poderes antes del primer uso en producción.

**4. Alerta de vencimiento ignorada porque llega al correo equivocado.**
*Síntoma*: la alerta T-30 del poder de Jorge Méndez llegó a la asistente jurídica que renunció hace un mes; el poder vence sin renovación y se firma un contrato con poder vencido.
*Causa raíz*: los destinatarios de las alertas están hardcodeados al email de una persona en lugar de a un rol o grupo.
*Cómo evitarlo*: las alertas de vencimiento se envían a un grupo de distribución configurado por el tenant (ej. `legal-team@andina.com`), no a una persona individual. El tenant debe actualizar esta configuración cuando hay cambios en el equipo jurídico. El sistema valida que el grupo tenga al menos un destinatario activo en el onboarding.

---

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué la verificación de si un poder cubre una operación concreta es un tramo agéntico y no una búsqueda de keywords, con el ejemplo de 'alquiler de maquinaria' vs. 'contratos de suministro' de la sección 6.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este pipeline si trabajo con poderes otorgados en otros países (poderes apostillados de proveedores internacionales), donde el formato notarial es completamente diferente al colombiano.»
3. **Por qué falló**: «El sistema respondió 'SÍ, cubierto' para el contrato OBR-2026-091 pero el poder había vencido 3 días antes. ¿En qué nodo del workflow se debió detectar el vencimiento y por qué no se detectó?»

---

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de extracción de poderes con OCR, validación de confianza, y revisión humana obligatoria del alcance extraído en la carga inicial.
- Implementar el sistema de alertas de vencimiento T-60/T-30/T-15 con Temporal, enviadas a grupos de distribución en lugar de personas individuales.
- Configurar el umbral de confianza para `REQUIRES_LEGAL_REVIEW` y los casos donde la revisión del abogado es obligatoria independientemente de la confianza del modelo.
- Identificar los riesgos jurídicos de una respuesta incorrecta del agente (firma con poder vencido, firma fuera de alcance) y las mitigaciones en el harness.
- Evaluar el retorno de inversión de la solución comparando el costo de un error de poder vencido (abogado externo + disputa contractual) contra el costo del servicio.

---

## 16. Módulos previos recomendados

| Módulo | Por qué prepara para esta ficha |
|--------|---------------------------------|
| **E01** — Anthropic SDK tool loop | La verificación de cobertura: el modelo llama a `get_power_scope(power_id)` para leer el alcance antes de emitir su juicio; sin E01, el estudiante no implementa correctamente el tool loop con respuesta estructurada y manejo de confianza. |
| **E05** — Temporal + idempotencia | El workflow `power_expiry_monitor` con schedule diario y actividades de notificación en T-60/T-30/T-15 es el patrón central de E05; sin él, el estudiante implementa un cron job frágil sin retry ni idempotencia. |
| **D04** — Observabilidad y trazas auditables | Cada consulta de cobertura genera un span con `power_id`, `operation_type`, `covered`, `confidence`, y la cláusula citada; D04 enseña a construir estas trazas para que sean auditables por el abogado en caso de disputa. |
| **C01** — SQLAlchemy async | El modelo `PowerOfAttorney` con campos `valid_from`, `valid_until`, `scope_json`, y la relación con `tenant_id` es el patrón ORM central; sin C01, el estudiante no puede implementar el `powers_registry` correctamente. |
