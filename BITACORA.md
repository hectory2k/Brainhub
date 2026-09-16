# Bitácora de BrainHub

Registro cronológico de bugs, fixes, descubrimientos y lecciones.

> **Filosofía:** El contenido real revela lo que los tests no ven.

---

## 2026-09-15 — Video industrial revela 5 bugs

### Contexto

Procesé un video de ciberseguridad industrial:
- **Transcript:** ME_lJOHAPUo_ES
- **Tamaño:** 453,628 caracteres (8.7x más grande que el de Kubernetes)
- **Segmentos:** 1,829
- **Tiempo de análisis:** 1.7s

### Bugs descubiertos

#### 1. HABLA incompleto

- **Síntoma:** `cierto: 512` y `muchas: 124` como términos top
- **Causa:** muletillas no estaban en `stopwords.json`
- **Fix:** +20 términos al nicho HABLA

#### 2. Scoring por presencia (no frecuencia)

- **Síntoma:** `malware (18x)` pesaba igual que `bitcoin (1x)`
- **Causa:** `score += 1` por keyword (0/1, sin frecuencia)
- **Fix:** `score += min(matches, 5)`
- **Impacto:** CIBERSEGURIDAD pasó de 18 a 140 puntos

#### 3. CIBERSEGURIDAD desbalanceada

- **Síntoma:** Solo 9 términos, sin `ciberseguridad`, `industrial`, `planta`
- **Fix:** ampliada a 34 términos (scada, ics, ot, ransomware, ...)

#### 4. FINANZAS con falsos positivos

- **Síntoma:** `banco` matcheaba en "banco de batería"
- **Síntoma:** `mercado` matcheaba en "mercado de herramientas"
- **Síntoma:** `precios` matcheaba en cualquier contexto
- **Fix:** quitados los 3 términos ambiguos

#### 5. AI_SAFETY retorno temprano

- **Síntoma:** CIBERSEGURIDAD=140 perdía contra AI_SAFETY=6
- **Causa:** `if scores['AI_SAFETY'] >= 3: return 'AI_SAFETY'`
- **Historia:** este bug ya se había arreglado el 2026-09-10 para el video de Kubernetes, pero volvió al recuperar el validador desde git (commit 2dfb79c)
- **Fix:** eliminado el retorno temprano + test de regresión

### Resultado

| Métrica | Antes | Después |
|---------|-------|---------|
| Nicho industrial | TECNOLOGIA | **CIBERSEGURIDAD** ✅ |
| SQLite re-análisis | UNIQUE constraint | ✅ OK |
| Tests | 112 | **116** (+4 regresión) |
| Términos top | cierto, muchas | ciberseguridad, planta, industrial |

### Lección

> Sin test de regresión, los fixes no son permanentes.
>
> El retorno temprano de AI_SAFETY había vuelto al recuperar el validador desde git (commit 2dfb79c), sin que nadie lo notara. Solo lo detectamos con un video industrial real.
>
> **Por eso:** `tests/test_nicho_regresion.py` previene regresión.

### Commits

- `f582bc5` — fix(nicho): scoring ponderado + SQLite idempotente + AI_SAFETY

---

## 2026-09-14 — Limpieza + Documentación + Ollama

### Logros

- ✅ 29 symlinks (scripts unificados en `~/proyectos/nlp/scripts/`)
- ✅ `duckdb/` borrado (3.8 GB recuperados)
- ✅ README v7.0.0 completo (11 secciones)
- ✅ TUTORIAL.md (2 flujos: YouTube + Papers)
- ✅ ROADMAP.md público
- ✅ CONTRIBUTING.md
- ✅ Cross-promo: VigiSalud + Argentina Hub + denoise
- ✅ Ollama verificado: 4 modelos (phi3:mini, llama3.2:3b, gemma:2b, tinyllama)

### Decisión

No integrar Ollama todavía — esperar sesión dedicada.

---

## 2026-09-13 — Networking + Demo

### Logros

- ✅ Alianza con Cristian Rojas (autor de denoise)
- ✅ Contacto con Dardo Valdez (MCP + RAG + 20 PDFs)
- ✅ Video asciinema grabado y online
- ✅ Demo reproducible (`demo.sh`)
- ✅ README con Autor + LinkedIn

### Contexto

Compartí BrainHub en el grupo de Cristian. Respondió con estrella en GitHub y me pidió un tutorial corto. Grabé video con `asciinema`.

### Links

- Video: https://asciinema.org/a/EqWi4xkuVw3Bvsp0
- Repo: https://github.com/hectory2k/Brainhub

---

## 2026-09-11 — Fix ñ + Guardias + Validador federado

### Bugs resueltos

| # | Bug | Fix |
|---|-----|-----|
| 1 | `años` → `anos` en 3 lugares | `normalizar_preservando_enie()` |
| 2 | `TECNOLOGIA` cuando era `FINANZAS` | Regex `\b` + `PRIORIDAD_NICHO` |
| 3 | `word`/`paper` en preguntas | Validador federado |

### Logros

- ✅ 6 guardias orquestadas (2 nuevas + 2 refactor)
- ✅ Validador federado (5 fuentes de conocimiento)
- ✅ 112 tests (antes 60)
- ✅ Fixture de regresión en `tests/fixtures/regresion_economia/`

### Lección

> Un output bugueado es oro.
>
> El fixture de `informe_deudores` capturó 3 bugs que se fueron arreglando en 2 días.

---

## Cómo usar esta bitácora

**Buscar bugs por nombre:**
```bash
grep -i "AI_SAFETY" BITACORA.md
grep -i "scoring" BITACORA.md
```

**Ver qué pasó un día:**
```bash
grep -A 20 "## 2026-09-15" BITACORA.md
```

**Ver todos los bugs resueltos:**
```bash
grep -E "^### Bug|^#### [0-9]" BITACORA.md
```

---

**Filosofía:** Documentar el "por qué", no solo el "qué".

---

## 2026-09-15 — DuckDB: del infierno de Python a la CLI

### Contexto

La DB `analisis_consolidado.duckdb` quedó inaccesible:

- Creada con versión nightly (storage version 999)
- La CLI estable 1.5.5 solo lee hasta v68
- `uv pip install duckdb --pre` intentaba compilar NumPy 2.5.3 en Termux → fallaba

Además, el directorio `duckdb/` había sido borrado el 2026-09-14 (3.8 GB), dejando solo el cache de sdists en `~/.cache/uv/`.

### Síntomas

    IO Error: Trying to read a database file with version number 999,
    but we can only read versions between 64 and 68.

    Failed to build `numpy==2.5.3`
    Call to `mesonpy.build_wheel` failed (exit status: 1)

### Solución

1. `pkg install duckdb` → CLI 1.5.5 (sin compilar nada)
2. Reconstruir la DB desde los 19 JSONs con `read_text` + `json_extract`
3. Replicar el filtro de `reconstruir.py` en SQL puro:
   - `es_generico()` → `length(term) >= 3 AND term NOT IN (stopwords)`
   - Deduplicación → `QUALIFY row_number() OVER (PARTITION BY video, term) = 1`
4. Script versionado en `scripts/reconstruir_db.sh`
5. Symlink en `~/.local/bin/reconstruir_db.sh`


### Esquema resultante

| Tabla | Filas | Rol |
|-------|-------|-----|
| `analysis` | 19 | 1 fila por JSON (documento, nicho, sentimiento) |
| `terminos_raw` | 274 | 1 fila por término (video, term, frequency) |
| `progreso` | 19 | estado por video |
| `stopwords` | 596 | lista usada en el filtro (auditoría) |

### Resultado

| Métrica | Script Python | SQL puro |
|---------|---------------|----------|
| analysis | 19 | 19 ✅ |
| terminos_raw | ~277 | 274 (`mira`, `pues` fuera) |
| stopwords | 594 | 596 |
| Tiempo | ? | ~1s |
| Dependencias | duckdb módulo Python | CLI solamente |

### Fixes incluidos en el SQL

- Prefijo `./` limpiado en `filename` y `video`
- `mira`, `pues`, `bueno`, `entonces`, `este` agregados a stopwords
- Índices en `term`, `video`, `nicho` para consultas rápidas

### Lección

> Cuando DuckDB es la herramienta, no hace falta Python.

`reconstruir.py` dependía de `duckdb.connect()` (módulo compilado). Replicar la lógica en SQL puro eliminó:

- la dependencia de Python en Termux
- los 3.8 GB de source
- el riesgo de versiones nightly incompatibles

El script SQL es más corto, más rápido y más portable que la versión Python.

> La CLI de DuckDB en Termux cubre el 95% de los casos de uso.
> Solo si necesitás extensiones custom (Postgres scanner, etc.) vale la pena compilar.

### Pendiente

- [ ] Evaluar si `brainhub/db/reconstruir.py` sigue siendo necesario
- [ ] Decidir si migrar otras queries de Python a SQL
- [ ] Considerar test de regresión del nicho industrial directo sobre la DB
      (bug #5 del 2026-09-15)

### Comandos

    # Reconstruir (con regeneración de stopwords)
    reconstruir_db.sh

    # Reconstruir rápido (sin regenerar stopwords.csv)
    REGEN_STOPWORDS=0 reconstruir_db.sh

    # Consultar
    duckdb /sdcard/Download/analisis_consolidado.duckdb


### 2026-09-15 (cont. 2) — Guardia de contaminación + pipeline completo

Tras reconstruir la DB, se armó el ecosistema de calidad:

#### Scripts nuevos (5)

- `scripts/crear_tablas_tecnicas.sh`: anatomia (3432), mesh_terms, cache_mesh
- `scripts/extraer_diccionarios.py`: diccionarios → CSV (clinico, nichos, tecnicos, nicho_keywords, vacios, stopwords)
- `scripts/actualizar_vista_tecnicos.sh`: vista unificada v_terminos_tecnicos
- `scripts/guardia_contaminacion.sh`: reporte de cobertura y términos sospechosos
- `scripts/pipeline_db.sh`: orquestador de los 5 pasos

#### Vista v_terminos_tecnicos

Unifica: anatomía (3432), MeSH (0, on-demand), clínico (156),
nichos (213), técnicos (134), nicho_keywords (260).

Total: ~3926 términos únicos.

#### Guardia de contaminación

Detecta términos que:
- Aparecen en ≥2 documentos
- NO están en v_terminos_tecnicos

Antes: 22 sospechosos
Después: 0 sospechosos

#### Términos sospechosos resueltos

Ruido (→ stopwords): may, basic, work, knowledge, students, impact,
acquisition, abilities, access, trends, sciences, information,
practice, stupid, skills, skill, sistemas, mundo, dia, igual,
venga, juan, sin

Técnicos (→ terminos_tecnicos.json): torch, loss, image, function,
train, training, neural network, classification, regression,
gradient, optimizer, tensor, model, layer, epoch, batch, dataset,
feature, inference, checkpoint, control

#### Cobertura final

- Freq ≥100: 100% técnicos (16/16)
- ≥2 docs: ~55%
- Global: 27.4% (incluye ruido de baja freq)

#### Pipeline

`pipeline_db.sh` corre en orden:
1. reconstruir_db.sh → análisis (4 tablas)
2. crear_tablas_tecnicas.sh → técnicas (3 tablas)
3. extraer_diccionarios.py → CSVs
4. actualizar_vista_tecnicos.sh → vista unificada
5. guardia_contaminacion.sh → reporte

#### Deuda técnica anotada

- Alias ES↔EN: `alias_mesh` y `mesh_cache.traduccion` no se exponen en la vista
- Lematización: `MAPA_ES` solo tiene 6 términos; NLTK es inglés-only
- `control` marcado como técnico (revisar si genera falsos positivos)
- MeSH (`mesh_terms`) vacío; se llena on-demand vía NCBI


### 2026-09-15 (cont. 2) — Guardia de contaminacion + pipeline completo

#### Scripts nuevos (5)

- scripts/pipeline_db.sh: orquestador de 5 pasos
- scripts/crear_tablas_tecnicas.sh: anatomia (3432), mesh_terms, cache_mesh
- scripts/extraer_diccionarios.py: diccionarios -> CSV
- scripts/actualizar_vista_tecnicos.sh: vista v_terminos_tecnicos
- scripts/guardia_contaminacion.sh: cobertura + sospechosos

#### Vista v_terminos_tecnicos

Unifica: anatomia (3432), MeSH (0 on-demand), clinico (156),
nichos (213), tecnicos (134), nicho_keywords (260).
Total: 3926 terminos unicos.

#### Guardia de contaminacion

Detecta terminos que aparecen en >=2 docs y NO estan en la vista.

| Momento | Sospechosos |
|---------|-------------|
| Antes   | 22          |
| Despues | 0           |

#### Terminos resueltos

Ruido (-> stopwords): may, basic, work, knowledge, students, impact,
acquisition, abilities, access, trends, sciences, information,
practice, stupid, skills, skill, sistemas, mundo, dia, igual,
venga, juan, sin

Tecnicos (-> terminos_tecnicos.json): torch, loss, image, function,
train, training, neural network, classification, regression,
gradient, optimizer, tensor, model, layer, epoch, batch, dataset,
feature, inference, checkpoint, control

#### Cobertura final

- Freq >=100: 100% tecnicos (16/16)
- >=2 docs: ~55%
- Global: 27.4% (incluye ruido de baja freq)

#### Modulos Python reparados (10)

Verificados end-to-end:
anatomia_parquet, mesh_parquet, mesh_cache, sugerente_anatomia,
pubmed_integracion, relaciones, paginacion, integrar_duckdb,
consolidar, exportar_sqlite

Todos importan sin error. anatomia_parquet devuelve resultados reales.

#### Deuda tecnica nueva

1. Alias ES<->EN no expuestos en v_terminos_tecnicos
   - diccionario_clinico tiene alias_mesh
   - mesh_cache tiene traduccion
2. Lematizacion marginal (MAPA_ES solo 6 terminos)
   - Evaluar spaCy-es
3. control marcado como tecnico (revisar si genera falsos positivos)
4. MeSH (mesh_terms) vacio, se llena on-demand via NCBI

#### Comando maestro

    pipeline_db.sh

Reconstruye todo en 5 pasos (~1 minuto).

---


### 2026-09-15 (noche) — Resumen LLM integrado en el pipeline

#### Logros

- brainhub/llm/ollama_client.py: generar() con keep_alive=0 y num_predict
- brainhub/llm/abstract_llm.py: generar_resumen_desde_analisis() con contexto compacto
- analisis_completo_v6.5.py: hook automatico antes de exportar_json()
- scripts/reconstruir_db.sh: columnas resumen_llm y resumen_modelo

#### Bugs resueltos

1. OllamaClient.generar() no pasaba num_predict -> modelo generaba
   hasta llenar contexto (2048) y entraba en loop con --context-shift
2. OllamaClient.generar() no pasaba keep_alive -> modelo quedaba 5 min
   en RAM y bloqueaba siguientes llamadas
3. Rama 'except' en abstract_llm devolvia None en vez de plantilla

#### Fix aplicado

generar() ahora incluye en el payload:
  keep_alive: 0     -> descarga modelo al terminar
  options.num_predict: 150  -> corta generacion

#### Modelos evaluados

| Modelo | Tiempo | Calidad | Veredicto |
|--------|--------|---------|-----------|
| tinyllama:latest | 50s | Alucina (inventa fechas, radios) | NO |
| gemma:2b | 32-74s | Coherente, sin alucinaciones | SI (default) |
| phi3:mini | - | No probado | reserva |
| llama3.2:3b | - | No probado (necesita >3.5 GB) | futuro |

#### Test end-to-end

1. analizar.sh Transcript_ME_lJOHAPUo_ES.txt
   -> Resumen: gemma:2b (32.8s)
   -> Texto: 'Este documento contiene informacion sobre un ataque...'
2. pipeline_db.sh -> DB reconstruida con resumen_llm
3. Consulta: 1 con resumen, 18 sin resumen (los otros no se re-analizaron)

#### Deuda tecnica nueva

1. Warning: exportar_sqlite_desde_json no maneja ON CONFLICT en DuckDB
   (no critico, pipeline_db.sh reconstruye desde JSON)
2. Re-analizar los 18 videos faltantes con LLM (~40-60 min)
3. gemma:2b tarda 32-74s por video; evaluar llama3.2:3b cuando haya RAM
4. Velocidad limitada por swap activo (1.0 GB)

---


### 2026-09-15 (noche) — SQL injection arreglado en api.py

#### Hallazgo

Al evaluar LiteLLM para las 11 APIs de BrainHub, se detecto
que /api/buscar era vulnerable a SQL injection:

  q = request.args.get('q', '')
  sql = f"... LIKE '%{q.lower()}%' ..."
  consultar(sql)  # q va directo al CLI duckdb

Payload de prueba: '; DROP TABLE terminos_raw;--

#### Vulnerabilidades encontradas (4)

1. api.py /api/buscar -> q
2. integrar_duckdb.py terminos_por_video() -> video_id
3. integrar_duckdb.py buscar_termino() -> termino
4. integrar_duckdb.py actualizar_estado() -> estado + video_id

#### Fix aplicado

Helper en integrar_duckdb.py:

  def _escape_sql_string(valor) -> str:
      return str(valor).replace("'", "''")

Estandar SQL: ' -> '' para escapar strings.
Aplicado en las 4 vulnerabilidades.

#### Test end-to-end

| Test | Resultado |
|------|-----------|
| /api/health | JSON OK |
| /api/buscar?q=planta | planta: 170 |
| injection | total: 0, tabla intacta |
| tabla terminos_raw | 234 filas |

#### Leccion

> Las consultas SQL construidas con f-strings siempre deben
> sanitizar el input. El helper _escape_sql_string debe usarse
> en cualquier funcion que reciba parametros externos.

#### Deuda tecnica nueva

1. /api/terminos usa int(limite) — seguro, pero por suerte
   Si se agregan mas filtros, usar _escape_sql_string
2. import RAGSimple sin usar en api.py
3. /api/grafo: import os agregado

---

