---
ext_id: F-CMP-01
slug: comparacion-cotizaciones
track: F
dept: CMP
ord: 141
title: "Comparación de cotizaciones (3+ proveedores) y recomendación"
summary: "Extrae ítems y precios de PDFs/Excels heterogéneos, normaliza unidades, aplica scoring multi-criterio y redacta la recomendación de compra con justificación auditada."
related_modules: [A06, B02, E01]
industries_instanced: [construccion, hospitalidad]
tenants_in_examples: [andina, mesonurbano]
big_corp_vendors: [Coupa, SAP Ariba, Jaggaer]
latam_tools: [excel, siigo-ordenes-compra, world_office]
key_concepts: [total-cost-of-ownership, scoring-multi-criterio, normalización-SKU, letra-chica, RFQ]
estimated_minutes: 45
deterministic_share: 0.5
version: 1
---

## 1. Problema operativo

El jefe de compras de Constructora Andina manda un RFQ a tres proveedores de materiales eléctricos. Recibe tres archivos distintos: uno en PDF con tabla de precios escaneada, otro en Excel con columnas en distinto orden, y un correo con lista de items pegada como texto. Consolidarlos a mano le toma medio día, y aún así pierde cláusulas de flete o garantía enterradas en notas al pie. Necesita una tabla comparativa lista en 15 minutos, con la recomendación documentada para auditoría interna.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **Coupa** | Portal de RFQ con templates predefinidos, proveedores suben en formulario estructurado, análisis automático | 50k–500k USD/año; implementación 3–6 meses |
| **SAP Ariba Sourcing** | Eventos de RFQ, reverse auction, integración con S/4HANA, scoring configurable | Dentro del bundle SAP, 100k–2M USD/año |
| **Jaggaer One** | RFQ + análisis de escenarios, fuerte en manufactura compleja y pública | Licencia enterprise, 80k–400k USD/año |

La clave del modelo big corp: los proveedores cargan en un **portal estructurado**. El problema de formatos heterogéneos no existe porque el formato lo impone la plataforma. Una PYME no puede forzar eso a sus proveedores.

## 3. PYME LATAM realista

Andina y Mesón Urbano viven en el mismo ciclo: el comprador reenvía un correo con la lista de items, el proveedor responde en el formato que quiere. El resultado son tres o cuatro archivos incompatibles. La consolidación ocurre en un Excel manual que tarda horas y no tiene trazabilidad. Siigo Compras y World Office permiten registrar la orden de compra ganadora, pero no ayudan en la comparación previa.

El problema real no es el análisis: es la **normalización**. Dos proveedores pueden cotizar el mismo cable como «Cable THHN 12 AWG x metro» y «THHN-12 m (rollo 100m)»; si el comprador no lo detecta, compara peras con manzanas.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Cotización proveedor A | PDF con tabla (escaneado o digital) | Por evento RFQ | 10–80 ítems |
| Cotización proveedor B | Excel `.xlsx`, columnas propias | Por evento RFQ | mismos ítems, otras columnas |
| Cotización proveedor C | Correo en texto / Word | Por evento RFQ | lista no estructurada |
| Lista de items solicitados | Excel maestro del comprador | Único por RFQ | 10–80 ítems con unidad y cantidad |

**Ejemplo de fila normalizada esperada:**

| item_id | descripcion_normalizada | proveedor_a_unit | proveedor_b_unit | proveedor_c_unit | unidad |
|---------|------------------------|------------------|------------------|------------------|--------|
| E-014 | Cable THHN 12 AWG | 850 | 870 | 840 | COP/m |

## 5. Tramos determinísticos

1. **Extracción de PDF digital**: con `pdfplumber` o Google Document AI (Vertex AI) extraer filas de tabla donde `confidence > 0.85`. Resultado: lista de `{descripcion_raw, cantidad, precio_unitario, unidad_raw}`.
2. **Extracción de Excel**: `openpyxl` + detección de fila de encabezado por heurística (primera fila con ≥ 4 celdas no vacías). Normalizar columnas por nombre fuzzy contra esquema canónico.
3. **Normalización de unidades**: tabla de conversiones fijas (`"rollo 100m" → precio/m = precio/100`). Sin modelo: regla cerrada.
4. **Construcción de tabla comparativa**: join por `item_id` entre la lista maestra y las tres cotizaciones. Celdas faltantes → `null` (no imputar).
5. **Scoring determinístico**: aplicar pesos configurados por el tenant (`precio: 50%, plazo: 30%, calidad_historica: 20%`) con fórmula lineal. Producir `score_total` por proveedor.
6. **Detección de inconsistencias obvias**: precio fuera de rango ± 3σ histórico → flag automático sin modelo.

## 6. Tramos agénticos

1. **Resolución de ambigüedad de SKU**: el modelo recibe pares `(descripcion_lista_maestra, descripcion_cotizacion)` y decide si son el mismo ítem. Ejemplo concreto: `"TUBO PVC 1/2 PULG x 6M"` vs `"TUBO 1/2\" PVC 6 METROS"` — sin regla cerrada porque la variación de escritura es libre. El modelo produce `{match: true/false, confianza: high/medium/low, razon}`. Si `confianza == low`, va a fallback humano.
2. **Detección de «letra chica»**: el modelo lee el texto completo de cada cotización PDF (no solo la tabla) y extrae condiciones que cambian el TCO: costos de flete, garantía de días vs meses, condiciones de pago a 30/60/90, cláusulas de escalada de precio. Justificación: estas condiciones no tienen campo estructurado; son prosa libre.
3. **Redacción de la recomendación**: el modelo genera un párrafo por proveedor y un párrafo de recomendación final, citando los factores de scoring y las alertas de letra chica. Salida para que el jefe de compras revise y apruebe antes de emitir la orden.

> [!cuidado]
> El modelo **no emite la orden de compra**. Solo redacta la recomendación. La aprobación y la creación en Siigo/World Office las hace el comprador.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_rfq] → descarga los 3 archivos del bucket del tenant (determinístico)
  ↓
[extract_items] → extracción PDF + Excel + texto (determinístico, tools: parse_invoice_pdf, fetch_excel)
  ↓
[normalize_units] → tabla de conversiones fijas (determinístico)
  ↓
[resolve_sku_ambiguity] → loop agéntico por pares dudosos (agéntico, tool: sql_query catálogo)
  ↓
[build_comparison_table] → join items × proveedores (determinístico)
  ↓
[detect_fine_print] → extracción de condiciones en texto libre (agéntico)
  ↓
[score_providers] → scoring lineal con pesos del tenant (determinístico)
  ↓
[draft_recommendation] → redacción párrafo por proveedor + conclusión (agéntico)
  ↓
[human_review] → interrupt_before: comprador aprueba o edita (siempre)
  ↓
[write_report] → persiste tabla + recomendación como PDF/XLSX (determinístico, tool: write_report)
  ↓
END
```

**Tools necesarias:**

- `parse_invoice_pdf` — extracción de cotizaciones en PDF
- `fetch_excel` — cotizaciones en Excel
- `sql_query` — catálogo maestro de ítems del tenant, historial de precios
- `write_report` — output en PDF o XLSX para el archivo de compras

## 8. Salida y entrega

El agente entrega:

1. **Tabla comparativa** (XLSX o tabla Markdown) con columnas: ítem | unidad | precio_A | precio_B | precio_C | precio_mínimo | score_A | score_B | score_C | alertas.
2. **Reporte de letra chica**: lista de condiciones detectadas por proveedor que impactan el TCO, con cita textual del fragmento original.
3. **Párrafo de recomendación** listo para pegar en el correo de aprobación interna.

Canal: descarga directa desde la app + envío opcional por `send_email` al jefe de compras.

**Mockup de tabla:**

| Ítem | Unidad | Proveedor A | Proveedor B | Proveedor C | Score |
|------|--------|-------------|-------------|-------------|-------|
| Cable THHN 12 AWG | COP/m | 850 | 870 | 840 ✓ | A:72 B:68 C:74 |
| Tubo conduit 1" | COP/m | 1200 | — | 1180 ✓ | A:65 B:n/a C:71 |
| ⚠ Flete no incluido | — | Proveedor A cobra $80k adicional en pedidos < $2M | — | — | — |

## 9. Cómo se vende

**Gancho**: «Tus cotizaciones llegan en tres formatos distintos. El agente las unifica, detecta la letra chica y te da la recomendación en 15 minutos, no en medio día.»

**Propuesta de valor diferencial**: trazabilidad completa (qué extrajeron, qué emparejaron, qué alertaron) lista para auditoría interna de compras.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 3 proveedores, 50 ítems/RFQ, report XLSX | 150–300 USD/mes |
| Estándar | Hasta 6 proveedores, 200 ítems/RFQ, letter-chica, historial | 300–600 USD/mes |
| Avanzado | Multi-divisa, integración API Siigo/World Office, golden set propio | 600–1200 USD/mes + setup 3–5k USD |

## 10. Riesgos

**1. Falso positivo en resolución de SKU.**
*Síntoma*: el agente dice que dos ítems distintos son el mismo; el comprador aprueba sin revisar y compra el producto equivocado.
*Mitigación*: todo match con `confianza != high` va a revisión humana obligatoria. El comprador puede override con un click y el feedback entra al golden set.

**2. Extracción fallida en PDF escaneado de baja calidad.**
*Síntoma*: la tabla sale vacía o con celdas corruptas; el agente intenta comparar con datos incompletos.
*Mitigación*: validar que `confidence_score` promedio > 0.80 antes de continuar. Si no, interrumpir y pedir al usuario que suba una versión digital o re-escanee a 300 DPI.

**3. Cotización con precios en moneda distinta sin declarar.**
*Síntoma*: precio en USD mezclado con COP sin conversión; el scoring queda corrupto.
*Mitigación*: detectar símbolo de moneda en la extracción. Si el tenant es Colombia y aparece «$» junto a números menores a 10, asumir USD y alertar para confirmación antes de convertir.

**4. Uso de la recomendación sin revisión (automatización excesiva).**
*Síntoma*: el comprador configura «auto-emitir orden» basado en el score; el modelo comete un error y se emite una orden incorrecta.
*Mitigación*: `human_review` es no-removible en el workflow. La app no expone opción de auto-aprobación en el tier básico.

## 11. Variantes por industria

### Instancia 1 — Construcción (`andina`)

**Datos típicos**: cotizaciones de 20–80 ítems (materiales, equipos, subcontratos), proveedores regionales sin portal digital, PDFs escaneados frecuentes, precios en COP con IVA separado.

**Delta determinístico**: IVA en Colombia es 19%; validar que cada precio venga con IVA desglosado o aplicar el 19% al neto según declaración del proveedor. Regla cerrada, sin modelo.

**Delta agéntico**: detectar si el subcontratista cotiza con o sin «prestaciones sociales» incluidas en la mano de obra — diferencia de ~52% sobre el valor neto. El modelo lee la prosa del documento para determinarlo.

**Regulación**: registro en Colombia Compra Eficiente si el cliente es contratista del Estado. Mantener evidencia de comparación de cotizaciones (Decreto 1082/2015).

**Precio orientativo**: 200–500 USD/mes; setup inicial 2–4k USD para ingesta del catálogo de ítems propios.

### Instancia 2 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: cotizaciones semanales de insumos perecederos (carnes, vegetales, lácteos) a 5–15 proveedores, volúmenes pequeños, precios con alta variabilidad estacional, entregadas por WhatsApp como foto o PDF.

**Delta determinístico**: frecuencia semanal → pipeline programado con trigger en lunes 8am; umbral de precio ± 15% sobre la semana anterior dispara alerta automática sin modelo.

**Delta agéntico**: proveedor nuevo sin historial de calidad → el modelo evalúa si las condiciones de la cotización son suficientemente competitivas para arriesgar el cambio, considerando el impacto en la homogeneidad del plato (ingredientes con origen conocido).

**Regulación**: en Colombia/México, facturas de alimentos deben cumplir trazabilidad INVIMA/SENASICA. El agente verifica que el proveedor esté en el registro activo (consulta API pública).

**Precio orientativo**: 100–250 USD/mes; sin setup especial si el tenant usa Siigo o Alegra.

## 12. Módulos técnicos relacionados

- **A06** (dataclasses y Pydantic): el modelo `QuotationItem` y `ComparisonRow` viven como dataclasses tipadas; la validación de unidades usa un `Literal` de Pydantic.
- **B02** (4 capas FastAPI): el endpoint `POST /rfq/{rfq_id}/compare` llama al servicio de comparación; el repo persiste el resultado como `ComparisonReport`.
- **E01** (Anthropic SDK + tools): la resolución de SKU y la detección de letra chica son el primer ejemplo de tool-calling con respuesta estructurada (`match: bool, razon: str`).

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Extracción de tabla desde PDF/Excel | determinístico | Biblioteca + reglas de layout; salida es JSON estructurado. |
| Normalización de unidades (kg↔lb, m↔rollo) | determinístico | Tabla de conversiones fija del tenant. Regla cerrada. |
| Emparejamiento «Cable THHN 12 AWG» ↔ «THHN-12 m» | agéntico | Variación libre de escritura entre proveedores; no existe regla cerrada. |
| Scoring lineal con pesos del tenant | determinístico | Fórmula definida; reproducible. |
| Detección de cláusulas de flete/garantía en prosa | agéntico | Texto libre sin campo estructurado; requiere comprensión semántica. |
| Redacción de la recomendación final | agéntico | Salida para humano; debe integrar contexto, tono y evidencia. |

## 13. Errores típicos

**1. Comparar sin normalizar unidades.**
*Síntoma*: el proveedor C parece 100x más caro porque cotizó por rollo de 100 m y los otros por metro.
*Causa*: el pipeline no aplicó la conversión de unidades antes del join.
*Arreglo*: validar que `unidad_normalizada` esté poblada en todas las filas antes de construir la tabla comparativa; si hay `null`, interrumpir.

**2. SKU resuelto con confianza «medium» aprobado automáticamente.**
*Síntoma*: en producción se compra un item ligeramente distinto; el proveedor entrega algo que no aplica.
*Causa*: el harness tenía `auto_approve_medium = True` que alguien activó para acelerar el flujo.
*Arreglo*: eliminar el flag; `medium` siempre va a revisión humana. Documentar en el golden set.

**3. PDF escaneado rotado 90°.**
*Síntoma*: Google Document AI extrae basura; la tabla sale vacía.
*Causa*: el escáner rotó la página; el OCR no detectó el texto en orientación incorrecta.
*Arreglo*: activar `autoRotate: true` en la llamada a Document AI, o pre-procesar con `pypdf` para normalizar orientación.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame la diferencia entre tramo determinístico y agéntico con un ejemplo distinto al de las cotizaciones.»
2. **Aplícalo a mi caso**: «Cómo adaptaría este workflow si mis proveedores me mandan las cotizaciones por WhatsApp como imagen JPEG.»
3. **Por qué falló**: «El agente emparejó dos ítems distintos como si fueran el mismo. ¿En qué parte del workflow ocurrió y cómo lo prevengo?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Diseñar el pipeline de extracción desde formatos heterogéneos (PDF, Excel, texto) hasta tabla comparativa normalizada.
- Identificar exactamente qué tramos son determinísticos (normalización, scoring) y cuáles son agénticos (resolución de SKU, letra chica).
- Configurar el scoring multi-criterio con pesos por tenant sin hardcodear ningún valor.
- Implementar el fallback humano obligatorio antes de emitir cualquier recomendación.
- Dimensionar y cotizar este servicio para una PYME de construcción o F&B.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A06   | `QuotationItem` y `ComparisonRow` son dataclasses Pydantic; el `Literal` de unidades es el primer uso real de tipos restrictivos que aquí validan la normalización de SKU. |
| B02   | El endpoint `POST /rfq/{rfq_id}/compare` sigue la arquitectura de 4 capas; el repo que persiste `ComparisonReport` es el patrón que se implementa directamente en esta ficha. |
| C02   | El `rfq_id` y el catálogo de ítems son datos del tenant; la política RLS que aísla cotizaciones entre tenants se implementa sobre la tabla `comparison_reports`. |
| E01   | La resolución de SKU ambiguo y la detección de letra chica son los primeros ejemplos de tool-calling con output estructurado (`match: bool, razon: str`) del SDK de Anthropic. |
| D04   | Cada llamada al modelo para resolver un par de SKUs genera un span en Phoenix; el `confidence_score` del match se convierte en la métrica de calidad que dispara alertas antes de que el comprador lo detecte. |
