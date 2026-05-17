"""Glossary tooltip injection.

Replaces the *first occurrence* of each key term in rendered HTML with
``<abbr class="term" title="...">term</abbr>``.

Rules:
- Only the first occurrence per term per render call.
- Never touches text inside ``<code>``, ``<pre>``, ``<a>``, or ``<abbr>``.
- Case-sensitive match using the exact key as written.

The glossary below extracts the 35 most critical terms for the
Excel-to-Python audience from ``_team/SHARED.md §1``.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Canonical glossary — (term, short definition)
# Order matters: longer/more-specific terms first to avoid partial matches.
# ---------------------------------------------------------------------------
GLOSSARY: list[tuple[str, str]] = [
    # 1.1 Language & process
    ("Intérprete de Python",  "Programa (python3/CPython) que lee un .py, lo compila a bytecode y lo ejecuta."),
    ("bytecode",              "Representación intermedia binaria del código Python; se cachea en __pycache__/."),
    ("Pyodide",               "CPython compilado a WebAssembly; corre dentro del navegador sin instalación."),
    ("uv",                    "Gestor de proyectos Python (Astral): reemplaza pip + virtualenv + pip-tools."),
    ("pip",                   "Herramienta clásica para instalar paquetes Python; uv la reemplaza en este curso."),
    ("virtualenv",            "Carpeta aislada con su propio Python y paquetes; evita conflictos entre proyectos."),
    ("entorno virtual",       "Caja aislada de dependencias de un proyecto. Excel: como un perfil de usuario independiente."),
    ("pyproject.toml",        "Archivo de configuración del proyecto Python: nombre, versión, dependencias y herramientas."),
    ("uv.lock",               "Registro exacto de cada versión instalada; garantiza que todos usan el mismo entorno."),
    ("AST",                   "Abstract Syntax Tree: árbol que representa la estructura del código antes de compilarlo."),
    ("wheel",                 "Paquete Python precompilado (.whl); se instala sin compilar, como un .exe de Windows."),
    ("__pycache__",           "Carpeta donde Python guarda el bytecode compilado para no recompilar en cada ejecución."),
    ("dis",                   "Módulo de Python que muestra el bytecode de una función; útil para entender el intérprete."),
    ("IDE",                   "Integrated Development Environment: editor con autocompletado, debug y linting integrados."),
    ("PEP",                   "Python Enhancement Proposal: documento que propone cambios al lenguaje; PEP 8 = estilo de código."),
    # 1.2 Types & mutability
    ("Inmutable",             "El objeto no se puede modificar después de creado (int, float, str, tuple…)."),
    ("Mutable",               "El objeto se puede modificar en su lugar (list, dict, set…)."),
    ("identidad",             "Comparada con `is`; dos referencias al mismo objeto en memoria."),
    ("IEEE 754",              "Estándar que define cómo los procesadores guardan decimales; explica por qué 0.1+0.2 ≠ 0.3."),
    ("iterador",              "Objeto con __iter__ y __next__; entrega un elemento a la vez sin cargar todo en memoria."),
    ("generador",             "Función con yield que produce valores uno a uno; versión perezosa de una lista."),
    ("lazy",                  "Evaluación postergada: el valor se calcula solo cuando se necesita, no al definirse."),
    ("from __future__",       "Importa comportamientos de versiones futuras de Python, p.ej. anotaciones lazy."),
    ("sys.path",              "Lista de directorios donde Python busca módulos al hacer import; como el PATH del sistema."),
    ("id()",                  "Función que devuelve la dirección en memoria de un objeto en CPython."),
    ("is",                    "Operador que compara identidad (mismo objeto en memoria), no igualdad de valor."),
    # 1.3 Web & architecture
    ("HTTP",                  "Protocolo request/response entre cliente y servidor; sin estado entre requests."),
    ("API",                   "Contrato de endpoints que un servidor expone; en este curso = API HTTP JSON."),
    ("Router",                "Capa que define endpoints HTTP: valida entrada, llama al servicio."),
    ("Servicio",              "Capa que implementa lógica de negocio; orquesta repos, no conoce HTTP."),
    ("Repo",                  "Capa que ejecuta queries concretas; recibe AsyncSession, devuelve modelos."),
    ("Migración",             "Archivo Alembic versionado que describe el delta entre dos estados del schema."),
    ("DNS",                   "Sistema que traduce un nombre de dominio a una IP; como una agenda telefónica de internet."),
    ("TCP",                   "Protocolo de red que garantiza entrega ordenada de bytes entre cliente y servidor."),
    ("TLS",                   "Transport Layer Security: cifra la conexión TCP; convierte http en https."),
    ("JWT",                   "JSON Web Token: token firmado que transporta identidad del usuario sin estado en servidor."),
    ("HMAC",                  "Hash-based Message Authentication Code: firma criptográfica que verifica integridad de un mensaje."),
    ("Bearer",                "Esquema de autorización HTTP: el header dice 'Bearer <token>' para identificarse."),
    ("cookie",                "Valor que el servidor deposita en el navegador para recordar al usuario entre requests."),
    ("WebSocket",             "Canal bidireccional persistente entre cliente y servidor; para comunicación en tiempo real."),
    ("streaming",             "Envío de datos en trozos continuos sin esperar la respuesta completa; SSE es un ejemplo."),
    ("ASGI",                  "Asynchronous Server Gateway Interface: contrato entre servidor y app Python async (FastAPI/uvicorn)."),
    ("event loop",            "Bucle que gestiona tareas async en Python; ejecuta una tarea a la vez, alterna en esperas de IO."),
    ("Pydantic",              "Librería que valida y convierte datos usando type hints; como validación de celdas en Excel."),
    ("decorador",             "Función que envuelve a otra para añadirle comportamiento; en Python se escribe con @."),
    # 1.4 Data
    ("Schema",                "Conjunto de tablas, columnas, tipos y restricciones de una base de datos."),
    ("Transacción",           "Bloque de queries que se commitea o aborta como un todo."),
    ("RLS",                   "Row-Level Security: política Postgres que filtra filas por variable de sesión."),
    ("ORM",                   "Object-Relational Mapper: convierte filas de tabla en objetos Python y viceversa."),
    ("DeclarativeBase",       "Clase base de SQLAlchemy 2.x; cada subclase que hereda de ella mapea una tabla."),
    ("MVCC",                  "Multi-Version Concurrency Control: Postgres permite lecturas simultáneas sin bloquear escrituras."),
    ("WAL",                   "Write-Ahead Log: registro de cambios que Postgres escribe antes de modificar los datos reales."),
    ("PITR",                  "Point-In-Time Recovery: restaurar la BD al estado exacto de un momento pasado usando el WAL."),
    # 1.5 Frontend
    ("DOM",                   "Document Object Model: árbol de nodos en memoria que el navegador construye al recibir HTML."),
    ("SPA",                   "Single Page Application: app web donde el render ocurre en el navegador con JavaScript."),
    ("bundle",                "Archivo JS compilado y empaquetado por una herramienta como Vite o webpack para el navegador."),
    # 1.6 Agents & LLMs
    ("Agente",                "Loop prompt→modelo→tool_use→tool_result que termina en end_turn o corte."),
    ("Harness",               "Código alrededor del SDK que gestiona el loop, hooks, skills y permisos."),
    ("Skill",                 "Archivo Markdown con frontmatter que describe una receta o procedimiento."),
    ("Tool",                  "Función externa que el modelo puede invocar con argumentos JSON."),
    ("prompt caching",        "Marca cache_control en bloques del prompt para reducir coste en hits."),
    ("tool_use",              "Bloque que emite el modelo cuando quiere llamar una función; contiene name e input JSON."),
    ("tool_result",           "Bloque que envía tu código con el resultado de ejecutar una tool; empareja por tool_use_id."),
    ("content block",         "Unidad de contenido tipada en la messages API: text, tool_use, tool_result o thinking."),
    ("ephemeral cache",       "Cache de prompt con ttl corto (5 m por defecto, 1 h si se declara explícito)."),
    ("extended thinking",     "Cadena de razonamiento interna del modelo antes de responder; activa con budget_tokens."),
    ("Tenant",                "Cliente/organización en una app multitenant; dimensión obligatoria en todo."),
    ("MCP",                   "Model Context Protocol: estándar que estandariza cómo un harness expone tools."),
    # 1.7 Deterministic vs agentic
    ("tramo determinístico",  "Parte del flujo donde la salida es función cerrada de la entrada; auditable."),
    ("tramo agéntico",        "Parte del flujo que exige razonamiento contextual; caro, no determinístico."),
    ("fallback humano",       "Ruta del workflow donde el agente delega a un humano ante baja confianza."),
    # 1.8 Track F business vocabulary
    ("3-way match",           "Comparación orden de compra ↔ recepción ↔ factura antes de aprobar pago."),
    ("DSO",                   "Days Sales Outstanding: días promedio que tarda el cliente en pagar."),
    ("EOQ",                   "Economic Order Quantity: cantidad de pedido que minimiza el costo total."),
    ("ROP",                   "Reorder Point: nivel de inventario que dispara una nueva orden de compra."),
    ("BANT",                  "Budget, Authority, Need, Timing — criterios de calificación de leads."),
    ("ICP",                   "Ideal Customer Profile: descripción del cliente ideal en variables observables."),
    ("Idempotency key",       "Clave única por side-effect agéntico; siempre incluye tenant_id."),
    # 1.9 Editor & runtime
    ("REPL",                  "Read-Eval-Print-Loop: modo interactivo de Python; evalúa cada línea al instante."),
    ("namespace",             "Dict aislado por ejercicio donde corre el código del usuario."),
]

# ---------------------------------------------------------------------------
# Tags whose text content must NOT be annotated
# ---------------------------------------------------------------------------
_SKIP_TAGS = re.compile(
    r"<(code|pre|a|abbr)(\s[^>]*)?>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)


def apply_glossary_tooltips(html: str) -> str:
    """Inject ``<abbr>`` for the first occurrence of each glossary term.

    Uses a placeholder strategy to avoid touching content inside skip-tags:
    1. Extract skip-tag spans and replace them with unique placeholders.
    2. For each glossary term, replace only the very first plain-text match.
    3. Restore placeholders.
    """
    if not html:
        return html

    # Step 1 — stash skip-tag content
    placeholders: list[str] = []

    def _stash(m: re.Match) -> str:
        idx = len(placeholders)
        placeholders.append(m.group(0))
        return f"\x00SKIP{idx}\x00"

    safe_html = _SKIP_TAGS.sub(_stash, html)

    # Step 2 — inject abbr for first occurrence of each term
    for term, definition in GLOSSARY:
        escaped_def = definition.replace('"', "&quot;")
        pattern = re.compile(re.escape(term))
        replacement = f'<abbr class="term" title="{escaped_def}">{term}</abbr>'
        new_html, count = pattern.subn(replacement, safe_html, count=1)
        if count:
            safe_html = new_html

    # Step 3 — restore stashed spans
    for idx, original in enumerate(placeholders):
        safe_html = safe_html.replace(f"\x00SKIP{idx}\x00", original)

    return safe_html
