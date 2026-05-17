# Track H — Operación de Producto

Este track convierte un implementador técnico en un operador de servicio vivo.
La diferencia: el implementador sabe construir; el operador sabe mantener, medir y escalar sin quemar dinero.

## Módulos

| ext_id | slug | título | ord | min |
|--------|------|---------|-----|-----|
| H01 | `runbooks-and-oncall` | Runbooks y on-call: el primer incidente a las 3am | 240 | 60 |
| H02 | `blameless-postmortems` | Postmortems blameless: aprender sin culpar | 241 | 45 |
| H03 | `agent-drift-and-evals` | Drift detection en agentes IA: golden sets, A/B con LLM, regresión | 242 | 75 |
| H04 | `finops-cost-monitoring` | FinOps: presupuestos, alertas, costo por tenant, optimización | 243 | 60 |
| H05 | `scale-small-to-big` | Empezar pequeño y crecer: escalado y costo paso a paso | 244 | 90 |
| H06 | `restore-drills` | Restore drills: el backup que nadie ha probado es ficción | 245 | 45 |
| H07 | `multi-model-failover` | Multi-modelo y failover: Anthropic ↔ OpenAI ↔ Bedrock | 246 | 60 |

**Total: ~435 minutos (~7.25 horas)**

## Prerequisitos del track

- D03 (Hetzner + Traefik + backup.sh)
- D04 (Phoenix + telemetry + cost middleware)
- E01 (Anthropic SDK en producción)
- E05 (Temporal workflows — para H06 drill workflow y H03 evals)

## Hilo interno del track

```
H01 (runbooks + on-call)
  → H02 (postmortem de lo que el runbook no resolvió)
    → H03 (drift: el agente falla sin que nadie lo reporte)
      → H04 (FinOps: el costo del agente que drifteó)
        → H05 (escalar: cuándo y cuánto gastar)
          → H06 (restore: el backup del sistema que escala)
            → H07 (failover: cuando el LLM falla)
```

## Decisiones de diseño del track

1. **Todos los costos en USD/mes y EUR/mes con rangos reales 2026.**
   Fuentes: Hetzner pricing (CX22 €4.49, CX32 €6.80, LB11 €5.39 verificados WebSearch 2026),
   Anthropic SDK pricing (sonnet-4-6: $3/M input, $15/M output), BetterStack/PagerDuty pricing.

2. **Énfasis en "medir antes de optimizar"** en H03, H04 y H05.
   El anti-patrón más caro en SaaS PYME es la optimización prematura.

3. **Opsgenie se declara obsoleto** en H01 (Atlassian detuvo ventas en junio 2025, cierra abril 2027).
   BetterStack free es la recomendación default para equipos de 1-3 personas.

4. **H05 es el módulo central del track** (90 min). Tiene las 4 etapas con números,
   6 reglas anti-quema de dinero, tabla de upgrade path y un ejercicio de plan mensual
   con calculadora de infra_cost_eur ejecutable en Pyodide.

5. **LiteLLM y OpenRouter verificados** como las dos opciones principales de gateway.
   Grafana OnCall OSS fue archivado en marzo 2026; se usa la versión Cloud.

## Archivos por módulo

```
H/
├── _README.md          (este archivo)
├── H01.md + H01.exercises.yaml + H01.quizzes.yaml
├── H02.md + H02.exercises.yaml + H02.quizzes.yaml
├── H03.md + H03.exercises.yaml + H03.quizzes.yaml
├── H04.md + H04.exercises.yaml + H04.quizzes.yaml
├── H05.md + H05.exercises.yaml + H05.quizzes.yaml
├── H06.md + H06.exercises.yaml + H06.quizzes.yaml
└── H07.md + H07.exercises.yaml + H07.quizzes.yaml
```
