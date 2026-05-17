---
ext_id: F-CMP-02
slug: evaluacion-proveedores
track: F
dept: CMP
ord: 142
title: "Evaluación trimestral de proveedores (KPI scorecards)"
summary: "Calcula automáticamente OTD, defect rate y variación de precio por proveedor, detecta patrones de degradación temprana y genera feedback accionable con tono profesional."
related_modules: [B02, C01, D04, E01]
industries_instanced: [retail, logistica]
tenants_in_examples: [tiendabox, expreslog]
big_corp_vendors: [SAP Ariba SLP, Coupa, Ivalua]
latam_tools: [excel, world_office, siigo-ordenes-compra]
key_concepts: [OTD, defect-rate, price-stability, scorecard, degradación-temprana, escalamiento]
estimated_minutes: 45
deterministic_share: 0.4
version: 1
---

## 1. Problema operativo

La directora de compras de TiendaBox Retail tiene 40 proveedores activos. Cada trimestre pasa dos días cruzando fechas prometidas vs. fechas de entrega en Excel, revisando notas de devolución en el ERP, y escribiendo correos individuales a los proveedores con peor desempeño. No tiene tiempo de detectar al proveedor que aún cumple el SLA pero cuyo OTD bajó 8 puntos en tres meses seguidos — señal de un problema que llegará en el trimestre siguiente. Necesita el scorecard calculado en minutos y los correos de feedback listos para revisar antes de enviar.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **SAP Ariba SLP** (Supplier Lifecycle & Performance) | Perfil centralizado del proveedor, KPIs automáticos desde S/4HANA, alertas de degradación, portal del proveedor para auto-reporte | Dentro del bundle Ariba, 20k–150k USD/año módulo SLP |
| **Coupa** | Supplier Risk & Performance con scoring configurable, integración con Dun & Bradstreet para riesgo financiero, flujos de acción automáticos | 50k–500k USD/año total plataforma |
| **Ivalua** | Evaluación 360° con cuestionarios al proveedor, gestión de riesgo de terceros, trazabilidad completa | Licencia enterprise, 100k–400k USD/año |

El patrón big corp: los KPIs se calculan desde el ERP transaccional en tiempo real. El feedback al proveedor se gestiona dentro del portal. PYME no tiene nada de eso integrado.

## 3. PYME LATAM realista

TiendaBox extrae el historial de órdenes de compra de World Office a un Excel manual cada trimestre. Expreslog usa un cuaderno de novedades en Notion para registrar entregas tardías. Ninguno tiene un campo «motivo de devolución» estructurado; está en el campo de notas libre del ERP. La evaluación trimestral es una reunión con el gerente de operaciones donde alguien pega tablas en PowerPoint.

El agente no reemplaza la reunión: la hace productiva. El análisis ya está hecho cuando empieza.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Órdenes de compra | Excel exportado de World Office / Siigo | Trimestral (pull) | 200–2000 órdenes/trimestre |
| Recepciones de mercancía | Excel o tabla ERP con fecha real de entrega | Trimestral | mismas filas |
| Notas de devolución / no-conformidades | Campo texto libre en ERP o hoja separada | Por evento | 5–50 registros/trimestre |
| Historial de precios por proveedor | Excel de compras con precio pactado vs. facturado | Trimestral | 200–2000 líneas |

**Ejemplo de fila de entrada:**

| po_id | proveedor | fecha_prometida | fecha_entrega_real | cantidad | cantidad_aceptada | precio_po | precio_facturado |
|-------|-----------|-----------------|--------------------|----------|-------------------|-----------|------------------|
| OC-2026-0341 | Textiles Andina | 2026-01-15 | 2026-01-18 | 500 | 498 | 12.50 | 12.50 |

## 5. Tramos determinísticos

1. **Cálculo de OTD (On-Time Delivery)**: `OTD = órdenes con fecha_real ≤ fecha_prometida / total órdenes`. Por proveedor, por mes dentro del trimestre. Regla cerrada.
2. **Cálculo de defect rate**: `defect_rate = (cantidad - cantidad_aceptada) / cantidad`. Agrupado por proveedor.
3. **Cálculo de variación de precio**: `Δprecio = (precio_facturado - precio_po) / precio_po`. Si `Δprecio > umbral_tenant` (configurable, default 2%), flag.
4. **Scoring compuesto**: `score = w_otd × OTD_norm + w_defect × (1 - defect_rate) + w_price × (1 - |Δprecio|_norm)`. Pesos configurados por tenant.
5. **Clasificación automática**: proveedor en cuartil inferior → `status: en_observacion`; en cuartil inferior dos trimestres seguidos → `status: alerta`.
6. **Detección de tendencia**: regresión lineal simple sobre los últimos 3 trimestres de OTD por proveedor. Si `pendiente < -0.05`, flag de «degradación temprana» aunque el score absoluto sea aceptable.

## 6. Tramos agénticos

1. **Clasificación de texto libre de devoluciones**: el campo de notas del ERP contiene cosas como «producto llegó húmedo», «empaque roto», «talla incorrecta». El modelo clasifica en categorías: `calidad_producto | empaque | logística | error_pedido`. Justificación: el texto libre no tiene vocabulario controlado; sin modelo es un regex frágil que falla ante sinónimos y errores ortográficos.
2. **Identificación de patrones de degradación**: el modelo recibe la serie histórica de KPIs del proveedor y detecta si hay un patrón que los números por sí solos no revelan (ej: OTD cae solo en diciembre → capacidad estacional, no problema estructural; vs. OTD cae en todas las categorías del mismo proveedor → señal de problema operativo real). Justificación: requiere razonamiento sobre contexto temporal.
3. **Redacción de feedback al proveedor**: el modelo produce un correo profesional con los hallazgos específicos, sin tono acusatorio, con expectativas claras para el próximo trimestre. Justificación: salida para humano; el tono y la especificidad contextual no son formulables como plantilla fija.

> [!nota]
> El correo que genera el agente **pasa siempre por revisión del comprador** antes de enviarse. El `send_email` tiene `requires_confirmation: true`. El modelo propone; el humano decide.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_data] → carga órdenes, recepciones y devoluciones del tenant (determinístico, tools: fetch_excel, erp_fetch_transactions)
  ↓
[compute_kpis] → OTD, defect rate, Δprecio por proveedor (determinístico)
  ↓
[detect_trend] → regresión lineal histórica, flags de degradación temprana (determinístico)
  ↓
[score_providers] → scoring compuesto, clasificación en cuartiles (determinístico)
  ↓
[classify_returns] → clasificar texto libre de devoluciones (agéntico, tool: sql_query notas ERP)
  ↓
[analyze_patterns] → identificar patrones anómalos en la serie histórica (agéntico)
  ↓
[draft_feedback] → redactar correo de feedback por proveedor en_observacion/alerta (agéntico)
  ↓
[human_review] → comprador revisa scorecards y correos antes de enviar (siempre)
  ↓
[send_email + write_report] → envío a proveedores + reporte interno (determinístico, tool: send_email, write_report)
  ↓
END
```

**Tools necesarias:**

- `fetch_excel` — exportaciones de World Office/Siigo
- `erp_fetch_transactions` — pull directo si el ERP tiene API
- `sql_query` — historial de evaluaciones anteriores del tenant
- `send_email` — feedback a proveedor (requiere confirmación)
- `write_report` — scorecard consolidado en PDF

## 8. Salida y entrega

1. **Scorecard por proveedor** (tabla con OTD, defect rate, Δprecio, score, tendencia, status).
2. **Ranking de proveedores** del trimestre con semáforo: verde/amarillo/rojo.
3. **Correos de feedback** (uno por proveedor en observación o alerta), listos para revisar.
4. **Resumen ejecutivo** de 1 página para la reunión de compras con los 3 principales hallazgos.

Canal: descarga PDF/XLSX desde la app + borradores de correo en panel de revisión.

**Mockup de scorecard:**

| Proveedor | OTD | Defect rate | Δprecio | Score | Tendencia OTD | Status |
|-----------|-----|------------|---------|-------|---------------|--------|
| Textiles Andina | 94% | 0.4% | +0.5% | 88 | ↗ estable | ✓ OK |
| Empaques Sur | 78% | 1.2% | +3.1% | 61 | ↘ degradando | ⚠ Observación |
| Plastipack Ltda | 71% | 2.8% | +5.4% | 44 | ↘↘ cayendo | 🔴 Alerta |

## 9. Cómo se vende

**Gancho**: «Tu evaluación trimestral que hoy toma 2 días la tienes lista en 20 minutos, con los correos de feedback ya redactados para revisar.»

**Diferencial**: detección de degradación *antes* de que el proveedor incumpla el SLA — en LATAM esto es crítico porque cambiar de proveedor tarda 4–8 semanas.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 20 proveedores, KPIs automáticos, scorecard PDF | 100–200 USD/mes |
| Estándar | Hasta 60 proveedores, tendencia histórica, correos redactados | 200–450 USD/mes |
| Avanzado | Ilimitado, integración API ERP, golden set propio, portal proveedor básico | 450–900 USD/mes + setup 3–6k USD |

## 10. Riesgos

**1. Clasificación incorrecta de devolución.**
*Síntoma*: el modelo clasifica «caja llegó mojada» como `calidad_producto` en vez de `logística`; el proveedor recibe feedback incorrecto.
*Mitigación*: golden set de 30–50 ejemplos reales del cliente para validar la clasificación antes del primer despliegue. Cualquier clasificación con `confianza < 0.7` va a revisión.

**2. Degradación temprana falsa positiva.**
*Síntoma*: el sistema marca a un proveedor excelente como «degradando» por una caída estacional conocida (diciembre, temporada de cosecha).
*Mitigación*: declarar `excluded_months` por tenant (ej: diciembre para retail). El modelo también recibe el contexto de temporada para su análisis de patrones.

**3. Correo de feedback enviado sin revisión.**
*Síntoma*: el comprador activa «envío automático» y un correo agresivo o con datos incorrectos llega al proveedor.
*Mitigación*: `send_email` no disponible en modo automático. La confirmación es un paso UI explícito, no un checkbox.

**4. Datos de órdenes incompletos (ERP sin campo de fecha real de entrega).**
*Síntoma*: el OTD calculado es 100% porque el ERP nunca registró fechas tardías.
*Mitigación*: validar en ingest que `fecha_entrega_real` no sea idéntica a `fecha_prometida` en más del 80% de las filas. Si sí, alertar que los datos de entrada son probablemente incorrectos.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 30–60 proveedores, mix de ropa + electrónico + hogar, alta variación estacional (temporadas), devoluciones frecuentes de clientes que rebotan al proveedor.

**Delta determinístico**: devolución de cliente ≠ devolución de proveedor. Filtrar solo las no-conformidades generadas en recepción, no en post-venta. Regla de negocio clara.

**Delta agéntico**: proveedor con OTD degradando solo en SKUs de una categoría específica → ¿problema de capacidad de esa línea de producción o cambio de política de ese proveedor? El modelo analiza el patrón a nivel SKU × proveedor.

**Regulación**: en Colombia, retenciones en la fuente aplicables a algunos proveedores (Resolución DIAN). El sistema verifica que el RUT del proveedor esté activo en DIAN antes de aprobar el pago de facturas.

**Precio orientativo**: 200–450 USD/mes.

### Instancia 2 — Logística / 3PL (`expreslog`)

**Datos típicos**: proveedores son principalmente transportistas y operadores de almacenaje. KPIs distintos: SLA de entrega last-mile (< 24h / < 48h), daño en tránsito, devoluciones al remitente.

**Delta determinístico**: OTD se mide en horas, no días. Umbral configurable por tipo de servicio (`express: 24h`, `standard: 72h`). El cálculo es el mismo; solo cambia la granularidad.

**Delta agéntico**: transportista que cumple SLA en zona urbana pero falla en zona rural → el modelo identifica la segmentación geográfica sin que el comprador tenga que armar el pivot manualmente.

**Regulación**: en Colombia, operadores de carga aéreo/terrestre deben estar habilitados ante Ministerio de Transporte. Validación automática contra Registro Nacional de Transporte.

**Precio orientativo**: 150–350 USD/mes; setup 2–3k USD para integración con TMS propio.

## 12. Módulos técnicos relacionados

- **B02** (4 capas FastAPI): el scorecard se persiste como `SupplierEvaluation` en la capa repo; el endpoint `GET /suppliers/{id}/scorecard` lo sirve al frontend.
- **C01** (SQLAlchemy async): las evaluaciones históricas viven en `supplier_evaluations` con `tenant_id`; la consulta de tendencia usa una window function sobre 4 trimestres.
- **D04** (Observabilidad Phoenix): cada llamada al modelo para clasificar devoluciones genera un span; si el `confidence_score` cae, la alerta aparece en el dashboard de Phoenix antes de que el cliente lo reporte.
- **E01** (Anthropic SDK + tools): la clasificación de texto libre es el ejemplo canónico de tool con output estructurado (`category: Literal[...]`, `confidence: float`).

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Cálculo de OTD, defect rate, Δprecio | determinístico | Fórmulas cerradas sobre datos estructurados. |
| Detección de tendencia (regresión lineal) | determinístico | Algoritmo estadístico determinista sobre la serie histórica. |
| Clasificación de texto libre de devoluciones | agéntico | Vocabulario abierto, sinónimos, errores ortográficos — sin regla cerrada. |
| Identificación de patrones temporales anómalos | agéntico | Requiere razonamiento sobre estacionalidad y contexto del negocio. |
| Redacción del correo de feedback al proveedor | agéntico | Salida para humano, tono profesional, contexto específico por proveedor. |

## 13. Errores típicos

**1. Comparar OTD entre proveedores de categorías distintas.**
*Síntoma*: el proveedor de perecederos parece el peor porque su SLA es 24h vs. 7 días del proveedor de mobiliario.
*Causa*: el cálculo no filtra por categoría o tipo de producto antes de comparar.
*Arreglo*: segmentar el scorecard por `category_group` del tenant; el ranking es dentro del grupo, no global.

**2. Tendencia calculada con solo 2 periodos.**
*Síntoma*: la regresión lineal dice «degradando» con dos puntos de datos; cualquier variación aleatoria parece tendencia.
*Causa*: el tenant tiene menos de 3 trimestres de historial.
*Arreglo*: si `n_periodos < 3`, no calcular tendencia; mostrar «historial insuficiente» en el scorecard.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame qué es OTD y por qué una caída de 8 puntos importa más que un valor absoluto de 78%.»
2. **Aplícalo a mi caso**: «Mi ERP no tiene campo de fecha de entrega real. ¿Cómo puedo adaptar el pipeline para usar las notas de recepción como fuente alternativa?»
3. **Por qué falló**: «El agente clasificó todas las devoluciones como `logística`. ¿Qué pudo salir mal y cómo lo corrijo?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Construir el pipeline de cálculo de KPIs de proveedor desde exportaciones de Excel/ERP.
- Implementar detección de degradación temprana con regresión lineal simple sobre la serie histórica.
- Diseñar el tramo agéntico de clasificación de texto libre con output estructurado y umbral de confianza.
- Establecer el flujo de revisión humana antes de enviar feedback a proveedores.
- Cotizar y dimensionar este servicio para retail o logística LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| B02   | El endpoint `GET /suppliers/{id}/scorecard` y la capa repo que persiste `SupplierEvaluation` siguen la arquitectura de 4 capas que esta ficha aplica directamente. |
| C01   | La window function sobre `supplier_evaluations` para calcular la tendencia de OTD en 4 trimestres es el ejemplo canónico de query analítica con SQLAlchemy async que se construye aquí. |
| D04   | El `confidence_score` de cada clasificación de devolución se traza en Phoenix; si cae por debajo del umbral, la alerta aparece antes de que el comprador reciba un correo de feedback incorrecto. |
| E01   | La clasificación de texto libre de devoluciones con `category: Literal[...]` y `confidence: float` es el ejemplo de tool-calling con output estructurado que se introduce en el módulo y se instancia aquí. |
| E05   | El schedule trimestral de evaluación de proveedores es un workflow Temporal durable e idempotente; E05 enseña exactamente el patrón `idempotency_key` que esta ficha reutiliza. |
