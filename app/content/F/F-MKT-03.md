---
ext_id: F-MKT-03
slug: generacion-contenido-brand
track: F
dept: MKT
ord: 203
title: "Generación de contenido con guardrails de brand"
summary: "Agente que produce copy para redes sociales, email y WhatsApp respetando tono de marca, palabras prohibidas y claims regulados; entrega borradores listos para aprobación humana."
related_modules: [D04, E01, E03, E04]
industries_instanced: [hospitalidad, serv-prof, retail, servicios-edu]
tenants_in_examples: [mesonurbano, consultorabc]
big_corp_vendors: [Jasper, Writer.com, Adobe Firefly]
latam_tools: [chatgpt-team, claude-team, canva, mailerlite]
key_concepts: [brand-voice, guardrails, banned-words, claims-regulados, skill-por-tenant, golden-set, CTR]
estimated_minutes: 45
deterministic_share: 0.2
version: 1
---

## 1. Problema operativo

El dueño de Mesón Urbano F&B necesita publicar tres posts de Instagram a la semana, un email mensual a su base y un mensaje de WhatsApp Business para cada promoción especial. No tiene un equipo de marketing: hay una persona que gestiona redes «además de sus otras cosas». El resultado es que se publican posts genéricos, tardíos, y que no suenan como el restaurante — suenan como cualquier restaurante.

En Consultora ABC el problema es el opuesto en materia de riesgo: la consultora ofrece servicios financieros y legales, y cualquier copy que prometa «garantizamos resultados» o «aseguramos X% de retorno» es un claim que el equipo legal debe revisar antes de publicar. Usar ChatGPT sin guardrails produce exactamente ese tipo de copy — bien redactado, regulatoriamente problemático.

La pregunta es: ¿cómo se usa un LLM para producir contenido de marketing a escala sin perder el tono de marca y sin arriesgarse a publicar algo ilegal o inapropiado?

## 2. Hoy en big corps

| Vendor | Qué hace | Costo orientativo |
|---|---|---|
| **Jasper** | Plataforma de generación de contenido con brand voice configurable, workflows de contenido, integración con CMS. Más de 50 templates. | 49–125 USD/usuario/mes; enterprise: cotizar |
| **Writer.com** | Plataforma enterprise de generación de contenido con brand guidelines, compliance checker, terminología prohibida y workflows de aprobación integrados. | 18–200 USD/usuario/mes; enterprise: cotizar |
| **Adobe Firefly + GenStudio** | Generación de assets visuales + copy integrados, con brand kits, templates y compliance de IP. | Incluido en Adobe Creative Cloud Enterprise (60–90 USD/usuario/mes) |

Las plataformas enterprise tienen brand guardrails nativos. La PYME usa ChatGPT Teams (30 USD/usuario/mes) o Claude Teams sin ningún guardrail configurado — el resultado es contenido genérico, inconsistente y potencialmente problemático.

## 3. PYME LATAM realista

Mesón Urbano usa Canva para diseño (plan Pro, 13 USD/mes) y ChatGPT o Claude para textos ad-hoc. No tiene un brand book formalizado — el tono es «lo que suena a nosotros», que solo saben internamente. La persona que redacta cambia cada seis meses.

Consultora ABC tiene un brand book en PDF, pero nadie lo lee antes de publicar. El equipo usa MailerLite para email marketing y publica en LinkedIn manualmente. Cada consultor redacta sus propios posts, con estilos radicalmente distintos.

La solución con IA no es «usar ChatGPT para todo» — es configurar el agente con los guardrails del cliente y hacer que el marketer apruebe el output antes de publicar. El LLM produce; el humano decide.

## 4. Datos típicos

| Campo | Fuente | Frecuencia | Ejemplo de valor |
|---|---|---|---|
| `content_request` | equipo de marketing | por solicitud | `"Post de Instagram para el menú de temporada de otoño"` |
| `channel` | solicitud | por pieza | `"instagram"` / `"email"` / `"whatsapp"` |
| `format` | solicitud | por pieza | `"caption_corto"` / `"email_cuerpo"` / `"mensaje_whatsapp"` |
| `brand_voice` | skill del tenant | fijo | `"Cálido, cercano, con toques de humor sutil. Sin jerga técnica."` |
| `banned_words` | skill del tenant | fijo | `["garantizamos", "aseguramos", "100% seguro", "mejor de la ciudad"]` |
| `regulated_claims` | skill del tenant | fijo | `["rendimiento garantizado", "sin riesgo", "aprobado por..."]` |
| `current_promotions` | slot dinámico | por campaña | `"20% off en menú de temporada hasta el 31 de mayo"` |
| `target_segment` | solicitud | por pieza | `"clientes habituales de almuerzo entre semana"` |
| `max_length` | por canal | fijo | `instagram: 2200 chars`, `whatsapp: 500 chars` |
| `hashtags_approved` | skill del tenant | fijo | `["#MesonUrbano", "#CocinaLocal", "#BogotaEats"]` |

**CTR (Click-Through Rate)**: porcentaje de personas que hacen clic sobre el contenido enviado. `CTR = clicks / impresiones`. Es la métrica principal de efectividad del copy en email y anuncios. Un buen CTR en email es 2–5%; en Instagram, el engagement rate es la métrica equivalente.

El skill por tenant (E03) almacena: `brand_voice`, `banned_words`, `regulated_claims`, `hashtags_approved`, `tone_examples` (3–5 ejemplos de copy aprobado previamente). Sin ese skill configurado, el agente no produce contenido — devuelve un error controlado.

## 5. Tramos determinísticos

1. **Validación de la solicitud de contenido**: verificar que la solicitud incluye `channel`, `format`, `target_segment` y `current_promotions`. Si falta alguno, el agente pide el campo faltante antes de generar. Regla cerrada.

2. **Aplicación de límites de longitud por canal**:
   - Instagram caption: ≤ 2 200 caracteres (límite de la plataforma).
   - WhatsApp Business mensaje: ≤ 1 024 caracteres (límite de la API).
   - Email subject line: ≤ 60 caracteres (para evitar truncamiento en móviles).
   - LinkedIn post: ≤ 3 000 caracteres.
   El agente recorta o avisa si el draft supera el límite. Regla fija.

3. **Checker de palabras prohibidas (banned-words filter)**: después de generar el draft, correr el texto por la lista `banned_words` del tenant. Si hay match, el nodo devuelve el draft marcado con `banned_word_detected: true` + la palabra que disparó la alerta. Nunca publica con una banned word sin acción humana explícita.

4. **Checker de claims regulados**: revisar si el draft contiene alguna de las frases de `regulated_claims`. Si hay match, el draft se marca con `regulated_claim_detected: true` y se pone en cola de revisión legal/compliance antes de enviarse al marketer. Regla cerrada, sin LLM.

5. **Verificación de hashtags**: los hashtags en el draft deben estar en la lista `hashtags_approved`. Cualquier hashtag que el modelo genere y que no esté en la lista se marca para aprobación. El agente no añade hashtags no aprobados al output final.

> [!cuidado]
> Los checks 3 y 4 son determinísticos y obligatorios. No son sugerencias: si un claim regulado aparece en el output, el draft **no se entrega al marketer** hasta que pase por revisión. El agente no puede «aprobar» sus propios outputs.

## 6. Tramos agénticos

1. **Generación del draft de contenido respetando brand voice.**
   *Por qué no es regla*: el tono de marca es descriptivo («cálido, cercano, con toques de humor»), no prescriptivo. No hay una función que tome «menú de otoño» y produzca copy «cálido con toques de humor». El LLM interpreta la descripción del brand voice + los ejemplos de tone del skill y genera copy coherente con el estilo del tenant.

2. **Adaptación del mensaje al segmento objetivo.**
   *Por qué no es regla*: el copy para «clientes habituales de almuerzo» es diferente al de «turistas que vienen por primera vez». La adaptación requiere razonar sobre quién es el receptor y qué le importa — no existe regla para eso.

3. **Propuesta de variantes A/B.**
   *Por qué no es regla*: el modelo puede generar 2–3 variantes del mismo mensaje con ángulos distintos (urgencia vs beneficio vs identidad). Qué ángulo funcionará mejor en ese segmento es una hipótesis que el marketer valida. El modelo propone las variantes con la justificación del ángulo; el humano decide cuál testear.

4. **Evaluación del propio output contra la rúbrica de brand.**
   *Por qué no es regla*: antes de entregar el draft, el modelo se autoevalúa contra la rúbrica de brand del tenant (¿el tono es coherente con los ejemplos aprobados? ¿hay alguna frase que suena genérica o corporativa?). Si detecta un problema, lo reformula o advierte. Esta auto-evaluación no es determinística — depende del contexto del skill.

> [!nota]
> La diferencia entre «usar ChatGPT» y «usar este agente» es el skill por tenant. Sin el skill, el LLM produce contenido genérico. Con el skill cargado (`brand_voice`, `banned_words`, `tone_examples`), el LLM produce contenido que suena a la marca. El skill es el producto, no el modelo.

## 7. Blueprint del workflow

### Nodos LangGraph

```
START
  ↓
[validate_request] → verificar campos requeridos de la solicitud (determinístico)
  ↓
[load_brand_skill] → cargar brand_voice, banned_words, regulated_claims, tone_examples (determinístico)
  ↓
[generate_draft] → LLM genera draft con brand voice + segmento + promoción (agéntico)
  ↓
[self_evaluate] → LLM evalúa draft contra rúbrica de brand, reformula si necesario (agéntico)
  ↓
[check_banned_words] → regex / exact match sobre banned_words (determinístico, GUARD)
  ↓
[check_regulated_claims] → match contra lista de claims regulados (determinístico, GUARD)
  ↓
[check_length] → recortar o avisar si supera límite del canal (determinístico)
  ↓
[check_hashtags] → verificar que hashtags estén en la lista aprobada (determinístico)
  ↓
[generate_variants] → LLM propone 2–3 variantes A/B con ángulos distintos (agéntico)
  ↓
[human_review?] → interrupt_before SIEMPRE — el output nunca se publica sin aprobación humana
  ↓
[deliver_content] → entregar borradores al marketer con checklist de aprobación (determinístico)
  ↓
END
```

> [!cuidado]
> `[human_review?]` con `interrupt_before` es **no negociable** en esta ficha. A diferencia de otros workflows donde el interrupt es condicional (solo si el importe supera un umbral), aquí el contenido de marketing **siempre** pasa por revisión humana antes de publicarse. El agente produce borradores; el marketer publica.

### Activities Temporal (job on-demand o semanal)

- `generate_content_batch(tenant, channel, requests_list)` — genera un lote de piezas.
- `deliver_content_for_review(tenant, batch_id, channel)` — entrega al marketer.
  `idempotency_key = "content:{tenant}:{channel}:{batch_id}"`

### Tools necesarias (referencia SHARED.md §3.6)

- `fetch_excel` — si el tenant tiene un calendario editorial en Sheets.
- `sql_query` — para obtener `current_promotions` y `target_segment` del sistema del tenant.
- `write_report` — bundle de borradores + checklist de aprobación en PDF o Notion.
- `send_email` — entrega del bundle al marketer para revisión.

## 8. Salida y entrega

### Bundle de contenido para revisión

```
CONTENIDO PARA APROBACIÓN — Mesón Urbano — Semana 3 Mayo 2026

SOLICITUD: 1 post Instagram + 1 mensaje WhatsApp para el menú de temporada de otoño.
Segmento: clientes habituales de almuerzo entre semana.

--- INSTAGRAM CAPTION (borrador) ---

¿Cambiaste el verano por el frío con ganas? Nosotros también. 🍂

Esta semana el menú de temporada ya es del otoño: crema de calabaza asada,
cordero braseado y tiramisú de canela. Los de siempre ya lo saben — los
martes cambia todo.

20% off si reservas antes del viernes. → link en bio

#MesonUrbano #CocinaLocal #BogotaEats

VARIANTE A (ángulo urgencia): "El menú de otoño dura solo hasta el domingo..."
VARIANTE B (ángulo comunidad): "Los que vienen cada martes ya lo saben..."

✓ Banned words: ninguna detectada.
✓ Regulated claims: ninguno detectado.
✓ Longitud: 847 caracteres (dentro del límite de 2 200).
✓ Hashtags: todos en lista aprobada.
⚠ REQUIERE APROBACIÓN DEL MARKETER ANTES DE PUBLICAR.

--- MENSAJE WHATSAPP (borrador) ---
[máx. 500 chars]

Hola 👋 Esta semana en Mesón Urbano estrenamos menú de otoño: crema de
calabaza, cordero y tiramisú de canela. Si eres de los de los martes,
tienes 20% off hasta el viernes con este mensaje. Reserva: [link].

✓ Longitud: 273 caracteres (dentro del límite).
✓ Banned words y claims: sin alertas.
⚠ Verificar que los destinatarios tienen opt-in WhatsApp Business activo antes de enviar.

CHECKLIST DE APROBACIÓN:
[ ] Copy aprobado por el equipo de marketing
[ ] Oferta (20% off) aprobada por gerencia
[ ] Lista de envío de WhatsApp verificada (opt-in activo)
[ ] Publicación programada en: ________
```

**Canal de entrega**: email al marketer + link al documento compartido. El marketer marca el checklist y confirma antes de que el copy salga del sistema.

## 9. Cómo se vende

**Gancho**: «El equipo de marketing tarda 3 horas en escribir un post que luego suena genérico. Este agente lo hace en 3 minutos y suena a tu marca — con los checks de palabras prohibidas y claims regulados ya corridos.»

**Propuesta de valor**: contenido en el tono correcto, con guardrails automáticos, y flujo de aprobación documentado. La diferencia entre «ChatGPT gratis» y este producto es el skill configurado y el trail de aprobación.

| Tier | Qué incluye | Precio orientativo |
|---|---|---|
| Básico | Generación de copy por solicitud, brand voice básico, sin checker automático | 100–200 USD/mes |
| Estándar | Brand voice + banned words checker + claims checker + variantes A/B + flujo de aprobación | 300–600 USD/mes |
| Premium | Todo + integración con calendario editorial + posting directo a Instagram/LinkedIn API después de aprobación + métricas de CTR por variante | 600–1 200 USD/mes + setup 2–4 k USD |

Setup: 2–3 semanas. Incluye: definición del `brand_voice` del skill con el equipo de marketing (sesión de 2 horas), carga de `tone_examples` (5–10 piezas de copy aprobadas anteriormente), definición de `banned_words` y `regulated_claims`, y golden set de 5 solicitudes de contenido para validar el output.

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| **Copy genérico**: el LLM produce texto correcto pero sin voz de marca. | El skill por tenant requiere ≥ 3 `tone_examples` de copy aprobado. Sin ellos, el sistema advierte que el skill está incompleto. Sin ejemplos, el brand voice es abstracto y el output lo refleja. |
| **Claim regulado no detectado**: una frase nueva con el mismo sentido que un claim prohibido pero con palabras distintas. | El checker de claimed_regulated es exact match (rápido, confiable) más una segunda pasada agéntica: el modelo evalúa si el draft implica un claim regulado aunque no use las palabras exactas. El fallback es la revisión humana siempre. |
| **Drift de tono**: con el tiempo, el agente empieza a sonar distinto a la marca porque el skill no se actualiza. | El golden set se revisa cada 3 meses con el equipo de marketing. Si la tasa de aprobación sin edición baja < 70%, el skill necesita actualización. |
| **Envío sin aprobación**: el marketer salta el checklist y publica el borrador directamente. | El sistema no entrega el copy publicable directamente — entrega un borrador con marca de agua «BORRADOR PARA APROBACIÓN». El marketer tiene que hacer una acción explícita para extraer el copy final. |
| **PII en el contenido**: el draft menciona accidentalmente datos de un cliente (nombre, compra, etc.). | Los datos de clientes individuales nunca entran en el prompt del nodo `generate_draft`. El segmento se describe con datos agregados (comportamiento del grupo), no con datos de individuos. |
| **Regulación en claims de salud (clínicas, farmacias)**: «Cura X», «alivia Y sin efectos secundarios». | La lista `regulated_claims` del skill de salud incluye todos los claims sensibles de ANMAT (Argentina), ANVISA (Brasil) o INVIMA (Colombia). El checker los detecta antes de entregar el draft. |

> [!cuidado]
> **Fallback humano**: si el checker detecta un claim regulado o un banned word, el draft **no llega al marketer** en ese estado. Se devuelve al nodo `generate_draft` con la instrucción de eliminar el elemento problemático. Si en el segundo intento vuelve a aparecer, el sistema lo marca como `requires_legal_review` y lo pone en cola de revisión manual. El agente nunca fuerza una entrega con alertas activas.

## 11. Variantes por industria

### Instancia 1 — Hospitalidad / F&B (`mesonurbano`)

**Datos típicos**: 3–5 piezas de contenido por semana (Instagram, WhatsApp, email mensual), menú que cambia semanalmente o con temporada, base de clientes que conoce la marca.

**Delta determinístico**: el menú de la semana es el input principal. El agente lee el menú de un Google Sheet y lo convierte en el `current_promotions` del prompt. Esto es determinístico (lectura + formato).

**Delta agéntico**: el tono de un restaurante boutique es específico — hay que sonar local, artesanal, no corporativo. El LLM tiene que saber cuándo usar humor suave vs cuándo ser más formal (un evento privado vs una promo de lunes).

**Regulación**: claims sobre ingredientes («100% orgánico», «sin aditivos») requieren certificación real. El checker de regulated_claims en hospitalidad incluye esos términos.

**Precio orientativo**: 200–400 USD/mes.

### Instancia 2 — Servicios profesionales (`consultorabc`)

**Datos típicos**: 2–3 posts LinkedIn por semana, 1 email quincenal, 1 caso de éxito mensual. El tono es profesional, basado en expertise.

**Delta determinístico**: el checker de claims regulados es más estricto y largo que en F&B. Incluye frases como «garantizamos resultados», «aseguramos retorno», «libre de riesgo», «asesoría certificada en X» (si la certificación no está en el perfil del consultor). El checker corre sobre el output antes de cualquier entrega.

**Delta agéntico**: el contenido de thought leadership (artículos de opinión, posts de LinkedIn con insights) requiere más elaboración que un post de Instagram. El LLM tiene que entender el tema de la consultoría y producir un punto de vista coherente, no genérico.

**Regulación Colombia (SFC)**: los contenidos financieros que impliquen asesoría de inversión requieren advertencia legal explícita. El agente añade automáticamente el disclaimer aprobado al final de cada pieza que toca inversión o rendimientos.

**Precio orientativo**: 350–700 USD/mes.

### Instancia 3 — Retail / E-commerce (`tiendabox`)

**Datos típicos**: 5–10 piezas semanales (Instagram, email, WhatsApp promocional), campañas por temporada (Black Friday, Navidad, Day of the Dead), catalogo de producto amplio.

**Delta determinístico**: el catálogo de producto es el input. El agente lee el CSV del catálogo (nombre, precio, disponibilidad) y genera copy de producto por SKU o por categoría. La longitud y el formato por canal son reglas fijas.

**Delta agéntico**: el copy de producto en e-commerce tiene que ser descriptivo y persuasivo a la vez. El LLM decide qué atributos destacar según el segmento: para los champions, destaca exclusividad; para los en-riesgo-de-churn, destaca precio.

**Regulación**: las promociones de descuento en Argentina deben mostrar el precio original tachado junto al precio con descuento (Ley 24.240, Ley de Defensa del Consumidor). El checker verifica que los posts de promo incluyan ambos precios.

**Precio orientativo**: 400–800 USD/mes.

### Instancia 4 — Educación

**Datos típicos**: instituciones educativas (institutos de idiomas, cursos técnicos, academias) con campañas de captación en períodos de inscripción. Contenido en redes y email con propuesta de valor del programa.

**Delta determinístico**: las fechas de inscripción y los precios de matrícula son inputs fijos que el agente lee de un documento estructurado. El checker verifica que el precio publicado coincide con el precio vigente.

**Delta agéntico**: el copy de educación tiene que conectar emocionalmente con el prospecto («cambia tu carrera», «domina el inglés en 6 meses»). El LLM balancea la motivación con la honestidad — ningún claim sobre tiempo de aprendizaje garantizado pasa el checker.

**Regulación (LATAM)**: las instituciones educativas no acreditadas no pueden usar los términos «certificado oficial», «título universitario» ni «avalado por el Ministerio» sin la acreditación correspondiente. El checker los incluye en `regulated_claims`.

**Precio orientativo**: 250–500 USD/mes.

## 12. Módulos técnicos relacionados

| Módulo | Qué aplica de ese módulo |
|---|---|
| **D04** — Observabilidad | Phoenix traza `generate_draft`, `self_evaluate`, `generate_variants`. Detectar: ¿cuántas veces el modelo falla el checker y tiene que regenerar? ¿cuántos drafts pasan sin edición humana? Esas métricas miden la calidad del skill. |
| **E01** — Anthropic SDK | El skill (`brand_voice`, `tone_examples`, `banned_words`) se carga como bloque de system prompt con `cache_control: {"type": "ephemeral", "ttl": "1h"}`. La solicitud específica (canal, formato, promoción del día) va en el mensaje dinámico sin cache. |
| **E03** — Skills por tenant | Esta ficha es el caso de uso más directo del skill por tenant. El skill `content_generation` tiene slots: `brand_voice`, `banned_words`, `regulated_claims`, `tone_examples`, `hashtags_approved`, `disclaimer_texts`. Sin estos slots definidos, el nodo `generate_draft` devuelve un error controlado: «Skill incompleto. Define brand_voice y al menos 3 tone_examples.» |
| **E04** — Memoria multitenant | El historial de piezas aprobadas (las que el marketer aprobó sin edición) se acumula como `approved_content_log` en el store de largo plazo del tenant. El nodo `self_evaluate` puede consultar ese historial para calibrar si el draft es coherente con lo que históricamente se aprueba. |

## 13. Errores típicos

**1. Claim regulado eludido con sinónimos (alucinación semántica).**
*Síntoma*: el checker exact-match no detecta nada, pero el draft dice «Con nuestro método tienes éxito garantizado en 6 meses» — semánticamente equivalente a «garantizamos resultados», que sí está en la lista `regulated_claims`.
*Causa raíz*: el checker de claims solo hace exact-match y no tiene la segunda pasada agéntica activa.
*Cómo evitarlo*: activar la segunda pasada agéntica (`self_evaluate` con instrucción explícita de detectar claims prohibidos por paráfrasis). Si el nodo detecta equivalencia semántica, marca el draft como `regulated_claim_detected: true` aunque las palabras exactas no coincidan.

**2. Riesgo legal por contenido auto-publicado sin review.**
*Síntoma*: el marketer configura el sistema para publicar directamente en Instagram después de la generación; un post con un claim de descuento («¡Matrícula gratis este mes!» cuando la institución no está acreditada para ese beneficio) sale sin revisión y genera una queja regulatoria.
*Causa raíz*: el `interrupt_before` del nodo `[human_review?]` fue desactivado para agilizar el flujo.
*Cómo evitarlo*: el `interrupt_before` es non-negociable en esta ficha. El sistema nunca entrega copy publicable directamente — siempre como borrador. Cualquier integración con API de publicación (Instagram, LinkedIn) requiere un paso de aprobación documentado con `approved_by` y timestamp antes de ejecutar el post.

**3. Skill incompleto produce contenido genérico.**
*Síntoma*: los drafts suenan a contenido de IA genérico, sin voz de marca; el equipo los rechaza sistemáticamente y los reescribe desde cero.
*Causa raíz*: el skill del tenant tiene `brand_voice` definido como una frase corta sin `tone_examples`; el LLM no tiene referencia concreta de cómo suena la marca.
*Cómo evitarlo*: el onboarding requiere obligatoriamente al menos 3 ejemplos de copy aprobado como `tone_examples`. El nodo `load_brand_skill` verifica que el slot `tone_examples` tenga al menos 3 entradas antes de habilitar `generate_draft`. Sin ellas, devuelve error controlado.

**4. Drift de tono por falta de actualización del skill.**
*Síntoma*: después de 3 meses, el agente empieza a generar copys que suenan a la versión anterior de la marca (cambió el tono de formal a cercano, pero el skill no se actualizó).
*Causa raíz*: nadie revisa el golden set ni los `tone_examples` del skill después del onboarding.
*Cómo evitarlo*: la tasa de aprobación sin edición se mide en D04. Si cae por debajo del 70% en un período de 30 días, el sistema notifica al responsable de marketing: «El skill de contenido necesita actualización». El skill tiene un campo `last_reviewed_date` visible en el panel.

**5. Hashtags no aprobados insertados en el draft.**
*Síntoma*: el modelo genera hashtags relevantes temáticamente pero no aprobados por el equipo de marca; el marketer los publica sin notar que uno de ellos está asociado a un movimiento controvertido en redes.
*Causa raíz*: el nodo `check_hashtags` no está activo o la lista `hashtags_approved` del skill está vacía.
*Cómo evitarlo*: si `hashtags_approved` está vacía, el agente no añade hashtags al output y lo declara explícitamente. El marketer define la lista aprobada como parte del onboarding del skill.

## 14. Pregúntale al tutor

1. **Explícame de otra forma**: «Explícame por qué el skill por tenant es lo que hace que el contenido suene a la marca y no a ChatGPT genérico — ¿qué diferencia hace exactamente cada slot del skill?»
2. **Aplícalo a mi caso**: «Mi cliente es una consultora financiera en Colombia. ¿Cómo defino la lista `regulated_claims` para cumplir con la SFC sin que el agente bloquee todo el contenido financiero legítimo?»
3. **Por qué falló**: «El agente generó un draft para Instagram con el hashtag #InversionesSeguras que no estaba en la lista aprobada y el marketer lo publicó. ¿En qué nodo falló el flujo y cómo lo arreglo?»

## 15. Salida esperada

Al terminar esta ficha, puedes:

- Configurar el skill por tenant con `brand_voice`, `banned_words`, `regulated_claims` y `tone_examples` como bloque cacheable del system prompt.
- Implementar los checkers determinísticos de banned words, claims regulados, longitud por canal y hashtags como nodos GUARD no saltables.
- Diseñar la segunda pasada agéntica de auto-evaluación del draft contra la rúbrica de brand.
- Configurar el `interrupt_before` como non-negociable y documentar el trail de aprobación para cumplimiento regulatorio.
- Cotizar y dimensionar el servicio para hospitalidad, servicios profesionales, retail y servicios educativos LATAM.

## 16. Módulos previos recomendados

| Módulo | Por qué leerlo antes |
|--------|---------------------|
| **D04** — Observabilidad | Phoenix traza cada llamada a `generate_draft` y `self_evaluate`; medir cuántas veces el modelo falla el checker es la métrica de calidad del skill. Sin D04 el drift de tono es invisible. |
| **E01** — Anthropic SDK | El skill se carga con `cache_control: ephemeral` en el system prompt; entender prompt caching es imprescindible para que el agente sea eficiente en costo cuando el tenant genera muchas piezas. |
| **E03** — Skills por tenant | Esta ficha es el caso de uso más directo de E03: el skill `content_generation` con sus slots es exactamente el patrón que E03 enseña para configurar comportamiento por tenant sin hardcodear. |
| **E04** — Memoria multitenant | El `approved_content_log` del tenant alimenta el nodo `self_evaluate`; entender E04 explica cómo el historial de aprobaciones calibra el agente con el tiempo. |
