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


## 2026-09-18 — Fixes PDFs + deploy.sh idempotente

### Bugs resueltos (8)

#### procesar (4 bugs)
1. No detectaba PDFs -> elif *.pdf
2. analizar era alias -> python3 directo
3. KeyError en preguntas_debate.py -> isinstance()
4. Descolumnado forzado -> auto-deteccion

#### Infra (4 bugs)
5. deploy.sh no idempotente -> detecta cambios reales
6. .gitignore sin *.bak.* -> backups con timestamp se subian
7. .bak trackeados -> git rm --cached
8. Comentarios de prueba en BITACORA -> borrados

### Test end-to-end
- PDF: RESUMEN FARMACOLOGIA
- Nicho: SALUD
- Documento 80/20 generado (60 lineas)

### Comando nuevo
    procesar archivo.pdf

### Lecciones
> Los alias NO funcionan dentro de scripts bash
> Validar isinstance() para datos de tipo variable
> Las guardias deben tener auto-fallback, no flag manual
> deploy.sh debe detectar cambios con git status --porcelain
> *.bak no matchea archivo.bak.20260918_1322
> Usar *.bak.* tambien

---

## 2026-09-18 — Fix: content_control schema en DuckDB

### Síntoma
- procesar ~/yt fallaba con 'NOT NULL constraint failed: content_control.id'
- El INSERT no especificaba 'id', pero el schema lo exigía
- content_control tenía 'id INTEGER PRIMARY KEY' sin default

### Diagnóstico (largo)
1. Pensé que era el fix anterior que no se había aplicado
   - Falso: el script ya tenía CREATE OR REPLACE
2. Pensé que había que recrear la tabla en la DB viva
   - Falso: DESCRIBE mostró que ya estaba correcta
3. La causa real: DuckDB NO autogenera INTEGER PRIMARY KEY
   - A diferencia de SQLite, no hay ROWID implícito ni AUTOINCREMENT
   - Un INSERT sin 'id' explícito revienta con NOT NULL

### Causa real
El schema original era:
  id INTEGER PRIMARY KEY   -- sin DEFAULT, sin SEQUENCE

En SQLite eso funciona (autoincremento implícito).
En DuckDB no: el entero queda NULL y viola el NOT NULL.

### Fix
1. content_control usa 'content_id VARCHAR PRIMARY KEY'
   - content_id ya es único por diseño ('youtube:s6WTGMuFL8s')
   - No hace falta ID sintético
2. CREATE OR REPLACE TABLE (era CREATE TABLE IF NOT EXISTS)
   - IF NOT EXISTS no actualiza el schema de tablas existentes
   - OR REPLACE sí, y es idempotente al reconstruir
3. INSERT con ON CONFLICT (content_id) DO NOTHING
   - Reconstruir desde Transcript_*.txt no duplica

### Lección
> DuckDB ≠ SQLite en autoincremento.
> Si el dato ya tiene un identificador natural único,
> usá ese como PK. Más simple, KISS, y sobrevive a reconstrucciones.
>
> CREATE TABLE IF NOT EXISTS es una trampa para migraciones:
> no actualiza el schema si la tabla ya existe.
> Para scripts de reconstrucción, CREATE OR REPLACE.
>
> Cuando un replace() exacto 'no matchea',
> regex con re.DOTALL + re.IGNORECASE es más robusto.
>
> El test directo de inserción valió más que el test del pipeline.
> Aislar la operación atómica primero, después el flujo completo.

### Estado
- content_control: 23 filas, schema sin 'id'
- PK: content_id VARCHAR PRIMARY KEY
- DuckDB v1.5.5 (Variegata)
- ~/yt ya no falla al insertar
- Commit: e6cdf5f fix(reconstruir_db): content_control schema correcto

---


## 2026-09-18 — Fix: conceptos matcheaban por substring

### Síntoma
- Procesé video de congreso de salud (s6WTGMuFL8s)
- Reporte mostraba: 'LESION_DEPORTIVA: 1'
- El video NO habla de lesiones deportivas

### Diagnóstico
1. Busqué 'lesion', 'deportiv', 'sport', 'injury' en el transcript
   - Resultado: 0 matches
2. Pero el diccionario tiene 'anterior' y 'cruzado' como keywords de LESION_DEPORTIVA
3. Busqué 'anterior' en el transcript: 1 match
4. El matcher era substring: 'anterior' in texto
   - 'anterior' matchea dentro de 'anteriormente', 'año anterior', etc.
   - Falso positivo → contador +1 → LESION_DEPORTIVA aparece

### Causa real
En analisis_conceptos (v6.5 línea 329):
    if any(p in seg['texto'].lower() for p in patrones):

Substring matching. Cualquier keyword del diccionario que aparezca
dentro de otra palabra activa el concepto. 'anterior' es la peor:
aparece en cualquier texto en español, en cualquier contexto.

### Fix
Cambiar a word-boundary matching con regex:
    texto_lower = seg["texto"].lower()
    if any(re.search(rf"\b{re.escape(p)}\b", texto_lower) for p in patrones):

Aplicado en las 3 versiones activas:
- v6.3: línea 363
- v6.4: línea 361
- v6.5: línea 330

### Verificación
Reprocesé el mismo transcript:
- Antes: LESION_DEPORTIVA: 1
- Después: CONCEPTOS DOMINANTES vacío (correcto)
- Términos, co-ocurrencias, sentimiento: idénticos (no rompió nada)

### Lección
> Substring matching en NLP es trampa.
> 'anterior' matchea 'anteriormente'. 'test' matchea 'testing'.
> Usar word-boundary con re.search(rf'\b{re.escape(p)}\b', texto).
>
> Los diccionarios de keywords deben ser específicos.
> 'anterior' y 'cruzado' NO son keywords de LESION_DEPORTIVA
> sin contexto ('ligamento anterior', 'ligamento cruzado').
>
> Deuda técnica pendiente:
> - v6.5 líneas 262, 319, 742: otros substring matching sin bug confirmado
> - Diccionario: revisar keywords demasiado genéricas ('anterior', 'test', 'funcion')

### Estado
- Fix aplicado en v6.3, v6.4, v6.5
- Test con transcript real: OK
- No hay regresión en otros conceptos

---


## 2026-09-19 — Fix: analizar_github analizaba repos equivocados

### Sintoma
- Pedia analizar midudev/libros-programacion-gratis
- El analisis devolvia terminos de algebra lineal (vectors, matrix, linear)
- El output decia: 'Extraido en: ML-Math-Bridge-main'
- Estaba analizando un repo de ML (bajado semanas antes) en lugar del pedido

### Diagnostico
1. El ZIP correcto SI se bajaba (250 MB, nombre correcto)
2. Pero no se extraia: ya habia carpetas con nombres parecidos
3. El find con head -1 tomaba la PRIMERA carpeta *-main del directorio compartido
   - ML-Math-Bridge-main (Aug 4) va antes que libros-programacion-gratis-main
4. Todo caia en /sdcard/Download/github_analisis (compartido entre corridas)

### Causa real
El script usaba un OUTPUT_DIR compartido y reusaba archivos existentes.
Con el tiempo se acumularon multiples extracciones, y el find tomaba
la primera alfabeticamente, no la recien bajada.

Ademas, aunque se arreglara el cache, el analisis quedaba dominado por
archivos de build:
- pnpm-lock.yaml: 4055 lineas (35% del texto)
- web/pnpm-lock.yaml: 3944 lineas (34%)
- web/src/styles/global.css: 2915 lineas (80% del texto post-lock)

### Fix
1. Workdir con timestamp: ~/temp/github_analisis/run_YYYYMMDD_HHMMSS
   - Cada corrida tiene su propio directorio, sin colisiones
2. Symlink latest apunta al ultimo analisis
3. Rotacion automatica: mantiene ultimas 5 corridas
4. Fix del contador FILE_COUNT (era 0 por bug de subshell)
   - Cambiado pipe | while por process substitution < <(find ...)
5. Excluir lock files: pnpm-lock, package-lock, yarn.lock, Cargo.lock, etc.
6. Excluir extensiones de config/visual: .json .yaml .yml .toml .xml .html .css
   - Mantiene: .md .txt .rst .py .js .java .c .cpp .h .go .rs .sh

### Verificacion
Corrida sobre midudev/libros-programacion-gratis:
- Antes: 11665 lineas, 13 archivos, terminos de pnpm-lock.yaml
  (resolution: 850, integrity: 850, true: 452, linux: 442)
- Post lock files: 3662 lineas, 11 archivos, terminos de CSS
  (var: 310, color: 232, rgba: 204, border: 192)
- Post extensiones: 590 lineas, 4 archivos, terminos de contenido
  (pdf: 126, dev: 59, librosgratis: 58, books: 54, python: 19, javascript: 14)

### Leccion
> Substring matching en NLP es trampa. Word-boundary con re.search.
>
> Directorios compartidos entre corridas son trampa.
> Usar workdir con timestamp (YYYYMMDD_HHMMSS) + symlink latest.
>
> Filtrar archivos de build en analisis semanticos:
> - Lock files: pnpm-lock, package-lock, yarn.lock, Cargo.lock
> - Config/visual: .json .yaml .yml .toml .xml .html .css
> Dejar solo: docs + codigo fuente.
>
> Bug del contador en bash: pipe | while read crea subshell,
> las variables no se propagan al padre. Usar < <(find ...).

### Estado
- analizar_github.sh arreglado y verificado
- Commit: 20d833c
- Workdir temporal en ~/temp/github_analisis/
- /sdcard/Download/github_analisis/ ya no es destino (limpiado)

---


## 2026-09-20 — Feature: flag --docs-only en analizar_github

### Contexto
El fix de ayer (filtros de contenido) resolvio el caso de repos de
contenido puro, pero seguia contaminado con repos de codigo. Cuando
se analizo Arkay92/OracleCortex, los terminos dominantes fueron
sintaxis Python: self (560), def (134), import (122), int (132).

### Sintoma
- Repo de codigo puro (30 archivos .py, 4114 lineas)
- Analisis dominado por keywords del lenguaje, no por el proyecto
- Inutil para entender que hace el repo

### Diagnostico
El script procesa docs + codigo por default. Para repos de contenido
eso funciona (el codigo es minoritario), pero para repos de codigo
puro, el codigo domina y sepulta la documentacion.

Es el mismo patron que lock files (pnpm-lock) y CSS (global.css).
Una categoria de archivo domina el analisis semantico.

### Fix
Flag opt-in --docs-only que restringe el analisis a .md, .txt, .rst.

Uso:
  analizar_github.sh usuario/repo main              (default: codigo + docs)
  analizar_github.sh usuario/repo main --docs-only  (solo documentacion)

### Verificacion
Corrida sobre Arkay92/OracleCortex:
- Default: 30 archivos, terminos top: self, def, import, int
- --docs-only: 6 archivos, terminos top: memory (20), hdc (20),
  sleep (18), concepts (15), symbolic (14), emergent (14), oracle (14)

Corrida sobre midudev/libros-programacion-gratis (sin regresion):
- Default: 4 archivos, terminos top: pdf, dev, librosgratis, books
- (identico a la corrida anterior al flag)

### Leccion
> Analisis semantico en repos de codigo vs repos de contenido
> requieren filtros distintos. No hay un default que sirva para todo.
>
> El patron que se repite: una categoria de archivo domina el analisis
> - Repos de contenido + lock files -> pnpm-lock.yaml domina
> - Repos de contenido + web    -> global.css domina
> - Repos de codigo             -> sintaxis del lenguaje domina
>
> Solucion: filtros en capas. Default + flags para casos especificos.

### Estado
- Flag --docs-only en analizar_github.sh
- Commit: feat(analizar_github): flag --docs-only para repos de codigo
- Sin regresion en repos de contenido

---


## 2026-09-21 — Alineaciones con 'Scripting avanzado con Python'

### Contexto
Lei 'Scripting avanzado con Python' (Alejandro G Vera, 2026).
El libro esta pensado para Kali Linux y seguridad ofensiva, pero varios
capitulos contienen patrones arquitectonicos aplicables a BrainHub.

### Que NO aplica
- Cap 5: Scapy, captura/generacion de paquetes
- Cap 6: Nmap, reconocimiento activo
- Cap 7: Playwright, auditoria web ofensiva
- Cap 12: framework de pentesting

### Que SI aplica (5 patrones a incorporar)

**1. argparse con subcomandos (Cap 1)**
- Unificar 30+ scripts sueltos en `brainhub <comando>`
- Hoy: procesar.sh, analizar.sh, preguntar.py, pipeline_db.sh, etc.
- Despues: brainhub procesar, brainhub analizar, brainhub preguntar

**2. Config con precedencia (Cap 1.3)**
- Patron: default -> archivo -> env vars -> CLI
- Aplicar a los 4 archivos pendientes de migrar a brainhub_config:
  ollama_client, abstract_llm, preguntar, rag_simple
- deep_merge recursivo, build_settings, command_line_overrides

**3. retry_async con backoff + jitter (Cap 3)**
- Para Ollama (muere cada 10-30 min)
- Reintentos con espera exponencial + variacion aleatoria
- Solo para errores transitorios (TimeoutError, ConnectionError)

**4. Migraciones versionadas no destructivas (Cap 9)**
- Hoy: reconstruir_db.sh usa CREATE OR REPLACE (destructivo)
- Patron: MIGRATIONS dict + PRAGMA user_version + backup previo
- Preserva datos entre versiones del esquema

**5. Logging estructurado en JSONL (Cap 1.4)**
- Hoy: stdout
- Patron: JsonFormatter + RotatingFileHandler
- Cada evento con run_id y profile

### Leccion
> Copiar el COMO (arquitectura, patrones), no el QUE (comandos de seguridad).
> El libro brilla en Cap 1, 3, 8, 9, 11. El resto es de otro dominio.

### Estado
- Documentado como hoja de ruta
- Sin aplicar todavia (BrainHub core sigue prioritario)
- Referencia: 'Scripting avanzado con Python', Alejandro G Vera, 2026

---


## 2026-09-21 — Leccion: codigo generado en AI Studio

### Contexto
Genere 'BrainHub Studio' con Google AI Studio (Gemini). Un dashboard
React/TypeScript con 6 modulos (Dashboard, PostCrafter, BuzzwordCleaner,
AudienceRadar, EngagementSimulator, BridgePanel).

En el canvas de AI Studio compilaba limpio. 'Verificado', decia.
Lo baje como ZIP a Termux. Y ahi empezo el trabajo real.

### Que se rompe al exportar de AI Studio

**1. Versiones de dependencias inventadas**
- package.json declaraba Vite 8, TypeScript 7, @vitejs/plugin-react 6
- Ninguna de esas versiones existe en npm publico
- AI Studio usa versiones internas en su sandbox

**2. Modelo inexistente fuera del sandbox**
- El codigo usaba 'gemini-3.8-flash'
- Ese modelo no existe en la API publica de Google
- Es un alias interno de AI Studio

**3. Codigo muerto**
- src/server/geminiService.ts: nadie lo importaba
- express y dotenv en dependencies: sin uso
- User-Agent 'aistudio-build': especifico del sandbox

**4. Nombre por defecto del template**
- package.json decia 'react-example'

### Que aprendimos
> El codigo generado por IA funciona en el sandbox de la IA.
> En la maquina real, el trabajo es la traduccion.
>
> Antes de publicar cualquier proyecto generado por IA, auditar:
> 1. Versiones de dependencias contra npm publico
> 2. Modelos contra la documentacion oficial
> 3. Codigo muerto (archivos sin import, deps sin uso)
> 4. Nombres por defecto del template
> 5. Secretos hardcodeados
>
> 80% del scaffolding es rapido y funcional.
> 20% del trabajo real es portabilidad, paths, permisos y limpieza.

### Comparacion con BrainHub
BrainHub (codigo propio) tuvo bugs equivalentes en la traduccion:
- Hardcodeos que no corrian en Windows
- Paths absolutos de Termux
- Permisos de scripts que dependian de como se crearon

La diferencia: en BrainHub yo escribi el codigo y podia rastrear
la causa. En Studio, Gemini genero codigo que no entiendo del todo
y tuve que auditar para entender que habia adentro.

### Decision
- NO publicar BrainHub Studio en GitHub
- NO mencionarlo como producto en LinkedIn
- SI usarlo como herramienta personal (si se arreglan 4 cosas)
- SI publicar la leccion en LinkedIn (post 'sandbox != produccion')

### Estado
- ZIP descargado, auditado, no publicado
- Post publicado en LinkedIn el 2026-09-21
- Correcciones pendientes (si se retoma como herramienta):
  1. package.json: nombre + versiones reales
  2. Eliminar src/server/ (codigo muerto)
  3. Sacar express, dotenv, esbuild, @google/genai
  4. Reemplazar Gemini por Ollama si se quiere 100% local

---


## 2026-09-25 — Concepto: Deuda de perímetro

### Origen
Lei un post de un DevOps Manager (Clarivate) sobre por que el 50% de
los proyectos GenAI mueren despues del PoC (Gartner predijo 30%, la
realidad fue 50%). Su diagnostico: no es la tecnologia, es DONDE se
construyen los proyectos.

Su frase: "deuda de perimetro: el trabajo que aplazas cuando construis
el PoC fuera de los controles dentro de los que tendra que vivir".

### Aplicado a BrainHub
Es el mismo fenomeno, en otro dominio. BrainHub es local-first por
diseno, pero el perimetro real (defaults seguros, salidas escritas,
controles de red) no estaba definido.

Ejemplos concretos:
- Ollama sin auth: si arranca y la red cambia, queda expuesto
- 18 defaults Python apuntan a DB corrupta (funciona solo si
  BRAINHUB_DB esta seteada en el shell)
- 2 DBs 'version 999' que ya no se pueden leer
- 115 JSONs huerfanos sin consolidar

### Recategorizacion de pendientes

**Deuda de perimetro** (seguridad + portabilidad):
- 18 defaults Python apuntan a DB corrupta
- Ollama sin regla de host explicita

**Deuda de datos** (funcionalidad):
- 115 JSONs huerfanos en /sdcard/Download/

**Deuda de higiene** (limpieza, no bloquea):
- 2 DBs corruptas en data/ (renombradas)

### Regla nueva
> Local-first no es solo "no hay cloud". Es "hay controles, hay
> defaults seguros, hay salidas escritas".
>
> Antes de agregar un default o exponer un servicio, escribir:
> - A donde apunta por defecto
> - Quien puede acceder
> - Como se saca

### Practica inspirada (post original)
El autor propone para empresas reguladas:
1. Escribir el perimetro antes que el prompt
2. POC dentro del perimetro desde dia 1
3. 3 semanas, criterios de exito en papel
4. Medir donde corre el flujo
5. Escribir la salida en el arranque

Aplicable a BrainHub en escala: cada nuevo modulo, cada nuevo
default, cada nuevo servicio expuesto debe tener perimetro definido
antes de la primera linea de codigo.

---


## 2026-09-26 — Curso LangGraph + fixes de arquitectura

### Contexto
Bajamos el curso 'Building Production AI Agents with LangGraph'
(20 videos, YouTube) y procesamos 16. El objetivo era aprender
sobre agentes IA y validar el pipeline con contenido nuevo.

### Que funciono
- youtube_transcript_api (fallback cuando yt-dlp falla con 429)
- Fallback de idiomas: es -> es-US -> en
- analizar 16 videos en loop, batches, todo OK
- Pipeline completo: 99 analysis, 1782 terminos_raw

### Que fallo (y como se resolvio)

**1. yt-dlp bloqueado con HTTP 429**
- Solucion: youtube_transcript_api (via distinta a YouTube)
- Delays de 5-15s entre videos

**2. Idioma es no disponible**
- Solucion: es-US (traduccion automatica de YouTube)
- Fallback en orden: es, es-US, es-419, en

**3. DuckDB con lock persistente (proceso stopped)**
- Causa: Ctrl+Z dejo el proceso en estado T con el lock abierto
- Solucion: kill -CONT PID + kill -9 PID
- Los procesos stopped no responden a SIGKILL directamente

**4. /tmp no escribible en Termux**
- Solucion: usar ~/tmp o ~/playlist_brainhub

**5. analizar escribe en terminos_raw pero no en analysis**
- analysis se llena solo con reconstruir_db.sh
- Los JSONs deben estar en /sdcard/Download/ para que se vean
- Solucion manual: copiar JSONs + correr reconstruir_db.sh

**6. reconstruir_db.sh es destructivo**
- Solo toca 5 tablas (analysis, terminos_raw, progreso,
  stopwords, content_control)
- Pierde anatomia, mesh_terms, cache_mesh, v_terminos_tecnicos
- Solucion: correr pipeline_db.sh completo

**7. analysis.filename no guarda path**
- Analizar el mismo archivo desde 2 directorios duplica filas
- Solucion manual: DELETE del duplicado

### Numeros finales
- analysis: 99 (era 81, +18)
- terminos_raw: 1782 (era 1439, +343)
- content_control: 25
- TECNOLOGIA: 61 (era 44, +17)

### Corpus nuevo
16 videos del curso LangGraph:
- 00. Overview
- 01. Environment Setup
- 02. Why Graphs Not Chains
- 03. State Nodes Edges
- 04. Control Flow
- 05. Tools And React
- 06. Checkpointers And Threads
- 07. Durable Execution
- 08. Human In The Loop
- 09. Time Travel
- 10. Memory
- 11. Subgraphs
- 12. Supervisor Teams
- 13. Swarm And Handoff
- 14. Plan Execute Reflection
- 15. Streaming

Pendientes (rate limit): 16, 17, 18, 19

### Deudas documentadas
1. reconstruir_db.sh destructivo (no toca tablas tecnicas)
2. analizar + reconstruir_db desacoplados
3. analysis.filename no guarda path
4. v_terminos_tecnicos discrepa entre output y query
5. 4 videos del curso pendientes (rate limit)
6. Diccionario sin AGENTES_IA/LANGGRAPH (conceptos caen a DATA_SCIENCE)

### Lecciones para el futuro

> yt-dlp bloquea con 429. youtube_transcript_api es el fallback.
> Termux: /tmp no escribible, usar ~/tmp
> DuckDB: Ctrl+Z deja lock persistente. Usar .quit
> Procesos stopped no responden a SIGKILL. Primero SIGCONT.
> Verificar que el archivo bajado NO sea un mensaje de error
> pipeline_db.sh es el flujo canonico, no reconstruir_db.sh solo
> analizar escribe terminos_raw; reconstruir_db llena analysis

### Estado
- Commit del dia: feat: curso LangGraph + fixes de arquitectura
- BITACORA actualizada 2026-09-26
- Todo pusheado a GitHub

---


## 2026-09-26 — Patrón: caché persistente + ventana incremental

### Origen
Aporte de contacto DevOps: en diseño de sistemas basados en
prácticas DevOps (y en general), los algoritmos más efectivos para
un caso de uso especial CASI NUNCA están en las buenas prácticas.

Motivo: las buenas prácticas plantean lo ideal a buscar CAMBIANDO
el contexto y el marco técnico. No tienen solución cuando no podés
cambiar casi nada, solo agregar mejoras incrementales sobre lo que
va a seguir funcionando mal.

### Caso clásico: latencias heredadas
Los microservicios modernos trasladan la demora del legacy al
usuario si el origen no puede cambiarse.

**Estrategia**: caché local persistente + ventana incremental.

1. Primera consulta: traer histórico completo, guardar en caché
   local consultable (SQLite, DuckDB)
2. Consultas siguientes: devolver histórico desde caché + pedir
   al origen solo la ventana reciente (ej: 30 registros en lugar
   de 17.000)
3. Interfaz: separar 'Actividad reciente' (fresh) de 'histórico'
   (posiblemente stale)
4. Ciclo de vida: descartar contextos que dejan de reutilizarse
   (ej: 30-40 min sin uso), definido por observabilidad

**Resultado típico**: trabajo reducido 2-3 órdenes de magnitud.

### Los 3 conceptos clave

**1. Casi nunca el algoritmo ideal está en las buenas prácticas**
Porque asumen que podés cambiar el contexto. Cuando no podés, la
solución es mitigar, no aplicar la práctica.

**2. Recientes vs histórico**
Separación simple y poderosa:
- Reciente -> siempre fresh, pedilo al origen
- Histórico -> cacheado, marcado como 'posiblemente stale'

**3. Ciclo de vida por observabilidad**
La caché no es infinita. Se descarta cuando deja de usarse.
Eso se detecta con métricas de uso.

### Aplicable a BrainHub (3 casos)

**Caso 1: Re-análisis incremental**
Hoy: pipeline_db.sh procesa todos los JSONs cada vez.
Propuesta: flag --incremental que solo procese nuevos.
Ahorro: saltar ~80% del trabajo si solo hay 5-10 nuevos.

**Caso 2: RAG con caché de temas**
Hoy: preguntar.py corre BM25 sobre todo el corpus cada vez.
Propuesta: cachear resultados de temas repetidos.
Ahorro: queries repetidas son instantáneas.

**Caso 3: Transcripciones cacheadas**
Hoy: content_control ya hace esto parcialmente.
Propuesta: hacerlo explícito con tabla cache_transcripts.
Ahorro: no re-bajar videos ya procesados.

### Aplicado a aprendizaje del curso LangGraph
El mismo patrón se aplica a cómo usar el análisis como índice:
- Primera vez que buscás 'checkpointer' -> búsqueda completa
- Segunda vez -> ya está cacheado -> instantáneo

### Relación con 'deuda de perímetro'
El patrón es deuda de perímetro en otra forma:
- Buena práctica = 'hacé X bien desde el principio'
- Realidad = 'no podés cambiar X, mitigá'

BrainHub es local-first con restricciones (Termux, 4 GB RAM, sin GPU).
Eso significa que el patrón de mitigación aplica más que el de
'hacé las cosas bien'.

### Prioridad
Media. Ideas para futuro, no bugs concretos.

---


## 2026-09-26 — Script mapa_corpus.py + fix CAIS

### mapa_corpus.py (nuevo)
Script que genera un mapa navegable del corpus desde DuckDB.

**4 modos**:
- `--tabla` — indice de documentos
- `--termino X` — documentos que mencionan X
- `--nicho Y` — documentos de un nicho
- `--stats` — metricas agregadas

**Opciones**: --json, --output archivo, --limit N
**Config**: variable BRAINHUB_DB
**Dependencias**: ninguna (stdlib)

Lee directo de la DB, no re-parsea JSONs.
Util para: ver corpus, buscar terminos, entender distribucion,
detectar contenido duplicado.

### Fix: clasificacion CAIS
Los 5 archivos CAIS_2026 (Congreso Argentino de Informatica en Salud)
estaban clasificados como TECNOLOGIA. Reclasificados como SALUD.

**Fix**:
    UPDATE analysis SET nicho='SALUD' WHERE filename LIKE 'CAIS%';

**Resultado**: SALUD 9 -> 14, TECNOLOGIA 61 -> 56

### Hallazgo: CAIS no es duplicado
Pensamos que CAIS_2026_Completo duplicaba los diarios.
Al verificar:
- Completo: 3977 segmentos, 16 terminos_raw
- Diarios: 3273 segmentos, 52 terminos_raw

Son dos granularidades del mismo evento. Cada uno aporta terminos
distintos. No hay duplicacion real.

**Decision**: mantener los 5 archivos.

### Leccion
> Antes de eliminar 'duplicados', verificar si son realmente
> duplicados o representaciones distintas del mismo contenido.
>
> Los reportes agregados (stats, mapa) ayudan a detectar
> patrones que no se ven a nivel individual.

### Estado
- mapa_corpus.py en scripts/
- CAIS reclasificado como SALUD
- Commit: feat: mapa_corpus.py + fix clasificacion CAIS
- Todo pusheado a GitHub

---


## 2026-09-26 — Auditoria de dependencias Python

### Contexto
Detectamos 123 paquetes instalados globalmente en Termux.
Algunos parecían "sin uso" pero podían ser usados por otros proyectos.

### Hallazgos
- 12 paquetes con 0 uso real en TODOS los proyectos
- 5 paquetes usados por otros proyectos (sistema-alquiler)
- Resto son legítimos de BrainHub o dependencias transitivas

### Paquetes usados por otros proyectos (NO SACAR)
- fastapi, uvicorn, starlette (vigisalud, sistema-alquiler)
- cryptography, passlib, bcrypt (auth)
- shodan (shodan_termux_env)
- python-jose (sistema-alquiler)

### Paquetes huérfanos (12)
azure-*, msal, pycryptodomex, pydub, mutagen, audioop-lts,
googletrans, deep-translator, markitdown

### Decision
NO desinstalar. Motivos:
- Ahorro ~150 MB de 110 GB libres
- Riesgo de romper otros proyectos por dependencias cruzadas
- Regla KISS: si funciona, no lo toques

### Leccion
> En Termux, todos los proyectos comparten Python global.
> No hay aislamiento de dependencias.
> Una "limpieza" local puede romper proyectos remotos.

### Fix a futuro
- venv por proyecto
- pipx para apps
- Auditoria anual

Backup: ~/proyectos/nlp/requirements-before-audit.txt

---

## 2026-09-26 — Mejora batch_ollama_robusto

### Contexto
El script ya tenia chequeo de RAM + reinicio Ollama. Faltaba:
- Pausa preventiva (solo pausaba reactivamente)
- Medicion de tiempo

### Cambios aplicados
1. Pausa 5s entre videos (era 2s)
2. Pausa 30s cada 5 videos (preventiva)
3. Medicion de tiempo por video
4. Resumen con tiempo total + promedio

### Beneficio
- Mas estabilidad en batches largos
- Visibilidad del tiempo real

---

## 2026-09-27 — Feature: yt_transcript.py (MVP)

### Contexto
Necesidad de separar texto limpio (para analisis) de timestamps
(para navegar al video). Los timestamps embebidos contaminaban el
analisis NLP. Los timestamps separados requieren validacion porque
las pistas traducidas tienen offsets (video de prueba: ~90s).

### Que se implemento
3 modulos + 1 CLI:
- yt_lib/io.py: estructura de archivos + state + metadata
- yt_lib/fetch.py: descarga con fallback (API -> yt-dlp)
- yt_lib/validate.py: validacion en 5 puntos
- yt_transcript.py: CLI con 4 subcomandos

### Decisiones de diseno
- Estructura por video, no por idioma
- Roles explicitos: source, translated, etc.
- Metadata con use_for_navigation + use_for_analysis
- Idempotencia: si existe, no re-descarga
- State resumible: .state.json con pasos
- Escritura atomica: .tmp + replace

### Lecciones
> El idioma de navegacion NO siempre es el idioma del audio.
> La pista en_source puede no ser la original.
> Hay que validar sincronizacion en 5 puntos.
> El "modo auto" da pending_validation, no validated.

### Validado con HNClGfpmSfk
- en_source: 208 segs, sync validado (offset 0.0s en 5 puntos)
- es-US_translated: 220 segs (traduccion con offsets)

### Pendiente
- Migrar ~/yt al nuevo flujo
- DuckDB con tablas de transcripts
- Reportes con links temporales
- Alineacion semantica entre idiomas

---

## 2026-09-27 — Feature: yt_transcript.py (MVP)

### Contexto
Necesidad de separar texto limpio (para analisis) de timestamps
(para navegar al video). Los timestamps embebidos contaminaban el
analisis NLP. Los timestamps separados requieren validacion porque
las pistas traducidas tienen offsets (video de prueba: ~90s).

### Que se implemento
3 modulos + 1 CLI:
- yt_lib/io.py: estructura de archivos + state + metadata
- yt_lib/fetch.py: descarga con fallback (API -> yt-dlp)
- yt_lib/validate.py: validacion en 5 puntos
- yt_transcript.py: CLI con 4 subcomandos

### Decisiones de diseno
- Estructura por video, no por idioma
- Roles explicitos: source, translated, etc.
- Metadata con use_for_navigation + use_for_analysis
- Idempotencia: si existe, no re-descarga
- State resumible: .state.json con pasos
- Escritura atomica: .tmp + replace

### Lecciones
> El idioma de navegacion NO siempre es el idioma del audio.
> La pista en_source puede no ser la original.
> Hay que validar sincronizacion en 5 puntos.
> El "modo auto" da pending_validation, no validated.

### Validado con HNClGfpmSfk
- en_source: 208 segs, sync validado (offset 0.0s en 5 puntos)
- es-US_translated: 220 segs (traduccion con offsets)

### Pendiente
- Migrar ~/yt al nuevo flujo
- DuckDB con tablas de transcripts
- Reportes con links temporales
- Alineacion semantica entre idiomas

---

## 2026-09-28 — Subcomando link en yt_transcript.py

### Contexto
El MVP de yt_transcript.py tenia 4 subcomandos. Faltaba generar
links navegables al video.

### Que se agrego
1. Modulo yt_lib/links.py con 5 funciones
2. Subcomando link en el CLI
3. 5 tests de extract_video_id (5 formatos de URL)
4. 3 tests de build_timestamped_url

### Decisiones
- extract_video_id soporta: youtube.com/watch?v=, youtu.be/,
  embed/, /v/, /shorts/
- build_timestamped_url devuelve formato corto o completo
- parse_timestamp acepta MM:SS y HH:MM:SS

### Resultado
Ciclo completo: inspect -> fetch -> validate -> link

Ejemplo:
    yt_transcript.py link HNClGfpmSfk --at 3:45
    # https://youtu.be/HNClGfpmSfk?t=225

---

## 2026-09-28 — Fix: 20 defaults Python apuntan a DB correcta

### Contexto
El análisis del día detectó que 20 archivos Python tenían
como default 'data/analisis_consolidado.duckdb' (path relativo)
que apunta a la DB corrupta (version 999).

Cuando BRAINHUB_DB estaba seteada en el shell, funcionaba.
Cuando no, caía al default roto. Eso pasaba en:
- Cron jobs
- Terminales nuevas
- Scripts que limpian env
- Tests aislados

### Diagnóstico
1. grep inicial encontró 18 archivos con el patrón
2. Pero el config.py usaba composición de Path:
     str(BASE_DIR / 'data' / 'analisis_consolidado.duckdb')
   en lugar del string literal, por eso el grep no lo vio
3. Los tests tampoco entraron en el grep inicial (buscaba
   solo *.py y modulos/*.py, no tests/)
4. Total real: 20 archivos (17 + config.py + 2 tests)

### Fix
- 17 archivos con el string literal: sed masivo
- config.py: fix específico (Path composition)
- 2 tests: sed masivo

Nuevo default en los 20:
    '/sdcard/Download/analisis_consolidado.duckdb'

### Verificación
- grep: 0 restantes con 'data/analisis_consolidado'
- py_compile: los 20 OK
- Test end-to-end sin BRAINHUB_DB:
    DB_PATH: /sdcard/Download/analisis_consolidado.duckdb
- verify_claims.sh: 5/5 OK

### Lección
> Cuando buscás un patrón en el código, no asumas que todos
> los archivos usan la misma forma.
>
> Mismo path, distintas construcciones:
> - String literal: 'data/analisis_consolidado.duckdb'
> - Path composition: str(BASE_DIR / 'data' / '...')
> - f-string: f'{BASE_DIR}/data/...'
>
> Un grep de una sola forma puede perder archivos.
> Buscar variantes (BASE_DIR, os.path.join, Path /).

### Estado
- 20 archivos con default '/sdcard/Download/...'
- config.py (crítico) arreglado
- Tests arreglados
- claims.json actualizado (terminos-raw: 1842)

---


### Referencias
- Commit fix: 78795e0
- Commit docs: d58f7a4
- Delta claims: terminos-raw 1782 -> 1842 (+60, análisis del día)

## 2026-09-28 — Fix colateral: grep cruzado encontró bug en CI

### Contexto
Tras cerrar el fix de los 20 defaults, se corrió un grep ampliado
(no solo *.py) para verificar que no quedaran referencias al path
viejo en docs, Makefile, .env*, etc.

El grep encontró 1 bug real que el grep original no vio.

### Hallazgo
.github/workflows/tests.yml seteaba:
    BRAINHUB_DB: data/analisis_consolidado.duckdb   (relativo)

Ese path no existe en el runner de GitHub Actions. Resultado:
10/10 tests de DuckDB skipeaban silenciosamente vía
`pytest.skip('DuckDB no disponible en CI')`. CI decía "verde"
sin testear nada de la DB.

Además, el workflow instala el CLI de DuckDB en un step previo,
o sea que la intención original era testear DuckDB de verdad.
El path relativo rompió esa intención sin que nadie lo notara.

### Fix
- tests/fixtures/fixture.sql: schema + datos mínimos
  (tablas terminos_raw y progreso, con datos que satisfacen
  todos los asserts de test_duckdb.py)
- tests.yml: genera mini.duckdb antes de los tests,
  BRAINHUB_DB apunta al fixture
- .gitignore: excluye mini.duckdb (se regenera en CI)
- Se mantiene solo CLI de DuckDB, sin agregar módulo Python
  a requirements.txt (el CLI ya se instala antes)

### Falsos positivos del grep
- 2 archivos .bak.pre_default_fix en tests/ → NO estaban
  commiteados, eran basura local del sed -i. Borrados.
- 5 hits en BITACORA.md y prompt_retoma.md → documentación
  intencional (citas del bug, ejemplos de la Lección).

### Verificado
- Simulación de CI local: rm mini.duckdb → regenerar desde .sql
  → 10/10 PASSED (antes: 10/10 SKIPPED)
- YAML válido
- mini.duckdb NO aparece en git status (ignorado)

### Lección
> El grep cruzado NO es ceremonia. Encontró un bug real en un
> archivo que el grep original no miraba (.yml de CI).
>
> Incluir en el grep ampliado:
> - docs/, README, Makefile, .env*, docker-compose.yml
> - .github/workflows/*.yml
> - residuales de refactors: *.bak.*, *.orig, *.pre_*
>
> Un grep que solo cubre código deja afuera CI, docs y config.

### Referencias
- Commit fix CI: f758cb8
- Commit docs: (este mismo, pendiente)
- Bug encontrado por: grep cruzado post-fix defaults

---

## 2026-09-29 — Truncamientos silenciosos en pipeline RAG

### Contexto
Aplicando el material de "Debugging a Broken RAG System" al pipeline
de BrainHub, se auditó el flujo real:
  query → RAGSimple.buscar() → preguntar.py → prompt → LLM

Durante la auditoría aparecieron 3 truncamientos con [:N] que
cortaban metadata y contexto silenciosamente.

### Hallazgo
Medición inicial:
  Total docs indexados: 95
  Docs >200 chars: 94 (99%)
  Docs con ||SEP|| después de 200: 49 (52%)

Bug 1 — rag_simple.py:95
  'documento': doc[:200]
  En 49/95 docs cortaba antes del separador ||SEP||, así que
  preguntar.py no podía hacer el split y el LLM recibía solo
  la primera mitad del chunk (resumen sin términos).

Bug 2 — mesh_cache.py:144
  resultado['traduccion'][:200]
  Guardaba traducciones truncadas a 200 chars en la DB. El cache
  quedaba silenciosamente incompleto.

Bug 3 — analisis_completo_v6.5.py:286
  contexto = texto[inicio:inicio + 400]   # 400 chars
  'contexto': contexto[:150].strip()      # ← cortado a 150
  El contexto era asimétrico (200 antes + 200 después del diálogo),
  pero se reducía a 150 chars, destruyendo la simetría.

### Fix
- rag_simple.py:        'documento': doc
- mesh_cache.py:        resultado['traduccion'] (sin [:200])
- analisis_completo_v6.5.py: 'contexto': contexto.strip()

### Verificación
- py_compile OK en los 3 archivos
- 5 queries reales: 0/14 docs sin ||SEP|| (antes: ~2-3 por query)
- len típico de doc: 516 (antes: 200)

### Lección
> Los truncamientos [:N] en código de pipeline son una familia
> de bug silencioso: no rompen, no tiran error, degradan calidad.
>
> Patrón: se pone [:200] "para no inflar X", y sin querer se
> corta un separador, una metadata, o un contexto que era
> estructural.
>
> Grep recurrente para auditar:
>   grep -rn "\[:[0-9]\+\]" modulos/ scripts/ *.py
>
> Antes de tocar un truncamiento, medir:
> - ¿Qué porcentaje de datos reales supera el límite?
> - ¿El char N corta alguna estructura (separador, marca)?
> - ¿El consumidor necesita el dato completo o es display?

### Referencias
- Commit fix: (pendiente)
- Origen: auditoría con material "Debugging a Broken RAG"
- Familia de bug: mismo patrón que tests.yml (skip silencioso)

---

## 2026-09-29 — Tracing en preguntar.py (trace_id + métricas)

### Contexto
El pendiente de mayor valor del RAG era observabilidad: sin tracing,
debuggear una respuesta mala era adivinar en qué capa fallaba
(carga, BM25, contexto, o LLM).

### Implementación
En scripts/preguntar.py:
- trace_id único por invocación (8 chars, uuid4)
- logger.info en cada hito del pipeline
- Log a logs/rag.log (ignorado por .gitignore)
- print() del CLI sin cambios (UX separada de trazabilidad)
- logging.basicConfig solo en __main__ (no contamina imports)

### Los 6 hitos logueados
1. START: pregunta, nicho, top_k, modelo
2. docs_cargados: cantidad
3. bm25_resultados + top_score
4. contexto_chars: tamaño del contexto al LLM
5. respuesta_chars + elapsed
6. DONE

### Hallazgo real: el 99% del tiempo es el LLM
Primera medición end-to-end (query "salud", 13 docs):
  docs_cargados=13
  bm25_resultados=5 top_score=1.608
  contexto_chars=1911
  respuesta_chars=108
  elapsed=58.54s

Desglose:
- Cargar docs + BM25 + contexto: ~80ms
- LLM (brainhub-llama, gemma:2b Q4, CPU Termux): ~58s
  - prompt eval: 8858ms / 258 tokens (34 ms/token)
  - eval output: 38085ms / 24 tokens (1586 ms/token)

O sea: optimizar BM25 no cambia nada. El cuello es el LLM
en CPU. Para acelerar hay que atacar el modelo (cuantización,
hardware, o reducir contexto).

### Verificación
- py_compile OK
- Query real: 6 líneas de trace con mismo trace_id
- Log persiste en logs/rag.log

### Lección
> El tracing no es ceremonia. La primera corrida ya reveló
> que el 99% del tiempo es el LLM — dato que sin logs no
> se ve, y que cambia completamente las prioridades.
>
> Antes de "optimizar el RAG", medir. Casi siempre el cuello
> está donde menos se espera.

### Referencias
- Commit feat: 411702c
- Archivo: scripts/preguntar.py
- Log: logs/rag.log
- Pendiente: mismo patrón en api.py

---

### Fix: default #21 escapado del sed (2026-09-29)

Hallazgo: grep ampliado del repo entero (--include="*.py" desde raíz)
encontró 1 default roto que el sed del 2026-09-27 no vio.

`brainhub/clustering/explorar.py:25` construía el fallback con
`str(RAIZ / "data" / "analisis_consolidado.duckdb")` en vez de string
literal → ni el grep original ni el sed lo matchearon.

Fix: reemplazar por `/sdcard/Download/analisis_consolidado.duckdb`.

### Lección
> Los defaults construidos con Path() escapan a los sed de string
> literal. Grep de verificación debe incluir --include="*.py" desde
> la raíz, no solo subcarpetas conocidas.

### Referencias
- Commit fix: 94d90d3
- Defaults totales: 21 (no 20 como decía la bitácora previa)
- Tests: 115 passed, 1 skipped

---

### Observaciones: primera corrida post-fix #21 (2026-09-29 21:52)

Corrida end-to-end exitosa con video I7_WXKhyGms (MCP + vector search).

**Confirma fix #21 en producción:**
- Pipeline corrió sin BRAINHUB_DB seteada
- Consolidó OK en /sdcard/Download/analisis_consolidado.duckdb
- Default correcto en uso

**Timings en caliente (revisar bitácora previa):**
- prompt eval: 32.37 ms/token (306 tokens)
- eval output: 392.63 ms/token (38 tokens)
- Total: 24.8s LLM
- Nota: medición previa decía 1586 ms/token — probablemente cold-start.
  Corregir cuando se acumulen 3+ corridas.

**Observaciones pendientes de investigar (deuda nueva):**
1. Transcript guardado como _ES.txt pero idioma detectado = EN
   → bug de naming, no de contenido
2. Sentimiento: DESCONOCIDO 100% en 385 segmentos
   → feature devuelve default, vale revisar léxico/umbral
3. Co-ocurrencias y conceptos dominantes sí funcionan

Estas 3 observaciones NO son deuda de perímetro. Sesión aparte.

---

### Hallazgo adicional: timestamps rotos (mismo análisis 2026-09-29)

El JSON de análisis NO contiene timestamps (verificado con regex:
0 hits de MM:SS/HH:MM:SS). TimestampsDB existe, ParserVTT existe,
segmentos_timestamp en DB existe — pero nunca se pueblan.

Causa raíz (2 bugs):
1. fetch.py (youtube_transcript_api) descarta start/duration
   al escribir el .txt. Los tiene en memoria y los tira.
2. analisis_completo_v6.5.py:918 busca
   Transcript_{id}_timestamps.vtt
   pero procesar (fallback yt-dlp) nombra {id}.es.vtt
   → nunca coinciden. Además forzar_subs solo corre si la API falla.

Fix propuesto (sesión aparte, ~20-30 min):
- fetch.py escribe .vtt paralelo al .txt con el nombre que espera
  analisis_completo_v6.5
- Verificar con: JSON debe tener grounding: "HH:MM:SS-HH:MM:SS"
  en citas_clave

Habilita: RAG con cita temporal ("en 12:34 dice X").
Prioridad: Media (feature, no bug crítico — el pipeline funciona sin él).

---

### Feat: Chunker MVP (2026-09-30)

Qué: `brainhub/chunking/chunker.py` — divide texto en chunks con
metadata de provenance. 3 estrategias (oraciones/parrafos/caracteres),
10 tests, suite completa en 125 passed / 1 skipped.

Diseño (robado de Spark NLP, sin Spark NLP):
- Chunk como dataclass con metadata (start_char, end_char, n_oraciones,
  estrategia, tier)
- a_dict() explícito (consistente con timestamps.SegmentoTemporal)
- Tokenizador pluggable: regex default, NLTK opcional
- chunk_id = {video}_{pos:04d}_{sha256(texto)[:8]} → idempotente

Decisiones de diseño (evidencia):
- Estrategia default: por_oraciones (max_oraciones=10)
- Overlap: 0 (video MCP: sin beneficio medible)
- Tokenizador: regex (empata con NLTK en transcripts YouTube:
  61 vs 61 oraciones, byte-a-byte iguales — verificado 2026-09-30)
- Sin NLTK default (KISS: NLTK ya instalado pero no es más rápido
  ni mejor para subtítulos)

Artefactos:
- brainhub/chunking/__init__.py (8 líneas)
- brainhub/chunking/chunker.py (219 líneas)
- tests/test_chunker.py (100 líneas)

Verificación:
- py_compile OK
- Import real OK (atrapa archivos truncados)
- Smoke test: chunk_id estable
- 10 tests nuevos passed
- Suite completa: 125 passed, 1 skipped

Pendiente (próxima sesión):
- scripts/chunkear.py (indexar transcripts a tabla chunks)
- Modificar preguntar.py para usar chunks
- Test end-to-end con I7_WXKhyGms

### Referencias
- Commit feat: f1b922a
- Commit docs diseño: c6af333
- Aprendizaje asociado: docs/aprendizaje.md (a_dict vs ClassEncoder)

---

### Feat: Chunker MVP (2026-09-30)

Qué: `brainhub/chunking/chunker.py` — divide texto en chunks con
metadata de provenance. 3 estrategias (oraciones/parrafos/caracteres),
10 tests, suite completa en 125 passed / 1 skipped.

Diseño (robado de Spark NLP, sin Spark NLP):
- Chunk como dataclass con metadata (start_char, end_char, n_oraciones,
  estrategia, tier)
- a_dict() explícito (consistente con timestamps.SegmentoTemporal)
- Tokenizador pluggable: regex default, NLTK opcional
- chunk_id = {video}_{pos:04d}_{sha256(texto)[:8]} → idempotente

Decisiones de diseño (evidencia):
- Estrategia default: por_oraciones (max_oraciones=10)
- Overlap: 0 (video MCP: sin beneficio medible)
- Tokenizador: regex (empata con NLTK en transcripts YouTube:
  61 vs 61 oraciones, byte-a-byte iguales — verificado 2026-09-30)
- Sin NLTK default (KISS: NLTK ya instalado pero no es más rápido
  ni mejor para subtítulos)

Artefactos:
- brainhub/chunking/__init__.py (8 líneas)
- brainhub/chunking/chunker.py (219 líneas)
- tests/test_chunker.py (100 líneas)

Verificación:
- py_compile OK
- Import real OK (atrapa archivos truncados)
- Smoke test: chunk_id estable
- 10 tests nuevos passed
- Suite completa: 125 passed, 1 skipped

Pendiente (próxima sesión):
- scripts/chunkear.py (indexar transcripts a tabla chunks)
- Modificar preguntar.py para usar chunks
- Test end-to-end con I7_WXKhyGms

### Referencias
- Commit feat: f1b922a
- Commit docs diseño: c6af333
- Aprendizaje asociado: docs/aprendizaje.md (a_dict vs ClassEncoder)

---

### Ops: brainhub_backup.sh (2026-10-01)

Qué: script de backup portable. Empaqueta todo el estado de BrainHub
en un tar.gz (~350 KB) con restore.sh embebido.

Contenido del backup:
- docs/ (BITACORA, prompt_retoma, aprendizaje)
- config/ (brainhub_config.json, stopwords.json)
- db/ (analisis_consolidado.duckdb, 4.8M → comprime a ~4M)
- jsons/ (36 análisis completos)
- README_BACKUP.md + restore.sh

Portabilidad (con evidencia):
- RAIZ="$HOME/proyectos/nlp" → resuelve en runtime
- DEST_DIR="${BRAINHUB_BACKUP_DIR:-/sdcard/Download}" → override
- DB_SRC="${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}"
- Verificado: mismo script, dos destinos (default y ~/tmp/test_backup)

Verificación:
- bash -n: sintaxis OK
- Backup real: 357 KB, 49 archivos
- DB íntegra: 99 analysis, 1882 terminos_raw (extraída y consultada)
- Docs completos: BITACORA 2424 líneas

Formato tar.gz: nativo Termux, universal (Linux/macOS/Windows 10+).
Sin dependencias externas (zip/rar no requeridos).

### Referencias
- Commit ops: <HASH> (a completar)
- Script: scripts/brainhub_backup.sh
- Verificación: backup extraído en ~/tmp + duckdb SELECT COUNT

---

### Fix: stopwords incompletas en análisis V6.5 (2026-10-04)

Bug: términos clave incluían conjugaciones verbales del pretérito
(habia, estaba, tenia) y ruido de YouTube (aplausos, musica, risas).

Causa raíz: base.es cubría infinitivos + presente, faltaba pretérito
(imperfecto -aba/-ía + indefinido irregulares).

Fix: +34 pretéritos + 9 ruidos = base.es 232 → 275 palabras.

Evidencia: Transcript_P1rDVQIAOKI_ES.txt (video gaming/política)
- Antes: 'habia: 25' en top-1 términos clave
- Después: top-10 son sustantivos con sentido (equipo, juego, counter, mario)
- Co-ocurrencias: 'habia + momento' → 'juego + jugando'

Hallazgo colateral (importante):
- El JSON guardado era de una corrida vieja (con código previo)
- 'es_transcript' en brainhub/analisis/nichos.py funciona correctamente
- HABLA SÍ se agrega a nichos_para_filtrar cuando archivo es transcript
- Lección: re-analizar > auditar JSON viejo

Bugs pendientes (auditoría V6.5, ver docs/IDEAS.md §10):
- Nicho mal clasificado (dominante ≠ principal)
- Sentimiento 100% DESCONOCIDO
- Análisis temporal 100% TESTIMONIO_GENERAL
- Citas clave random

### Referencias
- Commit fix: 4b4cc34
- Archivo: stopwords.json
- Verificación: re-análisis de P1rDVQIAOKI_ES.txt

---

### Fix: nicho mal clasificado en análisis V6.5 (2026-10-04)

Bug: 3 videos de evidencia clasificados incorrectamente. 2 mal
(P1rDVQIAOKI=FINANZAS, ObiAWFqgpMg=CIBERSEGURIDAD), 1 bien
(I7_WXKhyGms=TECNOLOGIA). Re-análisis post-fix #1 mostró mismos
valores → NO era artefacto de corrida vieja.

Causa raíz (doble):
1. Substring matching sin word boundary. Términos cortos del
   diccionario ('ot', 'soc', 'ics', 'ia') matcheaban dentro de
   palabras más largas ('otro', 'social', 'physics', 'familia').
2. Argmax sin umbral. Cualquier score > 0 ganaba. Textos sin nicho
   claro siempre "ganaban algo".

Evidencia dura (ObiAWFqgpMg, prompt-eng clasificado CIBERSEGURIDAD):
- CIBERSEGURIDAD: substring=3, wordbound=0 (3 fantasmas)
- TECNOLOGIA:     substring=4, wordbound=3
- El nicho reportado estaba basado en 0 evidencia real.

Fix (2 fases):

Fase 1b — modulos/ponderacion_nichos.py + modulos/nicho_multietiqueta.py
- \b en matches de términos del diccionario
- Precompilación de patrones en __init__ (self._patrones)
- .lower()/.strip() fuera de loops internos
- ObiAWFqgpMg e I7_WXKhyGms corregidos

Fase 2 — brainhub/analisis/nichos.py
- MARGEN_MIN = 5 (top1 - top2 < 5 → GENERAL)
- Nuevo método _decidir_principal()
- principal calculado una vez, reusado en nichos_para_filtrar
- P1rDVQIAOKI → GENERAL (abstención correcta)

Verificación:
- 3/3 videos de evidencia correctos (2 con nicho, 1 abstención)
- Regresión sobre 88 análisis: 89 normales, 9 a GENERAL, 0 regresiones
- Falsos positivos cazados por umbral (verificados por lectura):
  · Ansiedad_Autoexigencia_ES: FINANZAS → GENERAL (era psicología)
  · Curso_Horacio_Anselmi_ES:  FINANZAS → GENERAL (era prep. física)
  · Transcript_P1rDVQIAOKI_ES: COMPRAS_PUBLICAS → GENERAL (era gaming)

Hallazgos laterales (no resueltos):
- Bug #2e: nicho_multietiqueta usa diccionario hardcodeado distinto
  al diccionario_nichos.json. Dos fuentes de términos inconsistentes.
- PonderacionNichos.margen_ganador declarado (=0.15) y no usado.
- Diccionario SALUD con términos en checo (kolena, lékař, operace).

Bugs pendientes (auditoría V6.5):
- Sentimiento 100% DESCONOCIDO (confirmado en los 3 videos)
- Análisis temporal 100% TESTIMONIO_GENERAL (confirmado)
- Citas clave random (confirmado)

### Referencias
- Archivos: modulos/ponderacion_nichos.py, modulos/nicho_multietiqueta.py,
  brainhub/analisis/nichos.py
- Backups: *.PRE_FASE1B (modulos), *.PRE_FASE2 (nichos.py)
- Evidencia antes/después: /sdcard/Download/Transcript_*_ES_*.json.PRE_AUDIT
- Verificación: regresión sobre 88 análisis
- Commit: (pendiente)

---

### Fix: sentimiento en español con lexicón curado (2026-10-04)

Bug: análisis de sentimiento 100% DESCONOCIDO / 0 (ruido uniforme)
en los 3 videos de evidencia. Valores: 0.06, 0.11, 0.17 (todos ≈0).

Causa raíz: textblob.TextBlob(texto).sentiment.polarity usa
léxico INGLÉS. En español, palabras positivas ("bueno", "maravilloso")
no están en el léxico -> polaridad 0. Palabras negativas ("terrible",
"horrible") sí matchean por coincidencia con inglés -> sesgo negativo.
Confirmado con test controlado (ES positivo +0.000, EN positivo +0.700).

Fix (2 partes):

Parte 1 - Generar lexicón español desde SentiWordNet + OMW 1.4:
- SentiWordNet (EN) tiene scores pos/neg por synset
- OMW 1.4 tiene lemas en español por synset (57k entradas)
- JOIN por synset_id -> ~3300 palabras ES con scores heredados
- Filtrado: descartar scores ambiguos (pos>0.3 AND neg>0.3)
- Resultado: ~2900 palabras base, 8236 con expansión morfológica

Parte 2 - Curaduría médica a mano:
- 73 términos positivos (eficaz, beneficio, mejoría, cura...)
- 91 términos negativos (adverso, mortalidad, grave, fracaso...)
- 46 términos de sesgo epistémico (preliminar, no concluyente,
  sugiere, podría ser...)
- 78 términos neutrales (tratamiento, paciente, equipo, partido...)
- JSON: lexico_medico_es.json

Merge final:
- Curado tiene prioridad sobre automático
- Excluir neutrales del resultado
- Expansión morfológica (plurales, femeninos)
- lexico_sentimiento_es.json final: 8236 palabras

Integración en v6.5:
- Nuevo módulo modulos/sentimiento_es.py (clase AnalizadorSentimientoES)
- Reemplaza textblob en analizar_sentimiento()
- Mantiene keys compat (polaridad + subjetividad) para no romper JSON/SQLite

Verificación (3 videos de evidencia):

| Video | Antes | Ahora | Interpretación |
|---|---|---|---|
| P1rDVQIAOKI | 0.06 | +0.34 | gaming/política, positivo |
| ObiAWFqgpMg | 0.17 | -0.04 | tutorial técnico, neutro |
| I7_WXKhyGms | 0.11 | -0.02 | tutorial técnico, neutro |

- 3 valores distintos (antes eran todos ~0.1)
- Coherentes con el contenido real
- min=-2.941 en ObiAWFqgpMg (segmento con carga negativa)

Hallazgos laterales:
- Frases compuestas no matchean ("no concluyente" se separa en
  "no" + "concluyente"). Pendiente n-gramas.
- Efecto colateral positivo en Bug #4: polaridades por sección
  ahora varían (0.25-0.42 en P1rDVQIAOKI vs todos ~0.05 antes).

Bugs pendientes (auditoría V6.5):
- Bug #3b: reporte muestra "DESCONOCIDO: 0.34" confuso
  (el DESCONOCIDO es el hablante, no el sentimiento)
- Bug #4: contexto temporal 100% TESTIMONIO_GENERAL
- Bug #5: citas clave random

### Referencias
- Archivos: modulos/sentimiento_es.py, lexico_medico_es.json,
  lexico_sentimiento_es.json, analisis_completo_v6.5.py
- Recursos externos: nltk (sentiwordnet, omw), OMW 1.4
- Scripts: ~/temp/derivar_lexico.py, ~/temp/merge_lexicos.py
- Commit: (pendiente)

---

### Fix: reporte confuso de sentimiento sin hablantes (2026-10-04)

Bug: el reporte mostraba "SENTIMIENTO POR HABLANTE: DESCONOCIDO: 0.34
(331 segmentos)" cuando no se detectaban hablantes. El DESCONOCIDO
es el nombre del hablante (bucket por defecto), pero al leerse parecía
indicar que el sentimiento era desconocido.

Causa: en segmentos_analizados se hardcodea 'hablante': 'DESCONOCIDO'.
Si el detector no encuentra hablantes reales, todo cae en ese bucket.
El output no distinguía "sin hablantes" de "sentimiento desconocido".

Fix (en analisis_completo_v6.5.py, 2 lugares):
- Detectar hablantes_reales = [h for h in stats_hablantes if h != 'DESCONOCIDO']
- Si hay: mostrar "SENTIMIENTO POR HABLANTE" con cada uno
- Si no: mostrar "SENTIMIENTO GLOBAL" + "(N segmentos, sin hablantes detectados)"

Verificación:
- P1rDVQIAOKI: "DESCONOCIDO: 0.34" -> "SENTIMIENTO GLOBAL: 0.34 (331 seg, sin hablantes)"
- Valor numérico intacto, presentación clara
- Análisis 1.686s (sin regresión)

Hallazgo: no era bug funcional (el cálculo estaba bien), era bug
de presentación. El nombre DESCONOCIDO era correcto pero engañoso.
Distingue: "no hay sentimiento calculado" vs "no hay hablantes".

### Referencias
- Archivo: analisis_completo_v6.5.py (líneas 382-395 y 784-797)
- Backup: analisis_completo_v6.5.py.PRE_BUG3B
- Verificación: re-análisis de P1rDVQIAOKI_ES.txt
- Commit: (pendiente)

---

### Fix: contexto temporal 99% default en transcripts (2026-10-04)

Bug: análisis temporal mostraba "TESTIMONIO_GENERAL" como
contexto_predominante en casi todas las secciones (14/15 en los
3 videos de evidencia). El clasificador de contexto discursivo
era funcionalmente inútil en transcripts de YouTube.

Evidencia (script de línea base sobre los 3 videos):
- P1rDVQIAOKI: 1008/1014 segmentos TESTIMONIO_GENERAL (99.4%)
- ObiAWFqgpMg: 419/421 (99.5%)
- I7_WXKhyGms: 1219/1226 (99.4%)
Los patrones actuales (frases formales academicas: "in my opinion",
"yo recuerdo") matchean 0.5-0.6% del habla natural.

Causa raiz (3 capas):
1. Datos: patrones son frases formales, no habla natural.
2. Logica: CONCEPTOS_POR_NICHO mezcla conceptos tematicos
   (DESARROLLO_SOFTWARE) con contextos discursivos
   (OPINION_PROFESIONAL). Solo el segundo aplica a temporal.
3. Fallback: TESTIMONIO_GENERAL es default silencioso, no
   categoria real.

Fix aplicado (Opción C - quitar del output, no arreglar):
- Consola: quitar "(TESTIMONIO_GENERAL)" del analisis temporal.
- Reporte MD: quitar columna "Contexto" de la tabla.
- Reporte MD inline: quitar contexto.
- Se mantiene el calculo interno (contexto_predominante sigue
  en el dict por si se usa en el futuro).
- No se toca clasificar_contexto() ni CONCEPTOS_POR_NICHO
  (se usan tambien en analisis_conceptos, que si funciona).

Verificacion:
- Los 3 videos muestran analisis temporal sin contexto.
- La polaridad por seccion sigue variando (0.25-0.42 en P1).
- Reporte MD con tabla de 3 columnas coherente.

Decision de diseño: preferible no mostrar un campo que miente
que mostrarlo mal. El analisis discursivo heuristico en
transcripts informales no tiene solucion rapida (requeriria
patrones de habla natural, o refactor para separar conceptos
de contextos). Se documenta como deuda tecnica en docs/IDEAS.md.

### Referencias
- Archivo: analisis_completo_v6.5.py (lineas 404, 461, 462, 465, 815)
- Backup: analisis_completo_v6.5.py.PRE_BUG4
- Verificacion: re-analisis de los 3 videos
- Commit: (pendiente)

---

## 2026-10-05 — Fix: default honesto en clasificación de contexto (bug #4)

**Commit:** c755329
**Archivo:** analisis_completo_v6.5.py
**Estado auditoría:** Alta #1 cerrada (5/5)

### Síntoma
`analisis_temporal[].contexto_predominante` mostraba `TESTIMONIO_GENERAL`
en 100% de las secciones, en todos los videos.

### Diagnóstico (con evidencia)
- `clasificar_contexto()` (L255) usaba `'TESTIMONIO_GENERAL'` como default.
- Patrones frágiles (frases literales) → recall real ≈ 1.8% en P1.
- `analisis_temporal()` (L333) agrupa con `Counter().most_common()` → el default domina por volumen.
- Contraste: `.conceptos` SÍ clasificaba bien (OPINION_PROFESIONAL: 4, TESTIMONIO_PERSONAL: 2).

### Causa raíz
Categoría de fallback disfrazada de categoría legítima contamina
agregaciones por votación. Mismo patrón conceptual que #3b.

### Fix
L261, L346, L347: `'TESTIMONIO_GENERAL'` → `'NO_CLASIFICADO'`

### Evidencia
- `grep TESTIMONIO_GENERAL` → 0 ocurrencias.
- P1 pre-fix:  5/5 `TESTIMONIO_GENERAL`
- P1 post-fix: 5/5 `NO_CLASIFICADO`

### Lección
**"Default silencioso != clasificación real."**

### Ticket derivado
Mejorar recall de `clasificar_contexto` (1.8%). Es feature, no bugfix.

### Observaciones colaterales
- Nicho `GENERAL` en video de gaming → revisar regresión #2.
- `hablantes detectados: 0` siempre → bug latente.
- Citas `[DESCONOCIDO]` incoherentes → es el Bug #5.

## 2026-10-06 — Bug #5 (citas clave) cerrado como falso positivo + Feature #1 anotada

### Bug #5: NO REPRODUCIBLE en HEAD

Los ejemplos originales ("Kisilov es el anticristo", "le duele") provienen
de Transcript_HUcIxt1v0wU_ES_analisis.txt, un output generado por script
legacy (pre-v7.2.4). El pipeline actual NO produce esas citas.

Barrido de 16 videos en playlist_brainhub: ninguna cita incoherente tipo
"Kisilov". Las citas actuales son strings entrecomillados del contenido
(código, UI, ejemplos didácticos).

Lección aplicada: "git log antes de diagnosticar"
(ya documentada en docs/aprendizaje.md, sesión 2026-10-05).

Estado: bug fantasma. Cierra sin fix.

### Feature #1 (roadmap) — Citas clave con criterio de peso semántico

Observación: el criterio actual de citas clave (extraer_dialogos, L272)
usa re.findall(r'"([^"]+)"') y no distingue habla del orador de strings
técnicos (código, mensajes de UI, prompts de ejemplo).

No es bug: no engaña de forma crítica. Es "menos útil de lo que podría ser".

Mejora propuesta (sesión futura):
- Fuente de candidatos: segmentos_analizados (no strings entrecomillados).
- Score por: frecuencia de términos clave del video + polaridad del segmento
  + coherencia temática (conceptos) + proximidad al eje del video.
- Filtros: descartar código (from X import, def, etc.), UI/metadata,
  longitud fuera de rango.
- Implementación modular (clase o módulo en brainhub/), no parche al legacy.
- Primera pieza que nace directamente en brainhub/, no migrada del legacy.

No arranca hasta sesión propia con diseño.
