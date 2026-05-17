// RPG Room definitions — 4 rooms, 20x15 tile grids, 80 puzzle levels
// Tile IDs: 0=FLOOR, 1=WALL, 2=DOOR_OPEN, 3=DOOR_LOCKED, 4=DESK, 5=TERMINAL,
// 6=BOOKSHELF, 7=SERVER_RACK, 8=WINDOW, 9=NPC_MARKER, 10=FLOOR_ALT, 11=RUG,
// 12=PLANT, 13=BOARD, 14=CHAIR, 15=STAIRS

export const ROOMS = {

  // ─────────────────────────────────────────────────────────────────────────
  // PHASE 1 — La Oficina
  // ─────────────────────────────────────────────────────────────────────────
  "la-oficina": {
    slug: "la-oficina",
    name: "La Oficina",
    subtitle: "Despacho de auditoría",
    tiles: [
      // Row 0  — top wall
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      // Row 1
      [1, 0, 0, 0, 0, 1, 0, 0, 8, 0, 0, 8, 0, 0, 1, 0, 0, 0, 0, 1],
      // Row 2
      [1, 0, 5, 14, 0, 1, 0, 12, 0, 0, 0, 0, 12, 0, 1, 0, 4, 14, 0, 1],
      // Row 3
      [1, 0, 0, 0, 0, 1, 0, 0, 0, 11, 11, 0, 0, 0, 1, 0, 0, 0, 0, 1],
      // Row 4
      [1, 0, 0, 0, 0, 0, 0, 0, 11, 11, 11, 11, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 5
      [1, 8, 0, 0, 0, 0, 0, 0, 11, 9, 11, 11, 0, 0, 0, 0, 0, 0, 8, 1],
      // Row 6
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 11, 11, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 7 — internal wall divider
      [1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1],
      // Row 8
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 9
      [1, 0, 6, 6, 0, 0, 0, 12, 0, 0, 0, 0, 12, 0, 0, 0, 5, 14, 0, 1],
      // Row 10
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 11
      [1, 8, 0, 0, 0, 4, 14, 0, 0, 13, 13, 0, 0, 4, 14, 0, 0, 0, 8, 1],
      // Row 12
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 13
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 14 — bottom wall
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    spawn: { x: 10, y: 13, facing: "up" },
    palette: { wall: "#4a3728", floor: "#d4c4a8", accent: "#8b6914" },
    objects: [
      // --- Puzzle Clusters ---
      {
        x: 2, y: 2,
        type: "puzzle_cluster",
        levels: ["terminal-mkdir", "first-variable", "iva-calculation", "invoice-message"],
        label: "Terminal del pasante",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Un viejo terminal parpadea en la esquina. La pantalla muestra un cursor esperando tu primer comando.",
            "Aquí empieza todo — carpetas, variables, cálculos. Lo básico."
          ]
        }
      },
      {
        x: 17, y: 2,
        type: "puzzle_cluster",
        levels: ["sum-invoices", "filter-high-value", "vendor-dict", "reusable-iva"],
        label: "Escritorio de facturas",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "El escritorio del director está cubierto de facturas. El desorden tiene un patrón — si lo encuentras.",
            "Sumas, filtros, diccionarios... las herramientas de quien organiza el caos."
          ]
        }
      },
      {
        x: 2, y: 9,
        type: "puzzle_cluster",
        levels: ["read-csv-file", "debug-conversion", "split-modules", "install-pandas"],
        label: "Estante de archivos",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Carpetas etiquetadas con nombres de clientes llenan el estante. Cada archivo es un misterio por descifrar.",
            "Leer datos, depurar errores, modularizar — el trabajo real empieza aquí."
          ]
        }
      },
      {
        x: 16, y: 9,
        type: "puzzle_cluster",
        levels: ["pydantic-invoice", "docker-basics", "git-first-commit", "first-api-endpoint"],
        label: "Estación DevOps",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Un segundo terminal con stickers de Docker y Git. Alguien dejó notas adhesivas con comandos.",
            "Validación, contenedores, control de versiones, APIs — el kit del profesional."
          ]
        }
      },
      {
        x: 5, y: 11,
        type: "puzzle_cluster",
        levels: ["http-anatomy", "jinja-template", "htmx-dashboard"],
        label: "Mesa de diseño web",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Bocetos de interfaces y diagramas HTTP cubren esta mesa. La web tiene su propio idioma.",
            "Peticiones, plantillas, interactividad — construye lo que el usuario ve."
          ]
        }
      },
      // --- NPC ---
      {
        x: 9, y: 5,
        type: "npc",
        npc_id: "don-ramon",
        label: "Don Ramón",
        dialogues: {
          progress_0: {
            speaker: "DON RAMÓN",
            lines: [
              "Bienvenido al despacho. Aquí todo empieza con lo básico: un terminal, unos datos, y ganas de aprender.",
              "Explora las estaciones de trabajo. Cada una tiene desafíos que te prepararán para lo que viene."
            ]
          },
          progress_50: {
            speaker: "DON RAMÓN",
            lines: [
              "Vas bien. Ya manejas variables y datos como si llevaras meses aquí.",
              "¿Ya revisaste la estación DevOps? Docker y Git son imprescindibles allá afuera."
            ]
          },
          progress_100: {
            speaker: "DON RAMÓN",
            lines: [
              "Impresionante. La oficina ya no tiene nada que enseñarte.",
              "La puerta al taller se ha abierto. Lo que sigue requiere más rigor — estás listo."
            ]
          }
        }
      },
      // --- Boss ---
      {
        x: 9, y: 11,
        type: "boss",
        levels: ["boss-full-system"],
        requires_all_others: true,
        label: "El Sistema Completo",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "La pizarra central muestra un diagrama de sistema completo. Todo lo que aprendiste converge aquí.",
            "Demuestra que puedes conectar las piezas — el jefe quiere verlo funcionando."
          ]
        }
      },
      // --- Door ---
      {
        x: 10, y: 13,
        type: "door",
        target_room: "el-taller",
        requires_percent: 70,
        locked_dialogue: {
          speaker: "NARRADOR",
          lines: ["La puerta no cede. Aún quedan tareas pendientes en esta sala."]
        },
        unlocked_dialogue: {
          speaker: "NARRADOR",
          lines: ["El mecanismo hace click. La puerta se abre hacia el taller."]
        }
      }
    ]
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PHASE 2 — El Taller
  // ─────────────────────────────────────────────────────────────────────────
  "el-taller": {
    slug: "el-taller",
    name: "El Taller",
    subtitle: "Taller de ingeniería",
    tiles: [
      // Row 0
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      // Row 1
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 2
      [1, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 1],
      // Row 3
      [1, 0, 7, 7, 0, 0, 0, 12, 0, 0, 0, 0, 12, 0, 0, 0, 7, 7, 0, 1],
      // Row 4
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 5
      [1, 8, 0, 0, 1, 1, 0, 0, 0, 10, 10, 0, 0, 0, 1, 1, 0, 0, 8, 1],
      // Row 6
      [1, 0, 0, 0, 1, 5, 14, 0, 10, 10, 10, 10, 0, 5, 14, 1, 0, 0, 0, 1],
      // Row 7
      [1, 0, 4, 0, 0, 0, 0, 0, 10, 9, 10, 10, 0, 0, 0, 0, 0, 4, 0, 1],
      // Row 8
      [1, 0, 14, 0, 0, 0, 0, 0, 10, 10, 10, 10, 0, 0, 0, 0, 0, 14, 0, 1],
      // Row 9
      [1, 0, 0, 0, 1, 1, 0, 0, 0, 10, 10, 0, 0, 0, 1, 1, 0, 0, 0, 1],
      // Row 10
      [1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
      // Row 11
      [1, 0, 6, 6, 0, 0, 0, 0, 0, 13, 13, 0, 0, 0, 0, 0, 6, 6, 0, 1],
      // Row 12
      [1, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 1],
      // Row 13
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 14
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    spawn: { x: 10, y: 1, facing: "down" },
    palette: { wall: "#2d3436", floor: "#b2bec3", accent: "#0984e3" },
    objects: [
      // --- Puzzle Clusters ---
      {
        x: 2, y: 2,
        type: "puzzle_cluster",
        levels: ["create-table-sql", "select-where-order", "orm-model-mapping", "alembic-migration", "async-session-di"],
        label: "Rack de bases de datos",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Los servidores zumban con datos esperando ser estructurados. Tablas, consultas, migraciones.",
            "Cada LED parpadeante es una consulta sin respuesta. Dales forma."
          ]
        }
      },
      {
        x: 16, y: 2,
        type: "puzzle_cluster",
        levels: ["password-hashing", "rbac-decorator", "rls-policy", "decision-auth-strategy"],
        label: "Rack de seguridad",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Estos servidores manejan autenticación y permisos. Un error aquí y todo queda expuesto.",
            "Hashing, roles, políticas — la primera línea de defensa."
          ]
        }
      },
      {
        x: 5, y: 6,
        type: "puzzle_cluster",
        levels: ["first-test-assert", "testing-pyramid", "ci-pipeline-yaml", "cd-staging-deploy"],
        label: "Terminal de pruebas",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "La pantalla muestra un pipeline en rojo. Algo falló en CI — descubre qué.",
            "Tests, pirámide de testing, integración continua. Aquí se forja la confianza en el código."
          ]
        }
      },
      {
        x: 13, y: 6,
        type: "puzzle_cluster",
        levels: ["sql-injection-defense", "clean-architecture-layers", "structured-logging", "sse-streaming", "deploy-coolify"],
        label: "Terminal de producción",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Un monitor muestra logs en tiempo real. Cada línea cuenta una historia de lo que pasa en producción.",
            "Defensa, arquitectura limpia, logs, streaming, deploy — el arsenal completo."
          ]
        }
      },
      {
        x: 2, y: 11,
        type: "puzzle_cluster",
        levels: ["decision-monolith-micro"],
        label: "Estante de arquitectura",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Libros de patrones de diseño y post-its con diagramas. La decisión más importante: ¿monolito o microservicios?"
          ]
        }
      },
      // --- NPC ---
      {
        x: 9, y: 7,
        type: "npc",
        npc_id: "don-ramon",
        label: "Don Ramón",
        dialogues: {
          progress_0: {
            speaker: "DON RAMÓN",
            lines: [
              "El taller es donde se construye de verdad. Bases de datos, seguridad, testing — nada de juguetes.",
              "Los racks de servidores tienen ejercicios. Las terminales, desafíos de CI/CD. Empieza por donde quieras."
            ]
          },
          progress_50: {
            speaker: "DON RAMÓN",
            lines: [
              "Ya dominas la mitad del taller. Nada mal para alguien que venía de la oficina.",
              "¿Revisaste las decisiones arquitectónicas? Son las que marcan la diferencia entre junior y senior."
            ]
          },
          progress_100: {
            speaker: "DON RAMÓN",
            lines: [
              "El taller es tuyo. Cada servidor, cada test, cada deploy — lo dominas.",
              "El laboratorio espera. Ahí las máquinas piensan por sí mismas. ¿Estás listo para eso?"
            ]
          }
        }
      },
      // --- Boss ---
      {
        x: 9, y: 11,
        type: "boss",
        levels: ["boss-production-service"],
        requires_all_others: true,
        label: "Servicio en Producción",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "La pizarra central muestra el diagrama de un servicio completo: DB, auth, tests, deploy.",
            "Ensamblá todo. Un servicio real en producción — sin excusas, sin atajos."
          ]
        }
      },
      // --- Door ---
      {
        x: 10, y: 14,
        type: "door",
        target_room: "el-laboratorio",
        requires_percent: 70,
        locked_dialogue: {
          speaker: "NARRADOR",
          lines: ["La puerta no cede. Aún quedan tareas pendientes en esta sala."]
        },
        unlocked_dialogue: {
          speaker: "NARRADOR",
          lines: ["El mecanismo hace click. La puerta se abre hacia el laboratorio."]
        }
      }
    ]
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PHASE 3 — El Laboratorio
  // ─────────────────────────────────────────────────────────────────────────
  "el-laboratorio": {
    slug: "el-laboratorio",
    name: "El Laboratorio",
    subtitle: "Laboratorio de inteligencia artificial",
    tiles: [
      // Row 0
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      // Row 1
      [1, 10, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 10, 10, 1],
      // Row 2
      [1, 10, 5, 14, 0, 0, 12, 0, 0, 0, 0, 0, 0, 12, 0, 0, 5, 14, 10, 1],
      // Row 3
      [1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 1],
      // Row 4
      [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1],
      // Row 5
      [1, 0, 0, 0, 0, 1, 7, 0, 0, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 1],
      // Row 6
      [1, 8, 0, 0, 0, 0, 0, 0, 0, 11, 11, 0, 0, 0, 0, 0, 0, 0, 8, 1],
      // Row 7
      [1, 0, 0, 0, 0, 0, 0, 0, 11, 11, 11, 11, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 8
      [1, 0, 4, 14, 0, 0, 0, 0, 11, 9, 11, 11, 0, 0, 0, 0, 4, 14, 0, 1],
      // Row 9
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 11, 11, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 10
      [1, 8, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 8, 1],
      // Row 11
      [1, 0, 0, 0, 0, 1, 5, 14, 0, 0, 0, 0, 5, 14, 1, 0, 0, 0, 0, 1],
      // Row 12
      [1, 0, 12, 0, 0, 0, 0, 0, 0, 13, 13, 0, 0, 0, 0, 0, 0, 12, 0, 1],
      // Row 13
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 14
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    spawn: { x: 10, y: 1, facing: "down" },
    palette: { wall: "#1a1a2e", floor: "#16213e", accent: "#0f3460" },
    objects: [
      // --- Puzzle Clusters ---
      {
        x: 2, y: 2,
        type: "puzzle_cluster",
        levels: ["call-claude", "tool-use-basic", "prompt-cache-config", "react-agent-loop", "rag-embed-retrieve"],
        label: "Terminal Claude",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Esta terminal está conectada directamente a Claude. El cursor espera tu primer prompt.",
            "Llamadas, herramientas, caché, agentes, RAG — el lenguaje de la IA aplicada."
          ]
        }
      },
      {
        x: 16, y: 2,
        type: "puzzle_cluster",
        levels: ["output-guardrails", "deterministic-vs-agentic", "eval-assertions", "mcp-server-setup"],
        label: "Terminal de control",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Guardrails, evaluaciones, servidores MCP — aquí se domestica a la IA.",
            "Sin control, un agente es un riesgo. Con control, es una herramienta quirúrgica."
          ]
        }
      },
      {
        x: 6, y: 5,
        type: "puzzle_cluster",
        levels: ["openai-sdk-call", "google-genai-call", "langgraph-read-flow", "temporal-workflow-basic", "langgraph-vs-temporal"],
        label: "Rack multi-proveedor",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Estos servidores hablan con OpenAI, Google, LangGraph, Temporal. Un ecosistema completo.",
            "Dominar un proveedor es fácil. Dominar la elección entre ellos es sabiduría."
          ]
        }
      },
      {
        x: 6, y: 11,
        type: "puzzle_cluster",
        levels: ["multi-agent-dispatch", "human-in-the-loop", "cost-engineering"],
        label: "Consola de orquestación",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Múltiples agentes, supervisión humana, costos — la complejidad real de producción.",
            "Aquí aprendes a ser el director de orquesta, no solo un músico."
          ]
        }
      },
      {
        x: 13, y: 11,
        type: "puzzle_cluster",
        levels: ["prompt-injection-defense", "ai-observability-traces"],
        label: "Consola de seguridad IA",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Inyecciones de prompt, trazas de observabilidad — la defensa del laboratorio.",
            "Un agente en producción sin seguridad es una bomba de tiempo."
          ]
        }
      },
      // --- NPC ---
      {
        x: 9, y: 8,
        type: "npc",
        npc_id: "don-ramon",
        label: "Don Ramón",
        dialogues: {
          progress_0: {
            speaker: "DON RAMÓN",
            lines: [
              "El laboratorio. Aquí las máquinas piensan — o al menos, lo intentan.",
              "Cada terminal conecta con un modelo diferente. Cada rack es un flujo de trabajo. Explora con cuidado."
            ]
          },
          progress_50: {
            speaker: "DON RAMÓN",
            lines: [
              "Ya hablas con Claude como si fueran colegas. Bien.",
              "Pero no olvides la seguridad y la observabilidad. Un agente ciego es peor que ninguno."
            ]
          },
          progress_100: {
            speaker: "DON RAMÓN",
            lines: [
              "Dominas el laboratorio. Agentes, flujos, multi-proveedor, seguridad — todo.",
              "Solo queda la ciudad. El mundo real. Escala, negocio, arquitectura. Adelante."
            ]
          }
        }
      },
      // --- Boss ---
      {
        x: 9, y: 12,
        type: "boss",
        levels: ["boss-agent-acme"],
        requires_all_others: true,
        label: "Agente ACME",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "La pizarra muestra el caso ACME: un agente completo de producción para una PyME real.",
            "Todo lo que aprendiste en este laboratorio converge aquí. Construye el agente definitivo."
          ]
        }
      },
      // --- Door ---
      {
        x: 10, y: 14,
        type: "door",
        target_room: "la-ciudad",
        requires_percent: 70,
        locked_dialogue: {
          speaker: "NARRADOR",
          lines: ["La puerta no cede. Aún quedan tareas pendientes en esta sala."]
        },
        unlocked_dialogue: {
          speaker: "NARRADOR",
          lines: ["El mecanismo hace click. La puerta se abre hacia la ciudad."]
        }
      }
    ]
  },

  // ─────────────────────────────────────────────────────────────────────────
  // PHASE 4 — La Ciudad
  // ─────────────────────────────────────────────────────────────────────────
  "la-ciudad": {
    slug: "la-ciudad",
    name: "La Ciudad",
    subtitle: "El mundo real",
    tiles: [
      // Row 0
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      // Row 1
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 2
      [1, 0, 7, 7, 7, 0, 0, 0, 8, 0, 0, 0, 8, 0, 0, 0, 4, 4, 0, 1],
      // Row 3
      [1, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 0, 12, 0, 14, 14, 0, 1],
      // Row 4
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 5
      [1, 8, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 8, 1],
      // Row 6
      [1, 0, 0, 6, 0, 1, 0, 0, 0, 11, 11, 0, 0, 0, 1, 0, 5, 14, 0, 1],
      // Row 7
      [1, 0, 0, 6, 0, 0, 0, 0, 11, 11, 11, 11, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 8
      [1, 0, 0, 0, 0, 0, 0, 0, 11, 9, 11, 11, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 9
      [1, 0, 0, 0, 0, 1, 0, 0, 0, 11, 11, 0, 0, 0, 1, 0, 0, 0, 0, 1],
      // Row 10
      [1, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 1],
      // Row 11
      [1, 0, 5, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 14, 0, 1],
      // Row 12
      [1, 0, 0, 0, 0, 0, 12, 0, 0, 13, 13, 13, 0, 0, 12, 0, 0, 0, 0, 1],
      // Row 13
      [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 1],
      // Row 14
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    spawn: { x: 10, y: 1, facing: "down" },
    palette: { wall: "#2c3e50", floor: "#ecf0f1", accent: "#e74c3c" },
    objects: [
      // --- Puzzle Clusters ---
      {
        x: 2, y: 2,
        type: "puzzle_cluster",
        levels: ["horizontal-scaling", "compose-vs-k8s", "k8s-pod-deploy", "feature-flags-toggle", "incident-response"],
        label: "Rack de infraestructura",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Tres racks de servidores zumban con el tráfico de una empresa real. Escalar no es opcional.",
            "Kubernetes, feature flags, respuesta a incidentes — bienvenido a la realidad."
          ]
        }
      },
      {
        x: 16, y: 2,
        type: "puzzle_cluster",
        levels: ["monorepo-navigation", "billing-stripe-basics", "public-api", "sdk-design"],
        label: "Escritorio de negocio",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Facturas de Stripe, documentación de APIs públicas, diseño de SDKs. El código genera dinero aquí.",
            "Monorepos, billing, APIs públicas — donde la ingeniería se encuentra con el negocio."
          ]
        }
      },
      {
        x: 3, y: 6,
        type: "puzzle_cluster",
        levels: ["code-review-checklist", "read-ai-generated-code", "build-vs-buy", "adr-template", "system-design"],
        label: "Biblioteca de arquitectura",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Estantes llenos de ADRs, checklists de code review, diagramas de sistema.",
            "Leer código, decidir qué construir, documentar por qué — el pensamiento senior."
          ]
        }
      },
      {
        x: 16, y: 6,
        type: "puzzle_cluster",
        levels: ["technical-communication", "serverless-tradeoffs", "cache-embeddings", "zero-downtime-deploy", "reading-production-code"],
        label: "Terminal de producción avanzada",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Comunicación técnica, serverless, caché, zero-downtime — los problemas que nadie te enseña en clase.",
            "Aquí se forjan los ingenieros que mantienen sistemas vivos 24/7."
          ]
        }
      },
      // --- NPC ---
      {
        x: 9, y: 8,
        type: "npc",
        npc_id: "don-ramon",
        label: "Don Ramón",
        dialogues: {
          progress_0: {
            speaker: "DON RAMÓN",
            lines: [
              "La ciudad. Aquí no hay ejercicios de práctica — hay problemas reales de empresas reales.",
              "Infraestructura, negocio, arquitectura, producción. Elige tu camino y demuestra lo que sabes."
            ]
          },
          progress_50: {
            speaker: "DON RAMÓN",
            lines: [
              "Ya navegas la ciudad como un veterano. Pero la mitad de los retos aún te esperan.",
              "¿Revisaste la biblioteca de arquitectura? Las decisiones importan más que el código."
            ]
          },
          progress_100: {
            speaker: "DON RAMÓN",
            lines: [
              "Lo lograste. Toda la ciudad, toda la plataforma — dominada.",
              "Ya no eres un aprendiz. Eres ingeniero. Sal y construye algo que importe."
            ]
          }
        }
      },
      // --- Boss ---
      {
        x: 9, y: 12,
        type: "boss",
        levels: ["boss-final"],
        requires_all_others: true,
        label: "El Desafío Final",
        intro_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "La pizarra más grande que has visto. Un sistema completo: infra, negocio, IA, arquitectura.",
            "Esto es todo. Demuestra que puedes diseñar, construir y operar un servicio de producción completo."
          ]
        }
      },
      // --- Stairs (end) ---
      {
        x: 10, y: 13,
        type: "door",
        target_room: null,
        requires_percent: 100,
        locked_dialogue: {
          speaker: "NARRADOR",
          lines: ["Las escaleras están bloqueadas. La ciudad aún tiene secretos por descubrir."]
        },
        unlocked_dialogue: {
          speaker: "NARRADOR",
          lines: [
            "Las escaleras se iluminan. Has completado todo el recorrido.",
            "El mundo real te espera afuera. Ya tienes las herramientas — ahora úsalas."
          ]
        }
      }
    ]
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

export function getRoomBySlug(slug) {
  return ROOMS[slug] || null;
}

export function getFirstRoom() {
  return ROOMS["la-oficina"];
}

export const ROOM_ORDER = ["la-oficina", "el-taller", "el-laboratorio", "la-ciudad"];
