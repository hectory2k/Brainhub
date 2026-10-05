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

---

## Familia 4: observabilidad

### Por qué

Sin tracing, debuggear es adivinar. Con tracing, sabés
exactamente en qué capa falla (carga, retrieval, contexto, LLM).

### Patrón de trace_id en BrainHub

1. Generar trace_id = str(uuid.uuid4())[:8] al inicio
2. Loguear en cada hito con el prefijo [trace_id]
3. Log a archivo (logs/rag.log), no a stdout
4. print() para UX, logger.info() para trazabilidad
5. logging.basicConfig solo en __main__

### Ejemplo real (preguntar.py)

```
15:42:10 [03e31e2c] START pregunta='salud' nicho=SALUD top_k=5
15:42:10 [03e31e2c] docs_cargados=13
15:42:10 [03e31e2c] bm25_resultados=5 top_score=1.608
15:42:10 [03e31e2c] contexto_chars=1911
15:43:09 [03e31e2c] respuesta_chars=108 elapsed=58.54s
15:43:09 [03e31e2c] DONE
```

### Hallazgo del primer trace

99% del tiempo es el LLM, no el pipeline:
- retrieval (docs + BM25 + contexto): ~80ms
- LLM (gemma:2b CPU Termux): ~58s
- prompt eval: 34 ms/token
- eval output: 1586 ms/token

Conclusión: para acelerar el RAG, atacar el modelo, no BM25.

### Cómo leer los logs

```
# Todo lo de una query
grep "03e31e2c" logs/rag.log

# Tiempos de las últimas 20 queries
grep "elapsed=" logs/rag.log | tail -20

# Detectar queries lentas
grep "elapsed=" logs/rag.log | awk -F'elapsed=' '{print $2}' | sort -rn | head
```

### Pendientes

- [ ] Replicar en api.py
- [ ] Agregar trace_id a módulos internos (opcional)
- [ ] Métricas agregadas (p50, p95 de elapsed)

---

### Los defaults con Path() escapan al sed de string literal (2026-09-29)

Contexto: el fix del 2026-09-27 reemplazó 20 defaults con sed sobre
el literal `'data/analisis_consolidado.duckdb'`. Un grep ampliado
posterior encontró 1 más que el sed no vio:

    str(RAIZ / "data" / "analisis_consolidado.duckdb")

El sed busca strings literales; `Path() / "..."` construye el path
en runtime, así que el string "data/analisis_consolidado.duckdb"
nunca aparece junto en el código fuente.

Regla: los grep/sed de defaults deben cubrir 3 formas:
1. String literal: `'data/...duckdb'`
2. Path construction: `Path(...) / "data" / "...duckdb"`
3. os.path.join: `os.path.join(..., "data", "...duckdb")`

Verificar con: `grep -rn "analisis_consolidado" --include="*.py" .`
(desde la raíz, no solo subcarpetas conocidas).

Referencias:
- Fix: 94d90d3
- Aprendido en: 2026-09-29

---

### Serializar objetos: a_dict() explícito > ClassEncoder con __dict__ (2026-09-30)

Contexto: al diseñar el Chunker surgió cómo serializar List[Chunk] a JSON.

Patrón malo (encontrado en tutoriales):
    class ClassEncoder(json.JSONEncoder):
        def default(self, o):
            if hasattr(o, '__dict__'):
                return o.__dict__
            else:
                super().default(self)  # ← BUG: pasa self, no o

Problemas del patrón malo:
1. Bug silencioso: en el else, recursión con el encoder en vez de o.
2. No maneja datetime, Path, set, Decimal → falla sin avisar.
3. Depende de __dict__ → rompe con __slots__.

Patrón elegido (consistente con timestamps.py):
    @dataclass
    class Chunk:
        ...
        def a_dict(self) -> Dict:
            return {'chunk_id': self.chunk_id, ...}

Ventajas:
- Explícito: controlás exactamente qué se serializa
- Testeable: chunk.a_dict() == {...} es trivial
- Consistente con SegmentoTemporal.a_dict() ya existente
- No agrega clase encoder global al repo

Alternativas válidas:
- dataclasses.asdict() + json.dumps() si crecen los tipos
- Encoder custom con isinstance para datetime/Path

Regla: metadata debe ser JSON-serializable (str/int/float/bool/list/dict).
Nada de set, Path, datetime crudos. Convertir antes:
str(path), dt.isoformat(), list(mi_set).

Referencias:
- Aprendido en: 2026-09-30
- Aplicado a: brainhub/chunking/chunker.py (pendiente)

---

### Re-analizar > auditar JSON viejo (2026-10-04)

Contexto: el análisis de P1rDVQIAOKI mostraba 'habia: 25' en top-1
términos clave. Investigué stopwords.json, es_transcript, V6.5
durante 1h antes de descubrir que el JSON guardado era de una
corrida anterior con código previo.

Regla para futuras auditorías:
1. Si un análisis guardado parece tener bugs, **re-analizar primero**
2. Comparar antes/después con el código actual
3. Si el bug desaparece → era artefacto de corrida vieja
4. Si persiste → entonces auditar código

Ahorra horas de auditar código que ya funciona.

Corolario: en BrainHub los JSONs guardados NO son evidencia del
comportamiento actual del código. Son snapshots históricos.

Referencias:
- Descubierto en: sesión auditoría V6.5
- Aplicado a: análisis de transcripts YouTube
- Commit fix posterior: 4b4cc34

---

## Familia 2: diagnóstico con evidencia

Bugs que parecen una cosa y son otra. La causa real solo aparece
al medir.

### Medir antes de proponer fix (2026-10-04)

Bug #2 (nicho mal clasificado) parecía "clasificador mal entrenado".
Hipótesis iniciales (todas falsas):
- Hardcodes sospechosos en los módulos → eran docstrings y tests
- Corrector de coherencia reasignando nichos → solo toca secundarios
- Diccionario con términos ambiguos → diccionario limpio

Causa real: substring matching sin word boundary. 'ot' dentro de
'otro', 'social', etc. Solo apareció al medir substring vs wordbound
en los 3 videos con un script de línea base.

Lección: grep muestra dónde buscar, no qué está mal. El código mata
hipótesis. Medir con un script antes de tocar.

Referencias:
- Descubierto en: sesión auditoría V6.5, bug #2
- Aplicado a: clasificador de nichos

---

## Familia 3: rendimiento en Termux

Optimizaciones no obvias que hacen la diferencia en Moto G56.

### Precompilar regex no es opcional (2026-10-04)

Fase 1 del fix de word boundary compilaba re.compile() dentro del
loop de términos. Con 8 nichos × 70 términos × 3 métricas × 99
análisis = ~500k compilaciones. Termux en Moto G56 tardaba 5-15s
por análisis.

Fix: precompilar una vez en __init__, guardar como self._patrones.
Bajó a ~1.5s (10× mejora). Para 99 análisis es la diferencia entre
20 min y 2.5 min.

Regla: si un patrón se repite en un loop, precompilarlo. La caché
de Python (re._cache) es 512 patrones — se desborda con diccionarios
grandes.

Referencias:
- Descubierto en: sesión auditoría V6.5, bug #2
- Aplicado a: modulos/ponderacion_nichos.py, modulos/nicho_multietiqueta.py

---

### Curaduría manual > automático para dominios específicos (2026-10-04)

Bug #3 (sentimiento) parecía resoluble con SentiWordNet + OMW
automáticamente. En la práctica, el lexicón resultante tenía:
- 4.5% palabras ambiguas (pos y neg ambos > 0.3)
- Faltantes críticos médicos: "adverso", "ineficaz", "mortalidad"
- Ruido semántico: "partido" (positivo), "tratamiento" (negativo)

30 min de curaduría manual con criterio médico superaron 3h de
automatización. El automático sirve como base (~2900 palabras),
la curaduría agrega precisión donde importa.

Regla: para dominios con vocabulario específico (médico, legal,
financiero), curaduría manual gana. Para sentimiento general,
automatización es suficiente.

Referencias:
- Descubierto en: sesión auditoría V6.5, bug #3a
- Aplicado a: lexico_medico_es.json

---

### sed en Termux: a\ no agrega salto de linea (2026-10-05)

Bug: `sed -i "75a\\ texto"` en BusyBox/Termux pega la línea nueva a
la siguiente sin `\n`, corrompiendo el archivo (Python igual parsea
si la línea pegada empieza con #, generando bugs silenciosos).

Solución: usar Python para editar archivos:

    lines = p.read_text().splitlines(keepends=True)
    lines.insert(74, "nueva linea\n")
    p.write_text(''.join(lines))

Regla: en Termux, evitar `sed a\` para agregar líneas. Usar Python
o `sed` con `s/$/\n.../` explícito.

Referencias:
- Descubierto en: sesión auditoría V6.5, bug #3a
- Aplicado a: modulos/sentimiento_es.py

---
