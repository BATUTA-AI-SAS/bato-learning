# Cómo se estructura el contenido

Lo lee el `content_loader.py` al arrancar (y al ejecutar `make seed`).

## Por cada módulo, dos o tres archivos

```
app/content/{TRACK}/{EXT_ID}.md              # cuerpo del módulo (obligatorio)
app/content/{TRACK}/{EXT_ID}.exercises.yaml  # ejercicios (opcional)
app/content/{TRACK}/{EXT_ID}.quizzes.yaml    # quizzes (opcional)
```

`{TRACK}` es la letra (`A`, `B`, `C`, `D`, `E`, `F`). `{EXT_ID}` es `A01`, `B03`,
`F-FIN-01`, etc.

## Frontmatter requerido en el `.md`

```yaml
---
ext_id: A01
slug: interpreter-and-uv
track: A
ord: 1
title: "Cómo Python ejecuta tu archivo, y por qué usamos uv"
summary: "Una línea que aparece debajo del título."
estimated_minutes: 30
---

# Cuerpo en Markdown a partir de aquí

Cada módulo cubre las secciones obligatorias de `_team/ARCHITECTURE.md` §4.
```

## `*.exercises.yaml`

```yaml
- slug: hello-world
  title: "Tu primer print"
  runner: pyodide                 # pyodide | backend
  kind: code                      # code | design
  prompt: |
    Haz que el código imprima exactamente: `hola mundo`
  hint: |
    Pista: `print(...)`.
  starter: |
    print("...")
  test: |
    out = __cap.getvalue().strip()
    assert out == "hola mundo", f"esperaba 'hola mundo', obtuve {out!r}"
    print("✓ correcto")
  solution: |
    print("hola mundo")
```

## `*.quizzes.yaml`

```yaml
- slug: mutability-basics
  question: |
    ¿Cuál de estos tipos es **inmutable**?
  explanation: |
    Las tuplas, strings, ints y floats son inmutables. Listas, dicts y sets son
    mutables.
  options:
    - text: "list"
      correct: false
      feedback: "Las listas son mutables."
    - text: "tuple"
      correct: true
      feedback: "Sí. Una vez creada, no la modificas en sitio."
    - text: "dict"
      correct: false
      feedback: "Los dicts son mutables."
```

## Convenciones

- Idioma de prosa: **español**. Identificadores en código: **inglés**.
- No `foo`/`bar`. Usa los personajes canónicos de `_team/SHARED.md` §2.
- Si introduces un término, asegúrate de que esté en el glosario de `SHARED.md`.
- El cuerpo del módulo (`.md`) **no** repite los ejercicios — el loader los añade desde
  los YAML al renderizar.
- Markdown soporta tablas, code fences, blockquotes. El renderer es markdown-it
  (CommonMark + tables + strikethrough).
