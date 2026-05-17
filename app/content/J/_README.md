# Track J — Compliance LATAM

Track de cumplimiento legal y regulatorio para agentes IA en LATAM.
4 módulos. Audiencia: desarrollador técnico que ya construye agentes
pero no conoce las obligaciones legales que activa al procesar datos
de clientes en Colombia, Perú, Brasil y México.

## Módulos

| ext_id | slug | título | ord | min |
|--------|------|--------|-----|-----|
| J01 | `habeas-data-co-pe` | Habeas Data Colombia (Ley 1581) + LFPD Perú (Ley 29733) | 260 | 60 |
| J02 | `lgpd-brasil` | LGPD Brasil: el más estricto de la región | 261 | 60 |
| J03 | `lfpdppp-mx-and-fe` | LFPDPPP México + facturación electrónica DIAN/SAT/CFDI | 262 | 75 |
| J04 | `kyc-aml-sarlaft-flows` | KYC/AML/SARLAFT en flujos agénticos: cuándo paras al humano | 263 | 60 |

## Archivos por módulo

Cada módulo produce 3 archivos:
- `{ext_id}.md` — contenido principal (13 secciones canónicas)
- `{ext_id}.exercises.yaml` — 2–3 ejercicios (design + code/pyodide)
- `{ext_id}.quizzes.yaml` — 3 quizzes con feedback explicativo

## Posición en el currículo

El Track J sigue a los Tracks C y D (datos + operación) y precede al
Track E (agentes IA). La motivación: las decisiones de diseño de
privacidad (RLS, retención, transferencia internacional) deben tomarse
antes de que el agente entre en producción con datos reales de clientes.

## Referencias normativas (verificadas mayo 2026)

- **Colombia**: Ley 1581/2012, Decreto 1377/2013, Decreto 886/2014,
  Decreto 1074/2015, Circular Externa 027/2020 (SARLAFT 4.0),
  DIAN Resolución 042/2020. Proyecto de ley 2025 eleva multas SIC.
- **Perú**: Ley 29733/2011, DS 16-2024-JUS (nuevo Reglamento, nov 2024),
  plazo de brechas reducido a 48h.
- **Brasil**: Lei 13.709/2018 (LGPD), Resolução CD/ANPD Nº 19/2024
  (transferencias internacionales, SCCs obligatorias desde ago 2025).
- **México**: LFPDPPP publicada 20 marzo 2025, INAI disuelto → SABG.
  CFDI 4.0 obligatorio desde 1 abril 2023. SAT PAC requerido para emisión.

## Principio rector del track

El cumplimiento legal NUNCA es 100% agéntico. El agente analiza,
clasifica y documenta. El humano (oficial de cumplimiento, DPO,
contador) decide y firma. Esta arquitectura no es una preferencia
de diseño; es un requisito regulatorio en todas las jurisdicciones
cubiertas.
