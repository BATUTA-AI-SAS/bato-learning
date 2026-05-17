# Track G — Negocio LATAM: convenciones del track

> Última revisión: 2026-05-16. Leer antes de escribir o editar cualquier módulo G.

---

## Propósito del track

Track G cierra el ciclo «sé construir → sé vender». El lector que llega aquí
terminó E06 (o al menos D + E01–E03) y puede armar un agente multitenant
funcional. Lo que no puede hacer todavía: firmar un cliente, cobrarle, y
mantenerlo feliz. Eso es lo que cubre G01–G07.

**Prerrequisito conceptual mínimo**: el lector conoce al menos un caso F
(preferiblemente F-FIN-01 o F-CTA-02) porque el Track G usa esos casos como
palancas de venta concretas.

---

## Principio transversal: los agentes NO toman decisiones comerciales

Declaración explícita e irrenunciable en todos los módulos del track:

> El agente IA entrega información, análisis y borradores. La decisión comercial
> —firmar, cobrar, escalar, despedir un cliente— la toma siempre un humano.
> No por limitación del modelo: por diseño deliberado del servicio.

Cualquier ejemplo que muestre un agente «cerrando una venta» o «rechazando un
contrato» automáticamente está mal. Los agentes en Track G son herramientas de
preparación y seguimiento, no de decisión.

---

## Convenciones específicas de G

### Moneda y precios

- Todos los precios de servicios vendidos al cliente en **USD/mes** (PYME
  LATAM los cotiza así desde que adoptó el SaaS anglosajón como referencia).
- Rangos siempre, nunca precio único: `200–800 USD/mes`.
- Cuando se menciona IVA/ISR/retención local, citar la ley pero no calcular
  (el contador del cliente hace eso).
- Los costos internos del lector (infra, API tokens) se expresan también en
  USD/mes para hacer el margen visible.

### Contratos y templates

- Siempre referenciar fuentes open-source verificables (Common Paper, YC
  templates, GitLab open-source contracts). Nunca inventar cláusulas como si
  fueran estándar: el lector necesita llevarlas a un abogado local.
- Jurisdicción canónica de los ejemplos: Colombia. Cuando un módulo generaliza
  a LATAM, lo dice explícito con una tabla de deltas por país.

### Personajes canónicos del track

Los módulos G usan preferentemente:

| slug | uso en G |
|------|----------|
| `andina` | Constructora Andina — el cliente ficticio del Capstone G07 |
| `consultorabc` | el lector en rol de proveedor (servicios profesionales) |
| `initech` | edge case de cliente difícil / scope creep |
| `acme` | cuando se necesita un cliente manufacturero genérico |

El proveedor que vende (el lector) **no tiene slug canónico**: se llama
«el proveedor» o «tu empresa» para subrayar que la propuesta es del lector,
no del curso.

### Secciones 9 y 10 de cada módulo: adaptaciones para G

- **Sección 9 (Determinístico vs agéntico)**: en Track G el eje es
  *proceso humano vs herramienta IA*. La tabla muestra qué partes del proceso
  comercial pueden asistirse con un agente (preparar brief, redactar borrador de
  propuesta, detectar señales de churn en datos de uso) vs qué partes exige
  juicio humano irremplazable (negociar precio, firmar, decidir escalation).
- **Sección 10 (Errores típicos)**: son errores de proceso comercial y
  contractual, no de código. Usar la misma plantilla de síntoma/causa/arreglo.

### Ejercicios en G

La mayoría son `kind: design` sin runner de código porque el output es un
documento (script de discovery, propuesta comercial, esqueleto de MSA). Para
los ejercicios que validan estructura de documento, se usa `runner: pyodide` con
tests sobre dicts que parsean el YAML/texto del lector.

Ningún ejercicio de G pide «escribe el código del agente». Eso ya se hizo en
E. En G el ejercicio es el artefacto comercial.

### Glosario específico de G (añadir a SHARED.md si no está)

- **Discovery**: sesión estructurada con el cliente para mapear el problema
  operativo real antes de cualquier demo o propuesta.
- **POC (Proof of Concept)**: agente mínimo sobre datos reales del cliente con
  success criteria acordados y fecha de cierre.
- **MSA (Master Service Agreement)**: contrato marco que regula la relación
  comercial general con el cliente. Se firma una vez.
- **SOW (Statement of Work)**: adenda al MSA que define alcance, entregables y
  precio de un proyecto específico.
- **DPA (Data Processing Agreement)**: acuerdo de tratamiento de datos
  personales. Obligatorio bajo Ley 1581 (CO), LGPD (BR), LFPDPPP (MX).
- **SLA (Service Level Agreement)**: compromisos de disponibilidad y tiempo de
  respuesta del servicio.
- **NDR (Net Dollar Retention)**: `(MRR inicio + expansión - contracción -
  churn) / MRR inicio × 100`. Mide cuánto crece el ingreso de la base existente.
- **NRR (Net Revenue Retention)**: sinónimo de NDR en uso común.
- **QBR (Quarterly Business Review)**: reunión trimestral con el cliente para
  revisar valor entregado, métricas acordadas y roadmap de expansión.
- **Churn**: cancelación de contrato. En PYME LATAM se mide anual porque los
  contratos suelen ser anuales.
- **Anchoring**: mostrar primero el precio más alto para que el resto parezca
  razonable por contraste.
- **SPIN**: marco de preguntas de ventas (Situación, Problema, Implicación,
  Necesidad-beneficio). Funciona como guía, no como guion literal en LATAM.
- **MEDDIC**: calificación de oportunidad (Metrics, Economic Buyer, Decision
  Criteria, Decision Process, Identify Pain, Champion). Útil para deals > 5k
  USD/año.

---

## Capstone G07 — cómo encajan los módulos anteriores

| Entregable de G07 | Módulo origen |
|--------------------|---------------|
| Discovery script aplicado | G01 |
| Propuesta comercial 1 página | G02 + G03 |
| MSA / SOW / DPA esqueletos | G04 |
| Plan de onboarding 14 días | G05 |
| KPIs de éxito acordados y plantilla QBR | G06 |

G07 es el único módulo del track que integra todos los anteriores. No introduce
conceptos nuevos; solo los pone en producción sobre un caso ficticio completo.

---

Fin de _README.md del Track G.
