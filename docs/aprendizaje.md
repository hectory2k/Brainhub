# Aprendizaje — patrones de bug y debugging en BrainHub

Catálogo vivo de lecciones aprendidas debugging este proyecto.
No es bitácora (esos son eventos fechados). Esto es conocimiento
acumulado que aplica en cualquier momento.

---

## Familia 1: bugs silenciosos

Nada se rompe. Nada tira error. La calidad se degrada sin avisar.

### Ejemplos reales del proyecto

| Fecha | Bug | Efecto silencioso |
|---|---|---|
| 2026-09-28 | 20 defaults con path relativo a DB corrupta | Funcionaba con env var, fallaba sin ella (cron, terminales nuevas) |
| 2026-09-28 | tests.yml con BRAINHUB_DB a path inexistente | 10/10 tests de DuckDB skipeados en CI, decia verde |
| 2026-09-29 | doc[:200] en rag_simple.py | 49/95 docs sin separador ||SEP||, LLM con chunks mutilados |

### Cómo detectarlos

1. Grepear el patrón específico en TODO el repo, no solo en el archivo donde buscás
2. Medir el impacto en datos reales (no asumir)
3. Verificar que el verde sea real: si un test skipea, no es verde

### Greps recurrentes para auditar

```
# Paths rotos (defaults, configs)
grep -rn "data/analisis_consolidado\|BRAINHUB_DB" . --include="*.py" --include="*.yml" --include="*.sh"

# Truncamientos sospechosos
grep -rn "[[:digit:]]*]" modulos/ scripts/ *.py | grep -v "print\|stderr\|_log"

# Tests que skipean silenciosamente
grep -rn "pytest.skip" tests/
```

---

## Familia 2: debugging de RAG

Basado en "Debugging a Broken RAG System". Aplicable al pipeline
preguntar.py -> rag_simple -> self_rag -> LLM.

### Flujo real a auditar

```
Query -> Cargar documentos (nicho, filename)
  -> RAGSimple.buscar (BM25)
  -> Armado de contexto (metadata + doc)
  -> Prompt al LLM
  -> Respuesta
```

### Checklist por síntoma

| Síntoma | Capa probable | Módulo a revisar |
|---|---|---|
| Respuesta inventada | Contexto / LLM | prompt + chunks |
| Respuesta vieja | Retrieval | integrar_duckdb |
| Keyword exacta perdida | Retrieval | rag_simple._tokenizar |
| Mucho ruido | Precision | rag_simple.buscar (umbral) |
| Confianza mal calibrada | self_rag | mejor_score / 10 (magic) |
| Chunks sin contexto | Chunking | timestamps.py |
| No se donde fallo | Observabilidad | no hay tracing |

### Pendientes conocidos del RAG

- [ ] Tracing con trace_id en preguntar.py y api.py
- [ ] Normalizar confianza en self_rag.py (el /10 es arbitrario)
- [ ] Inyectar metadata al prompt (filename + nicho)
- [ ] Tests de regresion para ||SEP|| en docs

---

## Familia 3: grep cruzado

### Regla

Cuando buscás un patrón, no asumas una sola construcción ni
un solo tipo de archivo.

### Variantes a buscar siempre

- String literal: 'data/x.duckdb'
- Path composition: str(BASE_DIR / 'data' / 'x')
- f-string: f'{BASE_DIR}/data/x'
- os.path.join: os.path.join(BASE_DIR, 'data', 'x')

### Tipos de archivo a incluir

- *.py, *.sh, *.yml, *.yaml, *.json, *.toml
- Makefile, Dockerfile, .env*
- .github/workflows/*.yml
- docs/*.md (a veces la doc apunta a paths rotos)

### Residuales de refactors

- *.bak.*, *.orig, *.old, *.pre_*
- Buscar aunque .gitignore los ignore: pueden existir localmente
  y confundir el grep

---

## Meta-lecciones

1. Antes de tocar, medir. Cada fix de esta semana se justificó
   con un número concreto (49/95, 10/10, 1782 -> 1842).
2. El verde puede ser mentira. Un CI que skipea tests es peor
   que un CI que falla, porque no te enterás.
3. Los truncamientos [:N] son sospechosos por defecto. Casi
   nunca son "para no inflar X", casi siempre cortan estructura.
4. Grepear el patrón, no el archivo. El bug del CI no apareció
   hasta que grepeamos YAML además de Python.
5. Anotar el por qué, no solo el qué. "1842" solo no dice nada;
   "1782 -> 1842 (+60, análisis del día)" cuenta la historia.

---

## Cómo usar este documento

- Antes de un refactor grande: leer Familia 1 y 3
- Antes de tocar el RAG: leer Familia 2
- Cuando aparece un bug raro: buscar aquí primero
- Cuando aprendés algo nuevo: agregarlo con fecha y número
