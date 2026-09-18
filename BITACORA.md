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


<!-- TAG: evaluacion_proyecto 2026-09-15 -->
### 2026-09-15 (cierre) — Evaluacion consolidada del proyecto

#### Contexto

Al cerrar la sesion mas larga hasta ahora (DuckDB + LLM + SQLi),
se hace una evaluacion del estado real del proyecto.

#### Veredicto por dimension

| Dimension | Antes | Despues |
|-----------|-------|---------|
| Arquitectura | 8/10 | 8.5/10 |
| Robustez de pruebas | 8/10 | 9/10 (+17 SQL) |
| Operabilidad | 8/10 | 9/10 (pipeline_db.sh) |
| Evaluacion cientifica | 5/10 | 5/10 (sin cambios) |
| Control de complejidad | 6/10 | 6/10 (sin cambios) |
| Potencial RAG/LLM | 8/10 | 9/10 (ya integrado) |
| Seguridad | no evaluada | 8/10 (SQLi cerrado) |

#### Fortalezas reales

1. Infraestructura solida: DB reproducible con 1 comando.
   Ya no depende de nightly de DuckDB, ni modulo Python duckdb,
   ni compilar NumPy en Termux.
2. Defensa en profundidad: tests unitarios + guardias + tests DB
   + fixtures + bitacora + SQL parametrizado.
3. Bitacora narrativa con lecciones: mecanismo de aprendizaje
   organizacional. Frases buscables que previenen repetir errores.
4. LLM opcional con guardias, NO dependencia central.

#### Debilidades reales (honestas)

1. Evaluacion cientifica 5/10: falta suite de evaluacion por
   nicho con documentos etiquetados. Sin eso, 'mejorar'
   CIBERSEGURIDAD puede empeorar FINANZAS sin detectarse.
2. Control de complejidad 6/10: ~30 modulos sin usar de 47,
   3 versiones de analisis_completo, deuda acumulada.
3. Scoring todavia necesita calibracion: min(matches, 5) es
   regla fija. Documentos largos tendran mas repeticiones.
4. Diccionarios manuales: ampliar CIBERSEGURIDAD a 34
   terminos puede sesgar hacia nichos con mas atencion.

#### Proximos pasos sugeridos (orden de ROI)

1. Suite de evaluacion por nicho (~2h)
   - 5 documentos etiquetados por nicho (25 total)
   - Precision/recall por nicho antes/despues de cada cambio
   - Es lo que la evaluacion senala como debil
2. Congelar v7.2.0 con changelog (~30 min)
   - Punto de referencia: DB reproducible + guardia + LLM + SQLi
3. Re-analizar 18 videos restantes con LLM (~1h background)
   - Hook listo, gemma:2b funciona, prompt esta
4. Fix warning de SQLite (~15 min)
   - No critico, pero ignorar warnings entrena a ignorar bugs
5. Grafos (deuda del 2026-09-10)
   - 8 bugs identificados, sin tocar
   - Validador federado ya funcional, siguiente pieza natural

#### Lo que NO hacer todavia

- Ollama como dependencia central (ya es capa opcional)
- FastAPI + JWT (overkill, mono-usuario)
- Denoise (overkill, sin casos reales)
- LiteLLM (confirmado no aplica, 0 APIs usan LLM)
- Integrar los ~30 modulos sin usar (mejor caso por caso)

#### Leccion

> El siguiente salto de calidad no es agregar features.
> Es medir con datos etiquetados.
> Sin eso, cualquier mejora de diccionario puede degradar
> otro nicho sin que nos enteremos.

#### Version sugerida

v7.2.0 - DB reproducible + LLM opcional + SQLi cerrado

---


#### Criterio de exito de la suite de evaluacion

La suite estara terminada cuando pueda detectar:

- Caida de 10% en precision de un nicho al ampliar otro diccionario
- Falsos positivos en documentos multi-tema (ej: ciberseguridad + finanzas)
- Cambios de clasificacion en 1 de cada 5 documentos luego de un fix

Sin este criterio, 'mejorar' un diccionario es fe ciega.

#### Snapshot numerico (2026-09-15 cierre)

- Tests Python: 116
- Tests regresion DB: 17 (todos pasando)
- Guardias: 8 (+ test_regresion_db)
- Nichos: 9 (incluye HABLA)
- Fuentes federadas: 5
- Modulos: 47 (~15 usados activamente)
- Documentos procesados: 19 videos
- Terminos unicos tecnicos: 3926
- Sospechosos (contaminacion): 0
- SQL injections cerradas: 4
- Modulos Python reparados: 10

---


### 2026-09-16 — Batch falló + cuarentena + limpieza

#### Contexto

Tras el batch nocturno del 2026-09-15, quedaron 55 videos sin
resumen LLM. Al investigar, aparecieron 8 bugs estructurales.

#### Bugs encontrados

1. Batch nocturno murió silenciosamente
   - Ollama murió durante el batch (probablemente RAM)
   - Sin auto-relanzar, los videos cayeron a None

2. analizar.sh NO es idempotente en nombres
   - Agrega _analisis_completo al nombre base
   - Si el input ya tenía _analisis, acumula: _analisis_analisis
   - Generó 42 archivos basura con 2-5 _analisis acumulados

3. _ollama_api duplicada en .bashrc
   - Línea 77: << PYEND (sin comillas, bash expande, bug latente)
   - Línea 134: << 'PYEND' (correcto)
   - Bash usa la última, pero la duplicación confunde

4. start_ollama con tmux es frágil
   - Si tmux muere, ollama serve muere
   - Causa probable de caída durante batches largos

5. Detector de binarios roto en batch_robusto.sh
   - grep -q $'\x00' no funciona como esperaba
   - Clasificó los 75 .txt como BINARIO y los movió a cuarentena
   - Fix: usar file -b en vez de grep

6. Filtro de basura tenía categorías demasiado amplias
   - find -name '*_resumen*.json' matchea JSONs válidos
   - 26 JSONs válidos movidos a quarantine
   - Fix: excluir *_analisis_completo.json

7. pipeline_db.sh es destructivo
   - Hace rm -f de la DB antes de reconstruir
   - Se pierden tablas técnicas (anatomia, mesh, etc)
   - Fix pendiente: opción --no-rm

8. Detector de nicho confunde tech/legal con CIBERSEGURIDAD
   - Transcript_DyhkXT_dgdk_ES_FORZADO (legal/violencia familiar)
   - Transcript_-lYFpNahqzY_EN (Microsoft Fabric/tech)
   - Fix pendiente: sesión dedicada

#### Fixes aplicados

- scripts/batch_robusto.sh (nuevo)
  - Reintentos automáticos (3 por video)
  - Logging detallado (intento, duración, causa)
  - Clasificación de errores (OOM, TIMEOUT, ENCODING, etc)
  - Auto-relanzar Ollama si muere
  - Cuarentena con metadata (.motivo.txt)

- scripts/filtro_basura.sh (nuevo)
  - 8 categorías de basura
  - Dry-run por defecto, --apply para ejecutar
  - Duplicados por hash MD5
  - Categoría motivos_sueltos (agregada hoy)

- Fix detector binarios: file -b en vez de grep x00
- Fix .bashrc: eliminada _ollama_api duplicada (sed 77,104d)
- start_ollama_nohup (versión sin tmux, más robusta)
- 43 archivos basura movidos a _legacy_
- 26 JSONs recuperados de cuarentena

#### Estado tras los fixes

- 75 .txt en /sdcard/Download/
- 30 JSONs válidos (con 6 resúmenes: 3 LLM + 3 plantilla)
- 73 videos pendientes de procesar
- DB reconstruida con 30 videos
- Detector de binarios funcionando

#### Lecciones

> Un batch nocturno que 'funciona' pero sin log es una bomba de tiempo.
> Un filtro de basura sin dry-run es un arma cargada.
> Un detector que clasifica el 100% como 'binario' no es un detector.
> Nada se borra: todo se mueve a legacy con motivo.

- Los errores en cadena son la norma, no la excepción
- Cuarentena + legacy salvaron el día (nada se perdió)
- Los heredocs con variables SIEMPRE con << 'EOF'
- Los logs con estructura (timestamps, categorías) son oro
- El silencio es el peor enemigo: sin output no hay debugging

#### Deuda técnica nueva

1. analizar.sh no es idempotente en nombres
2. pipeline_db.sh es destructivo (agregar --no-rm)
3. Detector de nicho (tech/legal mal como CIBERSEGURIDAD)
4. Cobertura 16.5% (refinar validador de términos)
5. Batch se corta en background (usar wake-lock + foreground)

#### Scripts nuevos versionados

- scripts/batch_robusto.sh
- scripts/filtro_basura.sh

---


### 2026-09-16 — Integraciones futuras (Jinja + PythonAnywhere + MCP)

#### Contexto

BrainHub expone 11 endpoints REST en api.py. Hoy corren solo
en Termux (localhost:5000) y ningun LLM los consume directamente.

#### 3 integraciones evaluadas

1. Jinja2 (templates)
   - dashboard.html actual es estatico (112 lineas vanilla JS)
   - Jinja permitiria base.html + bloques reutilizables
   - Cuando aplicar: dashboard > 5 paginas + auth
   - Hoy: overkill

2. PythonAnywhere (hosting)
   - api.py actual no es accesible desde fuera del celular
   - PythonAnywhere free tier: URL publica + HTTPS + 24/7
   - Limitaciones: CPU 100s/dia, 512 MB disco, se duerme
   - Arquitectura: api.py en PythonAnywhere, LLM en Termux
   - Alternativas: Render, Railway, Fly.io

3. MCP (Model Context Protocol)
   - Estandar de Anthropic para que LLMs consuman tools
   - Compatible: Claude Desktop, Cursor, Continue.dev
   - Exponer 6 endpoints utiles: health, search, nicho,
     videos, analizar, resumen
   - Implementacion: pip install mcp + mcp_server.py
   - Uso real: Dardo con 20 PDFs puede cruzar con BrainHub

#### Orden recomendado

1. MCP server local (1h) -- rapido, util ya
2. Jinja para dashboard (2h) -- solo si crece
3. PythonAnywhere (3h) -- solo si acceso externo

#### Leccion

> Exponer APIs sin cliente concreto es overkill.
> MCP convierte los endpoints en herramientas para LLMs
> y es el caso de uso mas claro hoy.

#### Estado

NO implementado. Documentado para cuando surja necesidad real.

---


## 2026-09-17 — RAG basico + 5 bugs + config centralizado

### Contexto

Sesion de continuacion despues del maraton del 15-16/09.
Foco: RAG sobre los 79 videos ya procesados + limpiar deuda
tecnica del pipeline.

### Logros

1. RAG basico funcionando (scripts/preguntar.py)
2. content_control recreada con schema correcto
3. Video KV cache (t4OnW22zXi4) procesado
4. 3 bugs del pipeline arreglados
5. Config centralizado (brainhub_config)

### Bug 1: RAG sobre resumenes LLM no funcionaba

SINTOMA:
- Query: 'que se dijo sobre plantas industriales'
- BM25 devolvia Como_dejar_el_1a1_ES (SALUD) score 3.8
- El video correcto (Transcript_ME_lJOHAPUo_ES) no aparecia

CAUSA:
- Solo se indexaba resumen_llm (texto abstracto: 'ataque a un
  sistema empresarial')
- Los terminos_clave reales (planta 170, industrial 155)
  no estaban en el indice

FIX:
- cargar_documentos() une analysis.resumen_llm con terminos_raw
  via JOIN + string_agg (term repetido 3x para pesar mas)
- Contexto al LLM con separador ||SEP||: 'Resumen: ... /
  Terminos clave: ...'
- Fix _tokenizar: normaliza plurales (plantas -> planta)

RESULTADO:
- BM25 ahora devuelve Transcript_ME_lJOHAPUo_ES score 16.36
- Recall@3 = 1.0, MRR = 1.0

### Bug 2: __pycache__ obsoleto

SINTOMA:
- preguntar.py tenia ||SEP|| en el codigo
- Pero el comando usaba la version vieja (sin separador)
- Terminos clave aparecian vacios

CAUSA:
- Python cachea bytecode en __pycache__/
- El .pyc era mas nuevo que el .py

FIX:
  rm -rf scripts/__pycache__

LECCION:
> Tras editar scripts, borrar __pycache__ antes de probar.
> O usar python3 -B script.py (no escribe .pyc).

### Bug 3: content_control se perdio al reconstruir la DB

SINTOMA:
- procesar URL tiraba 'Table with name content_control does not exist'
- El pipeline funcionaba igual pero con warning

CAUSA:
- ~/yt usa content_control para idempotencia
  (INSERT OR IGNORE + UPDATE status)
- La tabla existia en la DB v999 (perdida)
- No se recreo en pipeline_db.sh

FIX:
  CREATE TABLE content_control (
    content_id VARCHAR PRIMARY KEY,
    source_type VARCHAR,
    source_url VARCHAR,
    status VARCHAR DEFAULT 'pending',
    processed_at TIMESTAMP,
    error_message VARCHAR
  );

PENDIENTE:
- Agregar content_control a reconstruir_db.sh

### Bug 4: resumen LLM alucinaba 'traduccion de idiomas'

SINTOMA:
- Video KV cache (t4OnW22zXi4) resumido como 'traduccion de
  idiomas'
- Los terminos clave eran: palabra(29), pasa(25), hablando(22),
  vez(22), viene(14), vuelta(13), llama(13)

CAUSA (2 sub-problemas):
A. Muletillas orales no filtradas por HABLA
B. El prompt del resumen incluia metadata ruidosa:
   - Segmentos, Dialogos, Polaridad
   - Terminos con frecuencia 'cache(39)' interpretado como
     identificador literal

FIX A:
- HABLA: 119 -> 127 terminos
- Agregadas: pasa, hablando, viene, vuelta, llama, lomo,
  lomos, vuelto
- AnalizadorNichos ya devolvia HABLA en nichos_para_filtrar,
  solo faltaban los terminos

FIX B:
- Quitar Segmentos, Dialogos, Polaridad del contexto
- Terminos sin frecuencia: 'cache, modelo, prompt, tokens'
- Prompt con REGLAS explicitas

RESULTADO A:
- Terminos ahora: cache(39), modelo(15), prompt(13), tokens(12),
  memoria(10)

### Bug 5: warning consolidar_en_duckdb

SINTOMA:
- Cada analisis tiraba 'Binder Error: There are no UNIQUE/
  PRIMARY KEY constraints that refer to this table'

CAUSA:
- analisis_completo_v6.5.py:613 hacia INSERT OR IGNORE INTO
  progreso
- DuckDB 1.5.5 requiere PRIMARY KEY para INSERT OR IGNORE
- progreso (creada por reconstruir_db.sh) no tiene PK

FIX:
- Cambiar INSERT OR IGNORE por DELETE + INSERT
- Consistente con el DELETE que ya hace para terminos_raw
- Tambien: marcar consolidar_en_duckdb de exportar_sqlite.py
  como obsoleta (usaba import duckdb, no instalable en py3.14)

### Logro: config centralizado

Inspirado en ProjectConfig de Brain-Tumor-3D-Segmentation.

- brainhub_config.json: config unificada
  (paths, db, llm, rag, nichos)
- brainhub_config.py: loader con dot-notation
  - cfg.get('db.path')
  - cfg.reload()
- Sin dependencias (JSON built-in, no pyyaml)

PENDIENTE: migrar ollama_client, abstract_llm, preguntar,
rag_simple para usar cfg

### Aprendizaje: proyecto Brain-Tumor-3D-Segmentation

FUENTE: https://github.com/bielvicens/Brain-Tumor-3D-Segmentation

QUE TOMAR:
- Arquitectura modular por responsabilidades
- Config centralizada (aplicado)
- Sliding-window inference (= chunking)
- Streamlit para demo
- Checkpoints best/last para batches LLM

QUE NO TOMAR:
- 3D U-Net / PyTorch / CUDA (no aplica a NLP)
- Reportar validacion como resultado (peligroso)
- Sin baselines ni ablacion (no es peer-reviewed)

### Metricas de la sesion

- Bugs resueltos: 5
- Scripts nuevos: 1 (brainhub_config)
- Videos procesados: 1 (t4OnW22zXi4 KV cache)
- HABLA: 119 -> 127 terminos
- Commits: ~5

### Estado

- 79 videos en DB (73+ con resumen LLM)
- RAG basico funcionando (BM25 + Ollama)
- 5 bugs resueltos
- Config centralizado

### Deuda tecnica

1. Chunking (2-3h) para RAG de calidad
2. Ollama estable (diferido a sesion dedicada)
3. Migrar scripts a brainhub_config
4. Agregar content_control a reconstruir_db.sh
5. analizar.sh no es idempotente en nombres

### Lecciones

> Los resumenes LLM no son buenos indices para BM25.
> Los terminos_raw si. La mezcla funciona.
>
> __pycache__ puede hacer que un fix no se aplique.
> Tras editar, borrar el cache.
>
> El prompt del LLM no debe incluir metadata ruidosa
> (segmentos, dialogos, polaridad). Confunde al modelo.
>
> Las tablas de la DB no se recrean solas. Si una falta,
> agregarla a reconstruir_db.sh.

---


### Cierre 2026-09-17: plantilla + balance del día

#### Documento nuevo: PLANTILLA_CLASE_40MIN.md

Ubicacion: docs/PLANTILLA_CLASE_40MIN.md
Tamaño final: 152 lineas

Contenido:
- Cronometro de 40 min para preparar una clase
- 8 etapas (0-3, 3-5, 5-8, 8-20, 20-28, 28-33, 33-38, 38-40)
- Checklist reutilizable
- Tabla comparativa: sin BrainHub vs con BrainHub
- Ejemplo real: paper 'Is AI making us stupid?'
- Formula: Datos (BrainHub) + Interpretacion (vos) = Clase 40 min

Caso de uso: preparar un ateneo/clase a partir de un paper
en 40 min en vez de 2h 25min (ahorro: 1h 45min)

#### Commits del dia (11 total)

| Commit | Contenido |
|--------|-----------|
| 328df2c | Fix plantilla (152 lineas, sin duplicacion) |
| e76f174 | Primer fix fallido (rompio el documento) |
| 6c3f9e4 | Plantilla nueva (183 lineas, con duplicacion) |
| 316d8b5 | Prompt consolidado (176 lineas) |
| 6e7edbf | Bitacora completa (957 lineas) |
| 8f86c4f | Config JSON |
| 60aa681 | Config JSON (v1) |
| 84656ea | 3 mejoras pipeline (HABLA + warning + prompt) |
| 846963d | Warning consolidar + video KV cache |
| 381d8f3 | Limpieza derivados atlas |
| b0e3f38 | 72 videos con resumen LLM |

#### Balance del dia

Logros:
- RAG basico funcionando (preguntar.py)
- 5 bugs resueltos (RAG, pycache, content_control, muletillas, warning)
- Config centralizado (brainhub_config.json)
- Video KV cache procesado (t4OnW22zXi4)
- Prompt: 1695 -> 176 lineas (10x mas corto)
- Plantilla nueva: 152 lineas
- Aprendizaje del proyecto Brain-Tumor-3D

Descartado:
- Textstat (no resuelve bugs, agrega complejidad)

Diferido:
- Chunking (2-3h) -> proxima sesion
- Migrar a brainhub_config (1h) -> proxima sesion
- Ollama estable -> sesion dedicada
- Streamlit, MCP, Jinja, PythonAnywhere -> roadmap largo

#### Lecciones del dia

> __pycache__ puede hacer que un fix no se aplique.
> Tras editar scripts, borrar el cache.
>
> Los resumenes LLM no son buenos indices para BM25.
> Los terminos_raw si. La mezcla funciona.
>
> El prompt del LLM no debe incluir metadata ruidosa
> (segmentos, dialogos, polaridad). Confunde al modelo.
>
> Las tablas DB no se recrean solas.
> Agregar a reconstruir_db.sh.
>
> No agregar features que no resuelvan un bug.
> Regla VigiSalud aplicada a Textstat (descartado).

#### Deuda viva

Alta:
1. Chunking (2-3h) - RAG de calidad
2. Migrar a brainhub_config (1h)

Media:
3. Ollama estable (sesion dedicada)
4. content_control en reconstruir_db.sh (5 min)
5. analizar.sh idempotente (10 min)

Baja:
6. Refinar validador (cobertura 12%)
7. Mejorar prompt del LLM para resumen

---


## 2026-09-18 — Soporte PDFs + auto-detección de descolumnado

### Contexto

Se probó procesar un PDF (RESUMEN FARMACOLOGIA) y el flujo
falló en varios pasos. 4 bugs encontrados.

### Bug 1: procesar no detectaba PDFs

SINTOMA:
- procesar RESUMEN.pdf -> trataba como 'texto directo'
- Guardaba en /tmp/texto_directo.txt (no escribible en Termux)

FIX:
- Agregado elif *.pdf -> procesar_paper
- /tmp/texto_directo.txt -> ~/tmp/texto_directo.txt

### Bug 2: procesar_paper.sh no encontraba analizar

SINTOMA:
- 'analizar: command not found' dentro del script

CAUSA:
- analizar es un ALIAS de bash
  alias analizar='python3 ~/proyectos/nlp/analisis_completo_v6.5.py'
- Los alias NO funcionan dentro de scripts bash

FIX:
- Cambiar analizar por python3 + ruta absoluta

### Bug 3: KeyError en preguntas_debate.py

SINTOMA:
- KeyError: slice(None, 150, None) al generar documento 80/20

CAUSA:
- citas_clave[0] es un dict {'hablante': ..., 'texto': ...}
- El código asumía que era un string
- terminos_clave[0] es [term, freq]
- El código asumía que era un string

FIX:
- Detectar tipo y extraer el campo correcto
- Si es dict -> .get('texto')
- Si es list/tuple -> [0]

### Bug 4: descolumnado forzado en PDFs de 1 columna

SINTOMA:
- descolumnar.py fallaba con 'GUARDIA DE DESCOLUMNADO FALLÓ'
- 58.3% de líneas cortadas en el PDF de farmacología
- El texto quedaba roto en pedazos

CAUSA:
- descolumnar.py asume PDFs de 2 columnas (papers científicos)
- RESUMEN FARMACOLOGIA es de 1 columna
- Al intentar descolumnar texto de 1 columna, lo rompe

FIX:
- Auto-detección del resultado de descolumnar
- Si la guardia falla, revertir al texto sin descolumnar
- Sin flag manual (era un parche)

### Test end-to-end

PDF: RESUMEN FARMACOLOGIA (20447 chars, 83 segmentos)
Nicho detectado: SALUD
Términos clave: accion(20), farmacos(16), sustancias(14)
Co-ocurrencias: farmacos + farmaco (14)
Documento 80/20: 60 lineas generadas

### Comando nuevo

    procesar archivo.pdf      # PDFs ahora soportados

### Lecciones

> Los alias NO funcionan dentro de scripts bash.
> Usar rutas absolutas (python3 ~/ruta/script.py)
>
> Los datos pueden venir en distintos tipos:
> - citas_clave[0] puede ser str o dict
> - terminos_clave[0] puede ser str, list o tuple
> Validar isinstance() antes de operar.
>
> Las guardias deben tener escape hatch automático,
> no flag manual (que el usuario tiene que saber).
>
> /tmp no escribible en Termux. Usar ~/tmp.

---

