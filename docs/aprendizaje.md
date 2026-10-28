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

---

### Output confuso != bug funcional (2026-10-04)

Bug #3b: el reporte mostraba "SENTIMIENTO POR HABLANTE: DESCONOCIDO:
0.34 (331 segmentos)". El cálculo estaba correcto (0.34 es el sentimiento
real) pero el output era engañoso porque DESCONOCIDO es el nombre del
hablante, no del sentimiento.

Lección: revisar los outputs con ojos de usuario, no de dev.
El nombre interno DESCONOCIDO se justifica en el código (bucket por
defecto) pero al leerse en el reporte parece indicar que el análisis
falló.

Regla: si un output puede interpretarse mal, cambiarlo aunque el
cálculo sea correcto. La claridad es parte del fix.

Referencias:
- Descubierto en: sesión auditoría V6.5, bug #3b
- Aplicado a: analisis_completo_v6.5.py (2 lugares)

---

### No mostrar campos que mienten (2026-10-04)

Bug #4: analisis temporal mostraba "TESTIMONIO_GENERAL" en 99%
de las secciones. El clasificador funcionaba, pero los patrones
no representaban habla natural en transcripts.

Ante un clasificador 99% default, hay 2 opciones:
- Arreglar los patrones (heuristico, subjetivo, sin techo claro).
- Quitar del output (KISS, honesto, sin ruido).

Elegimos quitar. Regla: si un campo no aporta informacion real,
es mejor no mostrarlo que mostrarlo mal.

Corolario: la polaridad por seccion SI varia y SI aporta.
No todo el analisis temporal era inutil, solo el contexto.

Referencias:
- Descubierto en: sesion auditoria V6.5, bug #4
- Aplicado a: analisis_completo_v6.5.py

---
---

### git log antes de diagnosticar (2026-10-05)

Bug #4 se creyó reabierto en la sesión del 2026-10-05, pero ya estaba
cerrado por commit 89f00dd (mismo día, 21:22). El prompt de retoma decía
"Bug #4 PROXIMO" cuando en realidad estaba cerrado. La desincronización
entre código y retoma hizo que se aplicara un segundo fix (c755329)
sobre el mismo bug sin saberlo.

Resultado: dos soluciones complementarias, no contradictorias.
- 89f00dd: quitar contexto_predominante del reporte humano (MD/consola).
- c755329: valor interno honesto (NO_CLASIFICADO en vez de TESTIMONIO_GENERAL).

Ambos son correctos: el humano no ve ruido, la máquina ve honestidad.

Lección: SIEMPRE `git log` antes de diagnosticar. La retoma puede estar
desactualizada. Un síntoma que parece "bug vivo" puede ser en realidad
"bug cerrado + retoma vieja".

Regla complementaria: si vas a crear un archivo nuevo, verificar
estructura de docs/ primero. Los archivos canónicos de doc viven en docs/.

Referencias:
- Commit 89f00dd (fix original, 21:22)
- Commit c755329 (fix complementario, 22:30)
- Commit d270b41 (docs intrusos en raíz, corregido)
---

### Tomar los primeros N no es neutral (2026-10-07)

Bug #7: `citas[:2]` para decidir si invocar el LLM. El orden de las
citas no refleja su calidad ni su longitud. Con 22 citas útiles, si
las 2 primeras eran cortas, el sistema se abstenía.

Regla: cuando una lista no está ordenada por el criterio que importa,
NO uses slicing ciego. Filtrá por criterio primero (acá: longitud >=30),
después tomá top N.

Aplica a: cualquier selección de "mejores N" de una lista no ordenada.

Referencias:
- Commit (Bug #7)
- ME_lJOHAPUo: caso testigo

---

### Reutilizar antes de reinventar (2026-10-08)

Feature #1 (Citas con peso semántico) requería segmentar texto. En lugar
de crear una nueva lógica de segmentación, se reutilizó el Chunker MVP
ya integrado, ajustando `max_oraciones=3`.

Regla: Si un módulo existente (como Chunker) ya resuelve el 80% del
problema (segmentación + metadata de provenance), úsalo como base y
agrega la lógica específica (scoring) encima. Evita duplicar código de
parsing/segmentación.

Aplica a: Cualquier nueva feature que requiera manipulación de texto
que ya esté cubierta por un componente existente.

Referencias:
- Commit 034f812 (Feature #1: Extractor de citas semánticas)
- brainhub/citas/extractor.py

---

## Entry points de BrainHub (2026-10-09)

| Comando | Entrada | Salida |
|---|---|---|
| `procesar <URL YT>` | URL YouTube | Transcript .txt en /sdcard/Download/ |
| `procesar <archivo.pdf>` | PDF | Texto combinado (vía procesar_paper.sh) |
| `procesar <texto>` | texto | ~/tmp/texto_directo.txt |
| `procesar <URL GH>` | GitHub | guía a analizar_github |
| `analizar <txt>` | transcript/texto | JSON + MD + SQLite + DuckDB |
| `analizar_github <user/repo>` | repo GitHub | texto_combinado + análisis |
| `preguntar <query>` | query | respuesta RAG |
| `consolidar <db>` | SQLite | DuckDB consolidado |

**Regla:** procesar y analizar son DOS pasos (YouTube/PDF). NO unificar sin
dolor real. `analizar_github` es flujo propio (todo-en-uno).

**Lecciones técnicas:**

1. **Aliases en shells no-interactivos:** `command -v analizar` no detecta el
   alias cuando el script corre desde bash no-interactivo (cron, systemd, script).
   Llamar siempre a paths absolutos de scripts `.py`.

2. **Termux no tiene `/tmp` escribible:** usar `mktemp` (que respeta `$TMPDIR`)
   o `~/archivo.new` en lugar de `/tmp/archivo`.

3. **`sed -i` con `a\` y `\n` es frágil en Termux:** preferir `awk` con
   redirección a `mktemp` + `mv`.

4. **Indentación al pegar en nano/Termux:** el pegador bracketed a veces come
   espacios al inicio. Verificar siempre con `sed -n` después de pegar.

5. **Auditoría de entry points:** antes de tocar cualquier script, mapear qué
   comandos existen (`ls ~/.local/bin/`, `grep alias ~/.bashrc`), qué hacen
   (`type`, `cat`), y quién llama a quién (`grep -rn`).

6. **Heredocs largos en Termux:** el bracketed paste puede meter espacios en
   lugar de saltos de línea. Para archivos >50 líneas, preferir `printf '%s\n'`
   con líneas separadas por `\`, o escribir en bloques chicos. Verificar con
   `git check-ignore -v` — NO confiar en `head`/`cat`, pueden renderizar raro
   por el ancho de terminal y mostrar líneas "pegadas" que en realidad no lo están.

7. **Conflictos de merge sin resolver:** `grep -c "^<<<<<<<"` es un chequeo
   rápido de CI. Si está en un `.gitignore`, rompe silenciosamente TODAS las
   reglas desde el `=======` en adelante (git interpreta `=======` como patrón
   literal). Correr siempre `git diff --check` antes de commitear.

8. **Señales de scoring normalizadas:** todas las señales de un score
   ponderado deben estar en el mismo rango. Mezclar `polaridad` (bruta, 0-N)
   con `polaridad_norm` (0-1) multiplica por 100 el peso real de una sola
   señal. Regla: si los pesos suman 1.0, las señales deben estar en [0, 1]
   o en [0, 100] uniformemente, no mezcladas.

9. **Falsos positivos de duplicación:** antes de arreglar "duplicados",
   verificar con `repr()` que los textos sean idénticos. Chunks distintos
   pueden contener la misma frase en contextos distintos. El display
   truncado (`[:40]...`) hace parecer duplicados donde no los hay.
   Verificar con `grep -c "frase" fuente.txt` primero.

## 2026-10-09 — FTS no está disponible en DuckDB/Termux

**Error:** HTTP 404 al intentar INSTALL fts.

**Causa:** DuckDB no distribuye extensiones para `linux_arm64_android`.

**Solución:** Usar `bm25s` (Python) en lugar de FTS nativo.

**Lección:** Verificar soporte de plataforma antes de adoptar extensión DuckDB.

## 2026-10-10 08:26 - Aprendizaje Bug #9: clasificación de nichos

- Un clasificador de nichos debe tener taxonomía completa; si falta DEPORTES/COMBATE,
  los textos deportivos pueden caer en GENERAL o en nichos incorrectos.
- Keywords genéricas como `market` causan falsos positivos en FINANZAS.
- Antes de parchar, validar con tests sintéticos:
  - `ufc fight market`
  - `boxing fight market`
  - `combat sports market`
- El tier/nicho incorrecto se propaga a chunks si no se corrige aguas arriba.

## 2026-10-10 22:10 - Aprendizaje Bug #9: Clasificación de nichos y keywords genéricas

1. **Taxonomía completa es obligatoria**: Si un clasificador carece de una categoría obvia (ej: DEPORTES), los textos de ese dominio caerán en GENERAL o en nichos incorrectos por coincidencias léxicas.
2. **Peligro de keywords genéricas**: Palabras como "market" en FINANZAS causan falsos positivos en contextos deportivos ("fight market", "betting market"). Solución: usar n-gramas específicos o eliminar términos demasiado amplios.
3. **Propagación de errores aguas abajo**: Un nicho mal detectado en la fase inicial del pipeline se propaga como `tier` a los chunks en DuckDB. Corregir el dato en la DB sin arreglar el detector es solo un parche temporal.
4. **Validación antes de parchear**: Siempre probar el detector con casos sintéticos límite (ej: 'ufc fight market' vs 'stock market investment') para asegurar que el fix no rompe la clasificación legítima.

## 2026-10-11 — Pipeline GitHub y C extensions en Termux

### analizar_github no consulta default_branch
- Asume rama main hardcodeada al armar la URL del ZIP de GitHub.
- Repos con default_branch = master (u otro) bajan solo lo que hay en main.
- Caso real: lvusyy/biliSub -> main tiene solo LICENSE (1 archivo),
  master tiene el código completo (10 archivos, 3069 líneas).
- Limitación conocida, no regresión: la línea 1386 de BITACORA documenta
  analizar_github.sh usuario/repo main como default. El fix es un feature:
  leer default_branch vía API GitHub antes de armar la URL del ZIP.
- Lección: nunca asumir rama por defecto de un servicio externo.

### Pipeline semántico aplicado a código = ruido
- El pipeline NLP de BrainHub trata cualquier texto como prosa narrativa.
- Aplicado a .py:
  - Términos clave = keywords sintácticas (self, def, str, import, args).
  - Citas clave = líneas de código partidas.
  - Hablantes detectados = falsos positivos desde LICENSE.
  - Sentimiento = -0.24, sin sentido (el código no tiene sentimiento).
- Lección: el tipo de archivo importa.
- Fix pendiente: detector por extensión + pipeline específico para código.

### C extensions en Termux/Android ARM64
- Compilan OK pero tardan. Verificado en Python 3.14 / android_24_arm64_v8a:
  - lxml 6.1.3, pillow 12.3.0, brotli 1.2.0, pycryptodomex 3.24.0.
- Tiempo total: ~5-10 minutos.
- Wheels cacheados en ~/.cache/pip/wheels/.
- Atajo: pkg install python-lxml python-pillow + venv --system-site-packages.

### Bilibili desde Termux (exploración)
- lvusyy/biliSub (master) es Python puro, sin Chrome CDP ni Node.js.
- --no-asr evita openai-whisper y PyTorch.
- import whisper está dentro de _init_whisper_model(), no en top-level.
- Output VTT nativo -> parseable directo por BrainHub.
- Pendiente: cookies, video target real.

## 2026-10-11 — Pipeline GitHub y C extensions en Termux

### analizar_github no consulta default_branch
- Asume rama main hardcodeada al armar la URL del ZIP de GitHub.
- Repos con default_branch = master (u otro) bajan solo lo que hay en main.
- Caso real: lvusyy/biliSub -> main tiene solo LICENSE (1 archivo),
  master tiene el código completo (10 archivos, 3069 líneas).
- Limitación conocida, no regresión: la línea 1386 de BITACORA documenta
  analizar_github.sh usuario/repo main como default. El fix es un feature:
  leer default_branch vía API GitHub antes de armar la URL del ZIP.
- Lección: nunca asumir rama por defecto de un servicio externo.

### Pipeline semántico aplicado a código = ruido
- El pipeline NLP de BrainHub trata cualquier texto como prosa narrativa.
- Aplicado a .py:
  - Términos clave = keywords sintácticas (self, def, str, import, args).
  - Citas clave = líneas de código partidas.
  - Hablantes detectados = falsos positivos desde LICENSE.
  - Sentimiento = -0.24, sin sentido (el código no tiene sentimiento).
- Lección: el tipo de archivo importa.
- Fix pendiente: detector por extensión + pipeline específico para código.

### C extensions en Termux/Android ARM64
- Compilan OK pero tardan. Verificado en Python 3.14 / android_24_arm64_v8a:
  - lxml 6.1.3, pillow 12.3.0, brotli 1.2.0, pycryptodomex 3.24.0.
- Tiempo total: ~5-10 minutos.
- Wheels cacheados en ~/.cache/pip/wheels/.
- Atajo: pkg install python-lxml python-pillow + venv --system-site-packages.

### Bilibili desde Termux (exploración)
- lvusyy/biliSub (master) es Python puro, sin Chrome CDP ni Node.js.
- --no-asr evita openai-whisper y PyTorch.
- import whisper está dentro de _init_whisper_model(), no en top-level.
- Output VTT nativo -> parseable directo por BrainHub.
- Pendiente: cookies, video target real.

## 2026-10-11 — Ingesta masiva de PDFs con BrainHub

### Fallback > Error en pipelines de ingesta
- Cuando una transformación puede fallar, NUNCA devolver vacío.
- Copiar el intermedio crudo es mejor que fallar.
- Caso: 55/141 PDFs cayeron a fallback (descolumnar rechazó) -> crudo copiado íntegro.
- El corpus sirve igual: el análisis funciona sobre texto crudo, no requiere columnas.
- Aplicación: parsers, migraciones, ETL.

### Import > Subprocess cuando el destino hace sys.exit()
- Si el script destino llama sys.exit(1) al fallar, invocarlo por subprocess mata el batch.
- Alternativa: importarlo, atrapar la excepción y hacer fallback.
- Caso: descolumnar.py hace sys.exit(1) cuando es_valido() == False.
- Fix: from descolumnar import procesar_columnas + try/except + fallback.

### Alias no existen en subprocesos no-interactivos
- alias analizar='python3 ...' funciona en shell interactiva.
- En bash -c '...' (nohup, cron, scripts) -> command not found.
- Solución: usar SIEMPRE el path completo en scripts.
- Regla: alias para humanos, paths completos para automatización.

### setsid nohup + notificación --ongoing para sobrevivir Android
- Android mata procesos en background a los ~10-15 min.
- termux-wake-lock NO alcanza por sí solo.
- Combo robusto:
  - termux-notification --id batch --ongoing (notificación no-swipeable)
  - setsid nohup bash -c '...' (disociado del shell padre)
  - termux-wake-lock (CPU despierta)
- Verificación: pgrep -f proceso antes de asumir que murió.
- Resultado: batch de 46 archivos sobrevivió sin perder progreso.

### Deduplicar por hash de contenido, no por nombre
- md5sum archivos | sort | uniq -w32 -D detecta duplicados reales.
- PDFs de Anna's Archive vienen con sufijos (1), (2) -> mismo contenido.
- Los 3 Python-para-análisis-de-datos (8) eran idénticos.
- Fix: dedup antes de analizar (ahorra tiempo de cómputo + espacio).

### Nombre corto es crítico (255 bytes por componente)
- Límite en ext4/F2FS (Android): 255 bytes por componente.
- Sufijos derivados (_analisis_completo.json = 23 chars) -> stem máx ~80 chars.
- PDFs con nombres de 240+ chars fallan al crear derivados.
- Fix: slugify() al entrar al pipeline.
- Regla: sanitizar input externo AL BORDE, no en el medio.

### comm es frágil con Unicode/espacios
- comm -23 <(find ...) <(ls ... | sed ...) falla con ñ, á, ¡, espacios dobles.
- Fix: while IFS= read -r txt; do [ ! -f "$json" ] && echo "$txt"; done < lista.txt.
- Check explícito por archivo > comparación de listas.

### pdftotext -layout gana a markitdown para papers
- pdftotext: rápido (ms), preserva columnas, predecible, solo PDFs.
- markitdown: lento (s), linealiza (pierde columnas), múltiples formatos.
- Decisión: pdftotext para papers; markitdown como fallback para formatos ricos.

### Análisis de código != análisis de prosa
- Los 3 Python duplicados dominaron el top de términos del corpus:
  datos, array, dtype, pandas, nan, dataframe.
- citas_clave en v1.pdf = 55% código (fragmentos de tokenizer.encode, lm_head).
- Lección: detector por extensión + filtro de código en extracción de citas.
- Refuerza hallazgo previo: analizar_github sobre .py = ruido.


## 2026-10-12 — Ollama persistente en Termux + qwen2.5:1.5b

### Ollama tarda ~10s en arrancar
- Chequeos con sleep 5 dan falsos negativos. Usar espera activa con curl en loop.

### setsid nohup mata Ollama
- En Termux/Android, setsid desacopla del shell y Android mata antes.
- Fix: nohup ollama serve > log 2>&1 & (sin setsid).

### termux-services + runit es el camino
- pkg install termux-services + reiniciar Termux.
- $PREFIX/var/service/ollama/run con variables.
- sv-enable ollama + sv up ollama. Persistente a cierres, auto-restart.

### Variables críticas en el script run
- OLLAMA_NUM_PARALLEL=1
- OLLAMA_MAX_LOADED_MODELS=1
- OLLAMA_KEEP_ALIVE=30m

### svlogd falla con lock viejo
- rm -f $PREFIX/var/log/sv/ollama/lock antes de arrancar.

### sv status falla sin SVDIR exportado
- export SVDIR=$PREFIX/var/service en ~/.bashrc.

### brainhub-llama mata el proceso en Moto G56
- 2.1 GB REPACK, Android mata al asignar.
- Fix: qwen2.5:1.5b (Q4_K_M, 1 GB).

### qwen2.5:1.5b: 7.5x más rápido
- Cliente directo con num_predict=30: ~16s.
- En pipeline: ~76-148s según tamaño del prompt.
- Cuello real: velocidad de generación en CPU ARM (~2s/token).

### citas_clave vs citas_clave_semanticas
- abstract_llm.py leía citas_clave (vacío).
- Fix: citas_clave_semanticas or citas_clave.

### RAM_MINIMA_GB hardcodeado
- abstract_llm.py: 2.0. brainhub_config.json: 1.5. El código ignora el config.

### Segmentación sin puntuación
- YouTube auto-captions sin puntuación → 1 chunk gigante.
- Criterio sano: puntos/char > 0.005.

## 2026-10-12 — Ollama persistente en Termux + qwen2.5:1.5b

### Ollama tarda ~10s en arrancar
- Chequeos con sleep 5 dan falsos negativos. Usar espera activa con curl en loop.

### setsid nohup mata Ollama
- En Termux/Android, setsid desacopla del shell y Android mata antes.
- Fix: nohup ollama serve > log 2>&1 & (sin setsid).

### termux-services + runit es el camino
- pkg install termux-services + reiniciar Termux.
- $PREFIX/var/service/ollama/run con variables.
- sv-enable ollama + sv up ollama. Persistente a cierres, auto-restart.

### Variables críticas en el script run
- OLLAMA_NUM_PARALLEL=1
- OLLAMA_MAX_LOADED_MODELS=1
- OLLAMA_KEEP_ALIVE=30m

### svlogd falla con lock viejo
- rm -f $PREFIX/var/log/sv/ollama/lock antes de arrancar.

### sv status falla sin SVDIR exportado
- export SVDIR=$PREFIX/var/service en ~/.bashrc.

### brainhub-llama mata el proceso en Moto G56
- 2.1 GB REPACK, Android mata al asignar.
- Fix: qwen2.5:1.5b (Q4_K_M, 1 GB).

### qwen2.5:1.5b: 7.5x más rápido
- Cliente directo con num_predict=30: ~16s.
- En pipeline: ~76-148s según tamaño del prompt.
- Cuello real: velocidad de generación en CPU ARM (~2s/token).

### citas_clave vs citas_clave_semanticas
- abstract_llm.py leía citas_clave (vacío).
- Fix: citas_clave_semanticas or citas_clave.

### RAM_MINIMA_GB hardcodeado
- abstract_llm.py: 2.0. brainhub_config.json: 1.5. El código ignora el config.

### Segmentación sin puntuación
- YouTube auto-captions sin puntuación → 1 chunk gigante.
- Criterio sano: puntos/char > 0.005.

## 2026-10-12/14 — Convención de nombres, controles y evidencia

### Una convención de nombres rota apaga los controles
- guardia_contaminacion.sh hace JOIN por nombre exacto: las 25 filas con nombre recortado no pasaban el JOIN y nadie las vio.
- Regla: UNA función que derive el nombre del video y un invariante terminos_raw ⊆ analysis en chequeo_salud.sh.

### Lo auditado no se borra: es la decisión
- Los huérfanos son el registro de que la convención se partió; borrarlos destruye la evidencia.
- Secuencia: auditar -> decidir convención -> migrar con UPDATE + mapeo -> verificar. DELETE solo al final y con copia previa.

### replace no es parseo
- replace('_ES','') corta en cualquier posición: ES_FORZADO quedó FORZADO.
- Usar regex anclada. Los IDs de YouTube miden 11 caracteres (pueden llevar _ y -): ^Transcript_(.{11})_.

### Dos escritores, dos filtros
- reconstruir_db.sh filtra stopwords y términos vacíos; v6.5 incremental inserta el top 20 sin filtrar (13-19 filas vs 20 por video).
- Al menos 25 términos extra de los huérfanos son stopwords. El filtro debe aplicarse en un solo lugar.

### Productor y consumidor derivan nombres por separado
- v6.5 deriva el nombre en 3 puntos (l.853, 867, 918) y buscaba Transcript_Transcript_<id>_timestamps.vtt. Mismo patrón del Bug #8.

### Lo documentado no es evidencia
- "+timestamp" y "[x] Blindar ingesta" no tenían respaldo en el código. Verificar con un grep o un conteo antes de escribirlo en el estado.

### Validar la respuesta externa antes de escribirla
- Una página de error de Google (500) se guardó como transcripción y generó chunks. Guardia de entrada en v6.5 (exit 1).

### Probar la hipótesis antes de actuar
- "La basura movió el nicho" se refutó con 10 líneas (DEPORTES con y sin firma).
- duckdb sin -readonly crea una base vacía; NOT IN con NULL da 0 filas falso (usar NOT EXISTS).

## 2026-10-14 — El retoma es deuda + backups como evidencia

### El retoma es deuda (2026-10-14)

Tres incidentes en 2 semanas donde el retoma no reflejaba el estado real:
- Bug #4 (7-oct): creímos que estaba abierto, ya estaba cerrado por otro fix.
- Bug #5 (7-oct): citas "random" venían de output legacy, no de HEAD.
- Bug #8 (14-oct): creímos que Chunker era huérfano, ya estaba integrado
  desde el 7-oct con 2151 chunks en DB y persistir_chunks.py.

Cada vez, arrancamos una sesión en falso por 30-60 minutos hasta descubrir
que el trabajo ya estaba hecho, o que el diagnóstico se basaba en evidencia vieja.

**Regla (protocolo de inicio de sesión, ahora en el retoma):**
1. Correr `git log --oneline -15` y `git status` ANTES de diagnosticar.
2. Leer docs/prompt_retoma.md COMPLETO (no solo el bloque pegable).
3. Leer BITACORA.md (últimas 100 líneas).
4. Contrastar el "próximo" del retoma con los commits recientes.
5. Si hay divergencia → PARAR, sincronizar retoma, después trabajar.

**Por qué funciona:** `git log` no miente. El retoma sí (por desactualización).

**Costo de no hacerlo:** 3 sesiones con diagnósticos basados en estado obsoleto.

### Los backups .PRE_* son evidencia, no basura (2026-10-14)

Los archivos `.PRE_<CAMBIO>` (ej. `.PRE_BUG7`, `.PRE_PROTOCOLO`,
`.PRE_VIDEOID`) son la fotografía del estado anterior a cada modificación.
No son ruido.

- Permiten auditar la evolución sin depender de git (útil si el commit
  no se hizo o si el archivo se modificó fuera del repo).
- Documentan la intención: `.PRE_BUG7` cuenta que hubo un bug #7.
- Cumplen la misma función que la decisión de "no borrar huérfanos"
  (Addendum 3, 14-oct): preservar la evidencia para que los controles
  no se apaguen.

**Regla:** los `.PRE_*` van a `legacy/` cuando ya cumplieron su ciclo,
nunca se borran sin decisión explícita. Coherente con la convención
de `legacy_scripts_backup/`.

### Documentar un fix no cierra el bug — documentar el estado real sí

Complemento de la lección del 13-oct ("lo documentado no es evidencia"):
un bug puede estar cerrado en código y abierto en el retoma (o al revés).
La única fuente de verdad al iniciar sesión es `git log` + `git status`.

Referencias:
- Sesión 2026-10-14 (ésta)
- Bug #4, #5, #8 (incidentes registrados)

### El assert protege el archivo, no al programador (2026-10-14)

En esta sesión, un `assert` en un script de edición atrapó un mismatch
entre el texto buscado (con fecha) y el texto real (sin fecha). El archivo
NO se escribió mal: el script falló limpio, y solo hubo que corregir el
assert y reintentar.

**Regla:** los asserts en scripts de modificación de archivos no son
"por si acaso". Son el punto de control entre "voy a cambiar" y "cambié".
Si un assert falla, no se pierde trabajo: se pierde un intento.

**Corolario:** el backup va ANTES del write_text, no después. Si el
write falla, el backup ya está hecho. Si el assert falla, el archivo
original está intacto.

**Anti-patrón:** escribir primero y verificar después. Si el write
ocurre antes del assert, un fallo puede dejar el archivo a medias.

Referencias:
- Sesión 2026-10-14 (bug del assert con fecha faltante)


### 🐛 Error recurrente: Módulo Python `duckdb` no instalado (2026-10-17)

**Problema:**
- Se intentó usar `import duckdb` en scripts Python, pero el módulo no está instalado en Termux.
- Error: `ModuleNotFoundError: No module named 'duckdb'`
- Esto ocurrió 3 veces en la sesión del 17-oct (migrar_huerfanos, diagnosticar_dyhkxt, unificar_dyhkxt).

**Solución:**
- Usar el **CLI de DuckDB** (`duckdb` en terminal) en lugar del módulo Python.
- Sintaxis: `duckdb "$DB" -readonly -c "SELECT ..."` o `duckdb "$DB" < script.sql`
- Para scripts bash con variables: `duckdb "$DB" << SQLEOF ... SQLEOF`

**Lección operativa:**
- Antes de escribir scripts Python con `import duckdb`, verificar si el módulo existe: `python -c "import duckdb"`
- Si no existe, usar el CLI directamente (ya está instalado y funciona en Termux).
- No intentar instalar el módulo Python sin consultar primero (puede romper dependencias o no estar disponible para ARM64/Android).

**Referencia:**
- Sesión 2026-10-17: Opción 1 (migración huérfanos) y Opción C (deduplicación DyhkXT_dgdk).

### Lección: El retoma es deuda viva y la idempotencia es obligatoria (2026-10-19)
- **Deuda documental**: Un bloque de retoma desactualizado lleva a diagnosticar bugs ya resueltos (ej. convención de nombres, Bug #8). El protocolo de inicio (git log + diff contra el retoma) es obligatorio para evitar trabajo fantasma.
- **Idempotencia en ingesta**: Cualquier script que alimente la DB desde archivos externos debe usar `INSERT OR IGNORE` (o `UPSERT`). Sin esto, re-ejecutar el pipeline tras un fallo o un rebuild duplicará registros o abortará por violación de PRIMARY KEY.
- **Parcheo seguro**: Usar Python con `assert src.count(viejo) == 1` antes de `replace` es la única forma confiable de modificar scripts en Termux sin que `sed` rompa caracteres especiales o `cat >` sobrescriba por error.

### Lección: Los scripts standalone no se migran sin inventario (2026-10-19)
- Antes de migrar rutas o modelos en scripts de batch, verificar si son orquestados o standalone. Los standalone pueden estar en uso manual y una migración masiva puede romper flujos ad-hoc.
- Documentar los scripts legacy (con rutas hardcodeadas) en lugar de migrarlos de inmediato. La migración completa requiere un inventario de uso y un plan de testing manual.
- El patrón "productor y consumidor derivan por separado" (Bug #8) se cierra con `os.environ.get('BRAINHUB_DB', ...)` en Python y `${BRAINHUB_DB:-...}` en bash. Los scripts legacy que no lo usan son deuda técnica documentada, no bugs activos.

### 📜 Historial de Decisiones y Hallazgos (2026-10-13/14)
### 📝 Hallazgos y Ajustes Recientes (2026-10-13)

**1. Incidente: Inyección de "Error 500" en fuentes .txt**
- **Causa**: Basura de Google ("Error 500 (Server Error)!!1500...") inyectada en archivos `.txt` fuente.
- **Impacto**: 5 chunks contaminados en DuckDB (4 en `_en`, 1 en `_es`).
- **Resolución**: Limpieza con regex + backup. Archivos `.txt` saneados.
- **Profilaxis**: Los 5 chunks se mantienen en DB como evidencia forense (no se borran).

**2. Blindaje de Ingesta**
- `chequeo_salud.sh` ahora rechaza archivos con firma "Error 500" (usar comillas simples para evitar expansión de `!!` en bash).
- Validación obligatoria antes de procesar cualquier `.txt` nuevo.

**3. Lección Aprendida**
- Deduplicar por hash de contenido, no por nombre de archivo (evitar inflado por variantes de idioma falsas).
- Mantener evidencia de errores como casos de prueba permanentes (profilaxis de aprendizaje).

---

### 🔎 Timestamps y nombres (2026-10-13)
- DB real: /sdcard/Download/analisis_consolidado.duckdb (brainhub.duckdb de la raíz era una base vacía).
- `chunks` NO tiene minuto (solo start_char/end_char); segmentos_timestamp no existe. Dos generaciones del pipeline: Transcript_<id>_ES.txt (sin tiempos, alimenta chunks) y yt_lib/yt_transcript.py (jsonl + timestamped en /sdcard/Download/corpus/<id>/), que nadie llama.
- Alineador de prueba (~/temp/probar_alineacion.py): 6 palabras normalizadas contra el VTT ancla 82/93 chunks de DyhkXT_dgdk (.en.vtt). Sin ancla -> NULL. Diseño previsto: tabla chunk_tiempo(chunk_id, t_inicio, metodo).
- 30 videos = 26 fuentes. ONrw_JAOHvo: traducciones reales. DyhkXT_dgdk: 3 variantes con hashes distintos y chunks en inglés (hipótesis sin probar: mismo texto). Un md5 exacto no las detecta.
- Lecciones: duckdb sin -readonly crea una base vacía; NOT IN con NULL da 0 filas falso; productor y consumidor derivan nombres por separado (patrón Bug #8).

### 🧭 Convención de nombres y controles (2026-10-14)
- DECISIÓN: no se borra lo auditado (25 huérfanos en terminos_raw/progreso, 5 chunks con firma). Es la evidencia para decidir la convención. Copia: analisis_consolidado.duckdb.PRE_REPROCESO_ONRW_20261013.
- 3 convenciones: nombre completo Transcript_<id>_ES (analysis, chunks, rebuild, archivos); recortado Transcript_<id> (v6.5 hasta l.918, l.867, consolidar.py:31); ID YouTube de 11 chars (yt_lib, .vtt).
- La convención rota apagó el control: guardia_contaminacion.sh hace JOIN por nombre exacto y no veía los 25 huérfanos.
- El rebuild filtra stopwords y v6.5 incremental no: al menos 25 términos extra de los huérfanos son stopwords. Falta contar los que no.
- Recomendado (abierto): clave = nombre completo; youtube_id por regex ^Transcript_(.{11})_; filtro en la escritura incremental.
- NO correr reprocesar_sanos.sh ni pipeline_db.sh hasta decidir. v6.5 l.918 ya usa el nombre completo (backup .PRE_VIDEOID).
- Detalle: BITACORA.md 2026-10-13/14 y docs/aprendizaje.md.

### Lección: Los estados 'pendiente' son deuda técnica, no trabajo en progreso (2026-10-19)
- Un video que queda en `pendiente` indefinidamente no es "pausado", es un fallo silencioso del pipeline (archivo vacío, Error 500, o crash). 
- La estrategia correcta no es intentar "reprocesarlo" ciegamente (lo que genera más basura), sino: 
  1. Diagnosticar la causa raíz en el archivo fuente.
  2. Si el archivo es irrecuperable, moverlo a `_descartados` y marcar el registro en la DB como `descartado_error` (UPDATE, no DELETE total, para preservar la auditoría).
  3. Limpiar `terminos_raw` y `chunks` asociados para que no contaminen las búsquedas BM25.
- Esto mantiene el pipeline frugal y la DB libre de "fantasmas" que inflan métricas y rompen joins.

### Lección: El puente minuto → chunks requiere alineación por contenido, no por nombre (2026-10-20)
- Un archivo llamado `*_ES*` puede contener texto en inglés (y viceversa). Confiar en el nombre del archivo para elegir el VTT de alineación lleva a falsos negativos (0% de cobertura).
- La solución frugal: normalizar ambos textos (VTT y chunk) a minúsculas, sin acentos y solo alfanuméricos, y buscar una secuencia de 6 palabras. Esto es O(N) y tolera diferencias de puntuación o traducción ligera.
- Agregar columnas `t_inicio` y `t_fin` directamente a la tabla `chunks` es más eficiente para el RAG que crear una tabla `chunk_tiempo` separada (evita JOINs en cada consulta de búsqueda).
