---
ext_id: F-CMP-03
slug: ocr-validacion-facturas
track: F
dept: CMP
ord: 143
title: "OCR + validación de facturas de proveedor (3-way match)"
summary: "Extrae campos de facturas PDF escaneadas, valida contra PO y recepción con tolerancias configurables, consulta NIT/RUT en DIAN/SAT y deja solo las discrepancias genuinas para decisión humana."
related_modules: [A06, B02, C01, E01]
industries_instanced: [salud, hospitalidad]
tenants_in_examples: [sanrafael, mesonurbano]
big_corp_vendors: [Esker, Tradeshift, Vic.ai, Tipalti]
latam_tools: [siigo-fe, contpaq-cfdi, alegra, dian-api, sat-api]
key_concepts: [OCR, 3-way-match, tolerancias, CFDI, factura-electronica, DIAN, parse-invoice]
estimated_minutes: 60
deterministic_share: 0.7
version: 1
---

## 1. Problema operativo

La jefa de cuentas por pagar de Clínica San Rafael recibe 200–300 facturas de proveedores al mes: medicamentos, insumos quirúrgicos, servicios de mantenimiento. Un 30% llegan en papel o PDF escaneado. El proceso actual: imprimir, buscar la orden de compra en el ERP, comparar a mano los ítems, verificar si los montos coinciden con la recepción, timbrar si todo cuadra. Toma 8 minutos por factura, 40 horas al mes para la asistente. Las facturas en papel además tienen riesgo de error de transcripción al ERP. Necesita que el 70% de facturas rutinarias se procesen automáticamente y solo las discrepancias genuinas lleguen a la persona.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **Esker** | Captura OCR + matching automático + flujo de aprobación en portal, integración con ERPs enterprise | 15–50 USD/usuario/mes + 0.05–0.20 USD/factura procesada |
| **Tradeshift** | Red de facturas B2B, e-invoicing, matching automático, supply chain finance | Desde 500 USD/mes; enterprise 5–50k/año |
| **Vic.ai** | IA nativa para AP automation, aprende de las aprobaciones históricas del cliente, integración NetSuite/SAP | 1–3 USD/factura o suscripción 1–5k USD/mes |
| **Tipalti** | Global AP automation, pagos internacionales, 1099/W-8, matching | 299–749 USD/mes base + fees por transacción |

El modelo big corp usa e-invoicing estructurado (EDI, XML) cuando el proveedor lo soporta. El OCR es el fallback para quienes no. En LATAM la factura electrónica (CFDI en México, e-doc DIAN en Colombia) es el caso **principal**, no el fallback — aunque llega como XML adjunto que muchos ERP PYME no procesan automáticamente.

## 3. PYME LATAM realista

Mesón Urbano recibe sus facturas de varios canales: XML CFDI por correo (México), PDF digital, foto WhatsApp del recibo, papel escaneado. Siigo Facturación Electrónica puede recibir el XML si el proveedor lo envía correctamente — pero el módulo no valida automáticamente contra la orden de compra. Alegra tampoco. El resultado: alguien igual tiene que abrir el PDF, abrir el ERP, comparar a mano.

La oportunidad: en Colombia, la DIAN expone una API de validación de facturas electrónicas. En México, el SAT tiene consulta de CFDI. Estos dos tramos — OCR y validación fiscal — son determinísticos y cubren el 70% del trabajo.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Factura electrónica (e-doc DIAN) | XML + PDF representación gráfica | Por transacción | 50–200/mes |
| CFDI México | XML `.xml` | Por transacción | 30–150/mes |
| Factura en PDF digital (sin XML) | PDF con texto seleccionable | Por transacción | 20–80/mes |
| Factura escaneada / foto | PDF escaneado, JPEG | Por transacción | 10–50/mes |
| Orden de compra (PO) | Tabla ERP exportada | Por período | 50–300 POs activas |
| Nota de recepción (GRN) | Excel o tabla ERP | Por recepción | mismas líneas que PO |

**Ejemplo de comparación 3-way:**

| Campo | PO | Factura extraída | Recepción | Resultado |
|-------|----|-----------------|-----------|-----------|
| Proveedor NIT | 900.123.456-7 | 900.123.456-7 | — | ✓ |
| Monto total | $4.500.000 | $4.590.000 | — | ⚠ Δ = 2% (dentro tolerancia) |
| Ítem: Guantes nitrilo x100 | 10 cajas | 10 cajas | 10 cajas | ✓ |
| Ítem: Gasas estériles x50 | 20 unid | 20 unid | 18 unid | ❌ Cantidad recepción < factura |

## 5. Tramos determinísticos

1. **Parsing XML CFDI / e-doc DIAN**: leer el XML directamente; extraer `Emisor.Rfc`, `Total`, `Conceptos`, `FechaTimbrado`. Sin OCR: los datos ya están estructurados. Cobertura: ~40–60% de las facturas en clientes modernos.
2. **OCR de PDF con texto seleccionable**: `pdfplumber` extrae el texto; expresión regular sobre patrones de NIT/RUT (`\d{3}\.\d{3}\.\d{3}-\d`), montos (`\$\s*[\d.,]+`) y fechas. Confianza alta cuando el PDF fue generado digitalmente.
3. **OCR de PDF escaneado o imagen**: Google Document AI Invoice Parser (Vertex AI) o AWS Textract con el modelo de facturas. Costo: ~1,50 USD/1000 páginas con Document AI en volumen. Extrae campos estructurados con `confidence` por campo.
4. **Validación NIT/RUT contra autoridad fiscal**: consulta API DIAN (Colombia) o API SAT (México) para confirmar que el proveedor está activo, que la factura fue timbrada y no está cancelada. Resultado binario: válida/inválida.
5. **3-way match determinístico**: comparar `{proveedor, monto, ítems, cantidades}` entre factura y PO + GRN. Calcular `Δmonto = |factura_total - po_total| / po_total`. Si `Δmonto ≤ tolerancia_tenant` (configurable, default 3%) y cantidades coinciden → match automático aprobado.
6. **Detección de duplicados**: buscar en la base del tenant si ya existe una factura con el mismo `numero_factura + proveedor_id`. Hash del par para indexación rápida.

## 6. Tramos agénticos

1. **Resolución de discrepancias menores**: cuando la descripción del ítem en la factura difiere de la PO pero parece el mismo producto («Guantes de nitrilo talla M» vs. «Guantes nitrilo M x100 pares»), el modelo decide si es el mismo ítem o si es un producto diferente. Justificación: sin regla — la variación de nomenclatura entre el catálogo de compras y el catálogo del proveedor es libre.
2. **Clasificación de diferencias genuinas**: cuando el monto supera la tolerancia, el modelo evalúa si es: a) un cargo adicional legítimo no en la PO (ej: flete incluido en factura pero no en orden), b) error del proveedor, c) cambio de precio acordado verbalmente. El modelo produce una hipótesis con `tipo` y `accion_sugerida`. Justificación: el contexto (hay un correo de aprobación, hay una nota en el ERP) importa; la regla no lo puede capturar.
3. **Redacción de consulta al proveedor**: cuando hay discrepancia no resuelta, el modelo redacta el correo al proveedor explicando el hallazgo, el monto de la diferencia y la acción requerida. Tono profesional, datos exactos.

> [!cuidado]
> Para medicamentos y dispositivos médicos críticos (Clínica San Rafael), **nunca** se aprueba automáticamente una factura con discrepancia en cantidad, sin importar el monto. El guardrail es incondicional: cualquier diferencia en `cantidad_recibida` vs. `cantidad_facturada` en SKUs clase `CRITICO` va siempre a revisión humana.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_invoice] → recibe PDF/XML por email o upload manual (determinístico)
  ↓
[detect_format] → XML CFDI / XML DIAN / PDF digital / PDF escaneado / imagen (determinístico)
  ↓
[parse_invoice] → parsing según formato; OCR si escaneado (determinístico, tool: parse_invoice_pdf)
  ↓
[validate_fiscal] → consulta DIAN/SAT para validar NIT y estado del timbre (determinístico)
  ↓
[check_duplicate] → hash factura+proveedor contra historial del tenant (determinístico, tool: sql_query)
  ↓
[three_way_match] → comparar contra PO+GRN del tenant (determinístico, tool: sql_query)
  ↓
[auto_approve?] → si match dentro de tolerancias y SKU no-crítico → aprobación automática
       |
       └── discrepancia detectada →
[resolve_discrepancy] → modelo evalúa hipótesis de diferencia (agéntico)
  ↓
[draft_query?] → si hipótesis necesita confirmación → redactar correo al proveedor (agéntico)
  ↓
[human_review] → contador revisa discrepancias no resueltas o SKUs críticos (siempre que aplica)
  ↓
[approve_and_post] → registrar en ERP / Siigo / Alegra (determinístico)
  ↓
END
```

**Tools necesarias:**

- `parse_invoice_pdf` — OCR + extracción estructurada
- `sql_query` — POs, GRNs, historial de facturas del tenant
- `send_email` — consulta al proveedor (requiere confirmación)

## 8. Salida y entrega

1. **Bandeja de aprobaciones automáticas**: lista de facturas procesadas sin discrepancia, listas para postear en el ERP.
2. **Bandeja de excepciones**: facturas con discrepancias clasificadas por tipo, con la hipótesis del agente y la acción sugerida.
3. **Borrador de correo** al proveedor para las discrepancias que requieren aclaración.
4. **Dashboard diario**: volumen procesado, tasa de aprobación automática, tiempo promedio de ciclo.

Canal: panel en la app + integración opcional con Siigo FE / Alegra via API para posteo automático.

**Mockup de bandeja de excepciones:**

| Factura | Proveedor | Monto | Discrepancia | Hipótesis agente | Acción |
|---------|-----------|-------|--------------|-----------------|--------|
| FE-2026-0891 | Medisuplies | $4.590k | Δmonto +2% | Cargo flete incluido | Consultar proveedor |
| FE-2026-0892 | CleanPro | $1.200k | Ítem «Desinfectante 5L» no en PO | Item agregado post-PO | Revisar con compras |
| FE-2026-0893 | Farmacol | $38.400k | Cantidad Insulina 100UI: factura 50 ≠ recepción 48 | SKU CRÍTICO — forzar revisión | 🔴 Revisión humana obligatoria |

## 9. Cómo se vende

**Gancho**: «El 70% de tus facturas son rutinarias y no necesitan que nadie las toque. El agente las procesa en segundos; tú solo ves las excepciones reales.»

**Diferencial en LATAM**: validación fiscal integrada (DIAN/SAT) que ningún ERP PYME hace automáticamente.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 100 facturas/mes, OCR + 3-way match, XLSX de excepciones | 150–300 USD/mes |
| Estándar | Hasta 500 facturas/mes, validación DIAN/SAT, integración Siigo/Alegra | 300–600 USD/mes |
| Avanzado | Ilimitado, multi-país, guardrails por categoría, API para ERP propio | 600–1500 USD/mes + setup 5–10k USD |

## 10. Riesgos

**1. OCR extrae monto incorrecto de PDF escaneado de baja calidad.**
*Síntoma*: el agente aprueba automáticamente una factura por $4.500.000 pero el real era $45.000.000 (cero extra por escaneo borroso).
*Mitigación*: nunca aprobar automáticamente si `confidence_score < 0.90` para el campo de monto total. Además, validar que el monto en letras (cuando existe) coincida con el número.

**2. API DIAN/SAT no responde (caída del servicio).**
*Síntoma*: el flujo se detiene porque la validación fiscal no puede completarse.
*Mitigación*: la validación fiscal es un paso de enriquecimiento, no un bloqueante. Si la API está caída, la factura pasa a revisión humana con nota «validación fiscal pendiente». El SLA del proveedor de API es ~99.5%.

**3. Duplicado no detectado por variación en número de factura.**
*Síntoma*: el proveedor reenvía la factura con número ligeramente diferente («FE-891» vs «FE-0891»); pasa el check de duplicados y se paga dos veces.
*Mitigación*: además del número, comparar por `{proveedor_id, monto_total, fecha_emisión}` en ventana de ±3 días. Si hay match en los tres campos con número distinto → alerta de posible duplicado.

**4. Aprobación automática de ítem crítico con discrepancia pequeña.**
*Síntoma*: un medicamento vital tiene 2 unidades de diferencia; el sistema lo aprueba porque Δ < 3%.
*Mitigación*: el guardrail de SKU crítico es condicional al campo `categoria_criticidad` de cada SKU en el catálogo del tenant. Nunca basarse solo en el monto.

## 11. Variantes por industria

### Instancia 1 — Salud privada (`sanrafael`)

**Datos típicos**: 200–400 facturas/mes, mix de medicamentos (alta frecuencia, montos medios), dispositivos médicos (baja frecuencia, montos altos), servicios de mantenimiento técnico.

**Delta determinístico**: los medicamentos tienen código INVIMA (Colombia) o COFEPRIS (México) registrado. Validar que el código en la factura coincida con el del catálogo maestro del hospital — regla cerrada que ningún OCR genérico hace.

**Delta agéntico**: servicio de mantenimiento facturado con descripción libre («Mantenimiento preventivo equipo Rayos-X sala 3»): el modelo decide si corresponde a la OT abierta sin número de referencia en la factura.

**Guardrail duro**: cualquier factura de medicamento controlado (psicotrópicos, estupefacientes) requiere firma digital del Jefe de Farmacia. El agente no puede aprobar; solo puede preparar el expediente.

**Precio orientativo**: 400–1000 USD/mes; setup 5–8k USD para carga del catálogo INVIMA/COFEPRIS.

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 60–120 facturas/mes de insumos perecederos, bebidas, servicios de limpieza. Alta proporción de proveedores pequeños que no emiten CFDI o e-doc; usan recibo de caja manual o PDF básico.

**Delta determinístico**: muchos proveedores locales emiten en papel; el flujo es foto WhatsApp → OCR → validación básica (NIT activo en DIAN/SAT). La validación de factura electrónica no aplica para régimen simplificado en Colombia.

**Delta agéntico**: el proveedor cobra un «incremento de precio» de temporada no en el contrato marco. El modelo revisa si hay correo de aprobación o nota en el chat del proveedor que justifique el cambio antes de marcarlo como discrepancia.

**Regulación**: en Colombia, proveedor de alimentos bajo régimen simplificado puede emitir documento equivalente (tiquete POS). El agente reconoce este formato y lo procesa con flujo simplificado (sin validación DIAN).

**Precio orientativo**: 150–300 USD/mes.

## 12. Módulos técnicos relacionados

- **A06** (dataclasses y Pydantic): `InvoiceExtract` es el modelo Pydantic de salida del OCR; `ThreeWayMatchResult` encapsula el resultado del match con todos los campos de diferencia.
- **B02** (4 capas FastAPI): `POST /invoices/process` llama al servicio de procesamiento; el repo persiste el `InvoiceRecord` con su estado (`auto_approved | pending_review | rejected`).
- **C01** (SQLAlchemy async): tabla `invoice_records` con `tenant_id`, `status`, `discrepancy_type`; índice compuesto `(tenant_id, proveedor_id, numero_factura)` para el check de duplicados.
- **E01** (Anthropic SDK + tools): la resolución de discrepancias es el ejemplo de razonamiento multi-paso con tool-use: el modelo consulta la PO, consulta el historial del proveedor, produce la hipótesis.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Parsing XML CFDI / e-doc DIAN | determinístico | Formato estructurado con schema publicado; xpath directo. |
| OCR de PDF escaneado | determinístico | Biblioteca + modelo pre-entrenado; sin razonamiento. |
| Validación NIT activo en DIAN/SAT | determinístico | API pública con respuesta binaria. |
| 3-way match monto + cantidades + proveedor | determinístico | Regla aritmética cerrada con tolerancia configurable. |
| «Guantes nitrilo M» ↔ «Guantes de nitrilo talla M x100» — ¿mismo ítem? | agéntico | Variación libre de nomenclatura entre catálogos; sin regla cerrada. |
| Clasificar si diferencia es flete legítimo vs. error vs. cambio de precio | agéntico | Requiere contexto: correos, historial, tipo de proveedor. |
| Redacción de consulta al proveedor | agéntico | Salida para humano; debe ser específica y no acusatoria. |

## 13. Errores típicos

**1. OCR extrae tabla de la factura pero mezcla líneas.**
*Síntoma*: la cantidad del ítem 2 aparece como precio del ítem 1 porque el OCR confundió columnas en un PDF con layout no estándar.
*Causa*: el modelo de Document AI/Textract no detectó correctamente los límites de celdas en tablas sin bordes visibles.
*Arreglo*: activar el modo «Form Parser» de Document AI que usa coordenadas de bounding boxes, no solo texto secuencial. Siempre verificar que la suma de las líneas extraídas igual el total de la factura antes de proceder.

**2. Duplicado no detectado porque el proveedor cambió el número de factura.**
*Síntoma*: se paga dos veces la misma factura.
*Causa*: el check de duplicados solo comparó por número de factura.
*Arreglo*: check compuesto `(proveedor_id, monto, fecha ± 3 días)`. Ver sección 10.

**3. Guardrail de SKU crítico ignorado por cambio en el catálogo.**
*Síntoma*: un medicamento crítico fue reclasificado de `CRITICO` a `NORMAL` por error en el ERP y el sistema lo aprueba automáticamente.
*Causa*: el pipeline lee la categoría del ERP en tiempo real sin validación adicional.
*Arreglo*: mantener una lista propia de SKUs críticos en la configuración del tenant, separada del ERP, con aprobación de dos personas para modificarla.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame qué es el 3-way match con un ejemplo de una factura de medicamentos de Clínica San Rafael.»
2. **Aplícalo a mi caso**: «Mis proveedores en México usan CFDI. ¿Qué parte del pipeline cambia respecto al flujo de PDF escaneado?»
3. **Por qué falló**: «El agente aprobó automáticamente una factura con discrepancia de cantidad. ¿En qué nodo del workflow falló el guardrail?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de OCR diferenciado por formato (XML nativo, PDF digital, PDF escaneado).
- Implementar el 3-way match con tolerancias configurables por tenant y guardrails por categoría de SKU.
- Integrar la validación fiscal DIAN/SAT como paso determinístico sin bloquear el flujo ante caída del servicio.
- Definir exactamente qué discrepancias van al modelo y cuáles van directamente a revisión humana.
- Cotizar el servicio para salud o F&B con estructura de tiers por volumen de facturas.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A06   | `InvoiceExtract` y `ThreeWayMatchResult` son los modelos Pydantic de salida del OCR; el `Literal` de `status` (`auto_approved | pending_review | rejected`) usa los tipos restrictivos que A06 introduce. |
| B02   | El endpoint `POST /invoices/process` y el repo que persiste `InvoiceRecord` siguen la arquitectura de 4 capas; el patrón de servicio que orquesta parse + análisis + persistencia se aprende en B02 y se aplica aquí. |
| C01   | El índice compuesto `(tenant_id, proveedor_id, numero_factura)` para el check de duplicados y la tabla `invoice_records` con `tenant_id` son el patrón de SQLAlchemy async con RLS que C01 enseña. |
| C02   | Las facturas son datos sensibles del tenant; la política RLS que impide que un tenant acceda a las facturas de otro se implementa sobre `invoice_records` con el patrón que C02 establece. |
| E01   | La resolución multi-paso de discrepancias — el modelo consulta la PO, consulta el historial del proveedor y produce la hipótesis — es el ejemplo de razonamiento con tool-use encadenado del SDK de Anthropic. |
