---
ext_id: F-OPS-03
slug: optimizacion-inventario
track: F
dept: OPS
ord: 163
title: "Optimización de inventario (stock-out vs sobrestock)"
summary: "Calcula ROP, safety stock y EOQ por SKU con clasificación ABC-XYZ; el agente detecta SKUs con patrones anómalos que rompen los supuestos estadísticos y recomienda acción — con guardrail duro para medicamentos y SKUs críticos."
related_modules: [A06, C01, E01]
industries_instanced: [retail, salud]
tenants_in_examples: [tiendabox, sanrafael]
big_corp_vendors: [Blue Yonder, ToolsGroup, RELEX]
latam_tools: [excel, world_office, siigo-ordenes-compra]
key_concepts: [ROP, safety-stock, EOQ, ABC-XYZ, días-de-inventario, coeficiente-de-variación, guardrail-crítico]
estimated_minutes: 45
deterministic_share: 0.7
version: 1
---

## 1. Problema operativo

La jefa de logística de TiendaBox Retail tiene 280 SKUs activos. Cada mes descubre el problema demasiado tarde: un SKU de alta rotación se agotó tres días antes del reabastecimiento, perdiendo 40 ventas. Otro SKU de temporada pasada tiene 6 meses de stock; el capital inmovilizado es de $12.000 USD. No tiene tiempo de revisar los 280 SKUs: revisa los que le gritan. En Clínica San Rafael, el problema tiene consecuencia directa en el paciente: un medicamento crítico sin stock es una crisis operativa. El jefe de farmacia necesita saber con 72 horas de anticipación si algún medicamento está por debajo del safety stock, no cuando ya hay faltante.

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|--------|----------|-------------------|
| **Blue Yonder** (antes JDA) | Inventory optimization con ML, demand sensing, repositioning automático entre almacenes | Desde 100k USD/año; impl. 200k–500k USD |
| **ToolsGroup** | Demand-driven inventory, service level optimization, probabilistic forecasting | 50k–300k USD/año |
| **RELEX Solutions** | Replenishment + inventory optimization para retail y supply chain, ML nativo | 100k–500k USD/año |

El modelo big corp: optimización continua en tiempo real con señales de POS, repositioning automático entre tiendas. PYME tiene un Excel con fórmulas PROMEDIO que alguien actualiza cuando tiene tiempo.

## 3. PYME LATAM realista

TiendaBox tiene el historial de ventas en World Office pero calcula el «punto de pedido» manualmente en Excel, generalmente como «cuando queda stock para 2 semanas». Siigo Compras puede generar una alerta cuando el inventario baja de X unidades, pero ese X lo puso alguien hace 2 años y no se actualiza. Clínica San Rafael usa un módulo básico de farmacia integrado al ERP que tiene alertas de stock mínimo, pero los mínimos son fijos y no se ajustan a la variabilidad de consumo.

La oportunidad: calcular ROP y safety stock estadísticamente correcto toma 10 líneas de código. Lo que ningún sistema PYME hace es detectar que un SKU ya no cumple los supuestos del cálculo.

## 4. Datos típicos

| Fuente | Formato | Frecuencia | Volumen típico |
|--------|---------|------------|----------------|
| Historial de ventas/consumo por SKU | Excel exportado de ERP | Mensual | 12–24 meses, 50–500 SKUs |
| Inventario actual | Excel o tabla ERP actualizada diariamente | Diaria | mismos SKUs |
| Lead time por proveedor por SKU | Excel maestro o tabla de compras | Estático (actualización trimestral) | mismos SKUs |
| Costo unitario y costo de orden | Excel de compras / catálogo ERP | Estático | mismos SKUs |
| Clasificación de criticidad | Catálogo del tenant (manual) | Estático | para salud: categoría CRÍTICO/NORMAL |

**Ejemplo de fila de cálculo:**

| sku | demanda_media | std_demanda | lead_time_días | z_factor | safety_stock | ROP | EOQ | dias_inventario_actual |
|-----|--------------|-------------|----------------|----------|-------------|-----|-----|------------------------|
| MED-044 | 12 unid/día | 3.2 | 5 | 1.645 (95%) | 24 | 84 | 180 | 4.2 |

Con 4,2 días de inventario y ROP de 84 unidades, MED-044 ya está por debajo del punto de reorden.

## 5. Tramos determinísticos

1. **Clasificación ABC-XYZ**: A = top 80% de valor de consumo; X/Y/Z por coeficiente de variación (`CV = std/mean`). Determina qué nivel de servicio aplicar (`z_factor`): clase A-X usa 95% (z=1.645), clase C-Z usa 85% (z=1.04). Configurable por tenant.
2. **Cálculo de safety stock**: `SS = z × σ_L`, donde `σ_L = sqrt(lead_time × σ_d² + demand_mean² × σ_lt²)`. Si el lead time es estable, simplifica a `SS = z × σ_d × sqrt(LT)`. Todo determinístico dado los parámetros.
3. **Cálculo de ROP (Reorder Point)**: `ROP = demand_mean × lead_time + safety_stock`. Aritmética directa.
4. **Cálculo de EOQ (Economic Order Quantity)**: `EOQ = sqrt(2 × D × S / H)`, donde D = demanda anual, S = costo de orden, H = costo de mantener inventario. Fórmula cerrada.
5. **Cálculo de días de inventario actual**: `DI = stock_actual / demand_mean`. Si `DI < lead_time + z × (σ_d / demand_mean)`, el SKU está en zona de riesgo.
6. **Flags automáticos**: SKU con `stock_actual < ROP` → alerta de reorden. SKU con `DI > 3 × (LT + cobertura_objetivo)` → alerta de sobrestock. Estos flags son reglas cerradas sin modelo.

## 6. Tramos agénticos

1. **Detección de SKUs con patrón anómalo que rompe los supuestos**: el modelo estadístico asume que la demanda sigue una distribución Normal estacionaria. El agente detecta cuándo esto no se cumple:
   - SKU con demanda bimodal (vende mucho en semanas 1-2 y casi nada en 3-4 — ciclo de cobro LATAM).
   - SKU con shift de nivel reciente (paso de 20 a 80 unidades/semana en los últimos 2 meses — posible cambio de cliente o canal).
   - SKU con outliers de demanda que inflan `σ` artificialmente (una compra de volumen inusual).
   Justificación: detectar qué tipo de anomalía es y si se debe ajustar el modelo o los parámetros requiere razonamiento contextual; un test estadístico solo dice «hay anomalía», no «qué hacer con ella».
2. **Recomendación de acción para SKUs fuera de banda**: cuando un SKU clase A tiene 60 días de inventario cuando el objetivo es 30, el agente recomienda una acción específica: promoción para acelerar rotación, reducción de la próxima orden, negociación de devolución con el proveedor, o descontinuación. Justificación: la acción correcta depende de si el SKU es de temporada pasada, tiene fecha de vencimiento, tiene cláusulas de devolución con el proveedor — contexto que no está en los números.
3. **Evaluación de si un medicamento crítico puede reducirse** (con guardrail duro): para SKUs clase `CRÍTICO`, el agente puede identificar si el sobrestock es genuino (consumo bajó 50% y la tendencia es sostenida). Pero la recomendación de reducir el stock mínimo de un medicamento crítico **nunca se implementa automáticamente**: requiere sign-off explícito del Jefe de Farmacia con trazabilidad en el sistema.

> [!cuidado]
> **Guardrail duro para salud**: cualquier cambio de `stock_minimo` de un SKU con `criticidad == CRITICO` requiere aprobación humana explícita con registro de quién aprobó, cuándo y por qué. El agente puede recomendar; no puede ejecutar.

## 7. Blueprint del workflow

```
START
  ↓
[ingest_data] → inventario actual, historial de ventas, lead times, costos (determinístico, tools: fetch_excel, erp_fetch_transactions)
  ↓
[classify_abc_xyz] → segmentar por clase y asignar z_factor (determinístico)
  ↓
[compute_params] → safety stock, ROP, EOQ por SKU (determinístico)
  ↓
[compute_inventory_days] → DI actual, flags de reorden y sobrestock (determinístico)
  ↓
[detect_anomalous_patterns] → SKUs donde los supuestos estadísticos fallan (agéntico, tool: sql_query historial)
  ↓
[recommend_actions] → acción para cada SKU fuera de banda (agéntico)
  ↓
[human_review_critical] → sign-off obligatorio para cualquier cambio en SKU CRÍTICO (guardrail duro)
  ↓
[human_review_general] → responsable de inventario revisa y aprueba recomendaciones (siempre)
  ↓
[update_reorder_params] → actualizar ROP/SS aprobados en ERP/sistema (determinístico)
  ↓
[write_report] → reporte de inventario con acciones aprobadas (determinístico, tool: write_report)
  ↓
END
```

**Tools necesarias:**

- `fetch_excel` — inventario y ventas desde Excel
- `erp_fetch_transactions` — consumo desde ERP
- `sql_query` — historial de parámetros de inventario, clasificación de criticidad
- `write_report` — reporte de inventario mensual

## 8. Salida y entrega

1. **Tabla de parámetros de inventario** por SKU: safety stock, ROP, EOQ, DI actual, status (OK / reorden / sobrestock / crítico).
2. **Lista de alertas de reorden** lista para generar órdenes de compra.
3. **Lista de SKUs con sobrestock** con acción recomendada y justificación.
4. **Lista de SKUs anómalos** donde los supuestos del modelo no se cumplen, con diagnóstico y recomendación.
5. **Semáforo de inventario** — dashboard de estado global con % de SKUs en cada estado.

Canal: tabla en la app + alerta Slack/email para SKUs en estado crítico.

**Mockup de tabla de estado:**

| SKU | Descripción | DI actual | ROP | Safety Stock | Estado | Acción sugerida |
|-----|-------------|-----------|-----|-------------|--------|-----------------|
| MED-044 | Insulina glargina 100UI | 4.2 días | 84 unid | 24 unid | 🔴 CRÍTICO — por debajo de ROP | Emitir orden urgente |
| SKU-042 | Contenedor 5L ACME | 62 días | 180 unid | 40 unid | ⚠ Sobrestock (obj: 30 días) | Reducir próxima orden |
| SKU-117 | Auriculares BT | 18 días | 200 unid | 60 unid | ✓ OK | — |
| SKU-089 | Crema solar SPF50 | 8 días | 120 unid | 35 unid | ⚠ Reorden | Emitir OC esta semana |

## 9. Cómo se vende

**Gancho**: «Tu Excel de inventario te dice cuánto tienes. Este sistema te dice qué deberías tener, qué ya se pasó, y cuáles son los 5 SKUs donde tienes que actuar esta semana.»

**Diferencial en salud**: guardrail documentado para medicamentos críticos — el único argumento que necesita el Jefe de Farmacia para aprobar el sistema ante su dirección médica.

| Tier | Incluye | Precio orientativo |
|------|---------|-------------------|
| Básico | Hasta 100 SKUs, ROP/SS/EOQ, alertas de reorden y sobrestock | 150–300 USD/mes |
| Estándar | Hasta 500 SKUs, detección de anomalías, recomendaciones de acción | 300–600 USD/mes |
| Avanzado | Ilimitado, guardrail configurable por categoría, integración bidireccional ERP, API | 600–1200 USD/mes + setup 4–8k USD |

## 10. Riesgos

**1. Safety stock calculado con lead time incorrecto.**
*Síntoma*: el proveedor cambió de 5 a 8 días de lead time hace 3 meses; el ROP sigue calculado para 5 días; hay stockouts recurrentes.
*Mitigación*: el sistema monitorea la diferencia entre `lead_time_declarado` y `lead_time_real` (calculado de fecha_orden a fecha_recepción). Si el promedio real > declarado + 20%, alerta para actualizar el parámetro.

**2. EOQ inaplícable por restricciones de almacenaje.**
*Síntoma*: el EOQ calculado para el medicamento es 500 unidades, pero el almacén de frío solo tiene capacidad para 150.
*Mitigación*: el tenant declara `capacidad_maxima_almacenaje` por categoría de SKU. EOQ se trunka en ese máximo con nota explícita.

**3. Guardrail de SKU crítico omitido por cambio en la clasificación.**
*Síntoma*: alguien reclasificó un medicamento vital de CRÍTICO a NORMAL por error; el sistema lo trata como SKU normal y reduce el safety stock automáticamente.
*Mitigación*: el campo `criticidad` de un SKU requiere aprobación de dos usuarios con rol `inventory_admin`. El log de cambios es auditable. Ver también F-CMP-03 §10.

**4. Recomendación de descontinuación de SKU con demanda oculta.**
*Síntoma*: el agente recomienda descontinuar un SKU con 0 ventas en los últimos 3 meses; en realidad el cliente principal está en pausa temporal y volverá en Q3.
*Mitigación*: la recomendación de descontinuación siempre requiere confirmación humana. El agente debe incluir en su justificación si hay historial de pausa/patrón estacional antes de recomendar descontinuación.

## 11. Variantes por industria

### Instancia 1 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 200–500 SKUs, alta variabilidad estacional (temporadas), devoluciones que afectan el inventario disponible, múltiples almacenes (bodega central + punto de venta).

**Delta determinístico**: inventario «disponible real» = stock físico - órdenes reservadas en plataforma e-commerce aún no cumplidas. Si TiendaBox tiene 100 unidades físicas pero 40 ya están reservadas en Shopify, el inventario disponible es 60. Esta corrección es aritmética.

**Delta agéntico**: SKU con alta variabilidad de demanda (`CV > 1`) tiene safety stock muy grande que inmoviliza capital. El agente evalúa si la variabilidad proviene de un cliente concentrado (un pedido grande irregular) o de demanda genuinamente errática — acción correcta es diferente en cada caso.

**Regulación**: en Colombia, algunos SKUs de retail tienen control de precios o políticas de devolución obligatoria (Ley 1480). No aplica al cálculo de inventario, pero sí al plan de acción para sobrestock: devolución al proveedor puede estar limitada por ley.

**Precio orientativo**: 200–500 USD/mes.

### Instancia 2 — Salud privada (`sanrafael`)

**Datos típicos**: 300–800 SKUs de medicamentos, insumos quirúrgicos y dispositivos médicos. Medicamentos con fecha de vencimiento. SKUs de alta criticidad (sin sustituto disponible). Consumo variable según ocupación hospitalaria.

**Delta determinístico**: medicamentos tienen `fecha_vencimiento`. El inventario disponible efectivo = stock físico × `(1 - fracción_por_vencer_en_LT)`. Si 30 unidades vencen antes de que llegue la próxima orden, no cuentan como disponibles.

**Delta agéntico**: consumo hospitalario sube cuando hay brotes estacionales (influenza, dengue). El agente detecta si la variabilidad reciente del consumo de un medicamento corresponde a un brote y ajusta el safety stock temporalmente. Justificación: el modelo estadístico no distingue entre variabilidad aleatoria y variabilidad por brote.

**Guardrail duro (no negociable)**:
1. Ningún SKU con `criticidad == CRITICO` puede bajar su `stock_minimo` sin sign-off del Jefe de Farmacia con registro en el sistema.
2. Ninguna recomendación de sustitución de medicamento controlado puede implementarse sin revisión médica.
3. El sistema muestra en rojo cualquier SKU crítico con `DI < 3 × lead_time`, sin importar si el cálculo de safety stock lo considera «en rango».

**Regulación**: Resolución 1403/2007 (Colombia) sobre gestión de medicamentos en hospitales. COFEPRIS en México para establecimientos de salud. El sistema mantiene trazabilidad de todos los cambios de parámetro de inventario para auditoría sanitaria.

**Precio orientativo**: 400–900 USD/mes; setup 5–8k USD para carga del catálogo INVIMA/COFEPRIS con clasificación de criticidad.

## 12. Módulos técnicos relacionados

- **A06** (dataclasses y Pydantic): `InventoryParams` (ss, rop, eoq, z_factor, criticidad), `InventoryAlert` (sku, tipo_alerta, dias_inventario, accion_sugerida) como dataclasses con validación Pydantic.
- **C01** (SQLAlchemy async): tabla `inventory_params` con `tenant_id`, `sku`, `rop`, `safety_stock`, `updated_by`, `approved_by` (campo extra para SKUs críticos). El campo `approved_by` solo se puede llenar por usuario con rol `inventory_admin`.
- **E01** (Anthropic SDK + tools): la detección de patrón anómalo es el ejemplo de razonamiento estadístico contextual: el modelo recibe la serie de demanda, los parámetros calculados, y decide si los supuestos se cumplen — con justificación estructurada.

## Determinístico vs agéntico

| Tramo | Tipo | Por qué |
|-------|------|---------|
| Clasificación ABC-XYZ | determinístico | Percentiles + coeficiente de variación. Algoritmo cerrado. |
| Cálculo de safety stock, ROP, EOQ | determinístico | Fórmulas estadísticas cerradas dado los parámetros de entrada. |
| Flags de reorden y sobrestock | determinístico | Comparación aritmética contra umbrales calculados. |
| Detección de SKU con distribución no-Normal / no-estacionaria | agéntico | Requiere razonamiento sobre el tipo de anomalía y su causa probable. |
| Recomendación de acción para sobrestock (promo, devolución, descontinuar) | agéntico | La acción correcta depende de contexto (temporada, cliente, proveedor). |
| Evaluación de si reducir safety stock de SKU crítico | agéntico + guardrail duro | El razonamiento puede hacerlo el agente; la ejecución nunca sin sign-off humano. |

## 13. Errores típicos

**1. Safety stock calculado con `σ` de una serie con outliers no limpiados.**
*Síntoma*: un mes hubo un pedido puntual de 500 unidades de un cliente inusual; la `σ` resultante inflió el safety stock por 3x y el capital inmovilizado creció innecesariamente.
*Causa*: el cálculo no filtró los outliers antes de estimar `σ`.
*Arreglo*: aplicar Winsorizing (truncar al percentil 95) antes de calcular estadísticos. Para SKUs clase A, además mostrar el outlier identificado al usuario para confirmar antes de excluirlo.

**2. EOQ menor que el mínimo de orden del proveedor.**
*Síntoma*: el EOQ calculado es 150 unidades pero el proveedor solo vende en múltiplos de 500; el sistema genera una orden de 150 que el proveedor rechaza.
*Mitigación*: el tenant declara `moq` (minimum order quantity) por proveedor. El sistema calcula `orden_real = max(EOQ, MOQ)` y muestra el costo adicional de subir al MOQ.

**3. El guardrail de medicamento crítico se aplica a todos los SKUs de salud.**
*Síntoma*: el Jefe de Farmacia tiene que aprobar manualmente hasta el ajuste de parámetros del alcohol desinfectante.
*Causa*: el campo `criticidad` se inicializó como `CRITICO` para todos los SKUs del catálogo farmacéutico por defecto.
*Arreglo*: la clasificación inicial debe ser `NORMAL`. Solo los medicamentos en la lista de `Critical Drug List` del tenant (generalmente 20–50 SKUs) se marcan CRÍTICO. La carga inicial de esa lista requiere aprobación del Jefe de Farmacia.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame el safety stock con un ejemplo de Clínica San Rafael donde el lead time varía entre 3 y 7 días.»
2. **Aplícalo a mi caso**: «Tengo SKUs con demanda muy intermitente (compran 0, 0, 200, 0, 0, 150). ¿El cálculo de ROP y safety stock sigue siendo válido?»
3. **Por qué falló**: «El agente detectó un SKU como anómalo porque tiene alta variabilidad, pero resulta que es un SKU estacional. ¿Cómo le paso ese contexto al agente?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Implementar el cálculo de safety stock, ROP y EOQ con las fórmulas estadísticas correctas para distribución de demanda estacionaria.
- Diseñar el guardrail duro para SKUs críticos con trazabilidad de sign-off en la base de datos.
- Identificar exactamente qué supuestos hace el modelo estadístico y cuándo el agente debe intervenir para cuestionarlos.
- Configurar alertas de reorden y sobrestock con umbrales dinámicos (no fijos) basados en los parámetros calculados.
- Cotizar y dimensionar el servicio para retail o salud, incluyendo el argumento del guardrail ante direcciones de salud reguladas.

## 16. Módulos previos recomendados

| Módulo | Por qué te prepara para implementar esta ficha |
|--------|------------------------------------------------|
| A06   | `InventoryParams` (ss, rop, eoq, z_factor, criticidad) e `InventoryAlert` son dataclasses con validación Pydantic; el campo `criticidad: Literal["CRITICO", "NORMAL"]` es el tipo restrictivo que bloquea cambios automáticos sobre SKUs críticos. |
| A07   | El cálculo paralelo de safety stock, ROP y EOQ para 500 SKUs simultáneos usa `asyncio.gather` sobre las queries de historial de consumo por SKU; A07 establece el patrón de I/O concurrente que aquí se aplica. |
| C01   | La tabla `inventory_params` con `tenant_id`, `approved_by` (solo para SKUs críticos) y el índice por `(tenant_id, sku)` siguen el patrón de SQLAlchemy async con control de acceso por rol que C01 enseña. |
| C02   | El campo `approved_by` de un SKU crítico solo puede llenarse por usuario con rol `inventory_admin`; la política RLS que aísla los parámetros de inventario entre tenants es el patrón que C02 establece. |
| E01   | La detección de patrón anómalo que rompe los supuestos estadísticos — el modelo recibe la serie de demanda y produce una justificación estructurada — es el ejemplo de razonamiento estadístico contextual con output tipado que E01 introduce. |
