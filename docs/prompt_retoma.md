# BrainHub — Prompt de Retoma

## Bloque pegable (inicio de chat nuevo)

> Soy Héctor, traumatólogo y desarrollador. Trabajo en BrainHub, un
> ecosistema de NLP local-first que corre en Termux/Android (Moto G56,
> Python 3.14, DuckDB CLI 1.5.5). Procesa YouTube, PDFs, GitHub y webs,
> y genera análisis estructurados + RAG sobre Ollama local.
>
> Reglas: KISS, local-first, frugal. Sin Docker, sin cloud, sin APIs externas.
> No agregar features que no resuelvan un bug. Diagnóstico con evidencia
> antes de tocar. Documentar en BITACORA.md y este archivo.
>
> Estado: v7.2.0, 99 analysis, 1782 terminos_raw, RAG basico, 116 tests.
> Deuda: 115 JSONs sin consolidar, 18 defaults Python apuntan a DB corrupta.
> Proximo paso: cerrar deuda de perimetro.
> 1. Fix 18 defaults Python (data/ -> /sdcard/) - 20 min
> 2. Regla OLLAMA_HOST=127.0.0.1 en scripts de Ollama - 5 min
> 3. Investigar 115 JSONs huerfanos sin consolidar - sesion aparte


## Fecha
2026-09-22 (última sesión: pipeline_db + verificador de claims)

## Estado (v7.2.0)
- 99 analysis en DB, 1782 terminos_raw, 4196 tecnicos
- DuckDB CLI 1.5.5, RAG básico funcionando
- Pipeline completo: procesar → analizar → pipeline_db.sh
- Deuda: 115 JSONs sin consolidar, 18 defaults Python apuntan a DB corrupta
- Config centralizado: brainhub_config.json
- 116 tests Python + 17 tests DB + 8 guardias

## Arquitectura

### Base de datos (DuckDB)
- `analysis` (99 filas) — filename, nicho, sentimiento, resumen_llm
- `terminos_raw` (1782 filas) — video, term, frequency
- `content_control` — idempotencia de ~/yt (persistente, sobrevive a reconstruccion via CREATE OR REPLACE + ON CONFLICT)
- `anatomia` (3432), `mesh_terms`, `cache_mesh`
- `v_terminos_tecnicos` (4196) — vista unificada
- `progreso`, `stopwords`, `terminos_diccionarios`

### LLM (Ollama)
- `gemma:2b` (default) — español nativo, ~30-150s por video
- `num_ctx=512`, `keep_alive=0`, `num_predict=80`
- **Muere cada 10-30 min** (Phantom Process Killer en Motorola/Android 16)
- **Fallback a plantilla** siempre disponible (nunca falla)

### RAG (BM25 + Ollama)
- `modulos/rag_simple.py` — BM25 (k1=1.5, b=0.75), plurales normalizados
- `scripts/preguntar.py` — pipeline SQL + BM25 + Ollama
- Indexa: `analysis.resumen_llm` + `terminos_raw` (JOIN + `||SEP||`)
- `responder_con_contexto()` — sintetiza respuesta final

### Chunking (PENDIENTE — próxima sesión)
- No existe `brainhub/chunking/` ni tabla `chunks`
- No existe `scripts/chunkear.py`
- Plan documentado abajo

### Config
- `brainhub_config.json` + `brainhub_config.py`
- `cfg.get('llm.modelo')`, `cfg.get('rag.top_k')`, `cfg.reload()`

## Comandos clave

### Pipeline principal
    procesar URL                     # descarga transcripcion YouTube
    analizar archivo.txt             # analisis + resumen LLM
    pipeline_db.sh                   # reconstruye DB desde JSONs

### RAG
    preguntar 'pregunta'             # RAG sobre resumenes
    preguntar 'pregunta' NICHO       # con filtro de nicho

### Ollama
    start_ollama_optimizado.sh       # arrancar con env vars optimizadas
    start_ollama_nohup               # arrancar sin tmux

### Validacion
    test_regresion_db.sh             # 17 checks
    guardia_contaminacion.sh         # cobertura de terminos
    filtro_basura.sh                 # limpieza (dry-run por defecto)
    filtro_basura.sh --apply         # aplicar limpieza
    batch_robusto.sh                 # batch con reintentos + cuarentena

### Config
    python3 -c "import brainhub_config as cfg; print(cfg.get('llm.modelo'))"

## Bugs RESUELTOS

| Fecha | Bug | Fix |
|-------|-----|-----|
| 09-15 | storage version 999 | `pkg install duckdb` |
| 09-15 | SQL injection (x4) | `_escape_sql_string` |
| 09-15 | keep_alive/num_predict | payload correcto |
| 09-15 | resumen LLM colgado | num_ctx + keep_alive |
| 09-16 | contenido legal como CIBERSEG | pendiente detector |
| 09-17 | RAG sobre resumenes no encontraba | JOIN terminos_raw + `||SEP||` |
| 09-17 | `__pycache__` obsoleto | `rm -rf scripts/__pycache__` |
| 09-17 | content_control perdida | recrear tabla |
| 09-17 | muletillas orales (pasa, hablando) | HABLA +8 terminos |
| 09-17 | warning consolidar_en_duckdb | INSERT OR IGNORE → DELETE+INSERT |
| 09-18 | content_control persistente | CREATE OR REPLACE + ON CONFLICT (e6cdf5f) |

## Deuda VIVA (priorizada)

### Alta
1. **Chunking (2-3h)** — resuelve RAG de calidad
2. **Migrar a brainhub_config (1h)** — 4 archivos: ollama_client, abstract_llm, preguntar, rag_simple

### Media
3. **Ollama estable** (sesión dedicada)
4. **analizar.sh idempotente** (10 min)

### Baja
6. Refinar validador (cobertura 12%)
7. Mejorar prompt del LLM para resumen

## Lecciones criticas

### Bash/Termux
> Heredocs con variables SIEMPRE con `<< 'EOF'` (comillas simples)
> Heredoc anidado en bash rompe Python por indentacion
> Tras editar `.py`, borrar `__pycache__` antes de probar
> Usar `~/tmp`, NO `/tmp`

### DuckDB
> Cuando DuckDB es la herramienta, no hace falta Python.
> La CLI cubre el 95% de los casos.
> `INSERT OR IGNORE` requiere PRIMARY KEY en DuckDB 1.5.5
> Las tablas DB no se recrean solas. Agregar a `reconstruir_db.sh`.

### LLM/Ollama
> El prompt del LLM no debe incluir metadata ruidosa (segmentos, polaridad)
> `keep_alive=0` + `num_predict` obligatorios
> `gemma:2b` es el sweet spot (espanol, sin alucinaciones)
> `tinyllama` alucina, no usar
> Ollama muere cada 10-30 min en Motorola + Android 16

### Pipeline
> El prompt es un snapshot, no la fuente de verdad
> Antes de arrancar: `git log --oneline -10`
> Los resumenes LLM no son buenos indices para BM25
> Los `terminos_raw` si. La mezcla funciona.

## Contexto operativo
- **Entorno:** Termux en Android (moto g56 5G, Android 16)
- **Python:** 3.14 (no 3.11)
- **DuckDB:** CLI 1.5.5 (NO modulo Python)
- **NO usar:** Docker, Kubernetes, sklearn, `pip install duckdb`
- **Ollama:** muere cada 10-30 min (Phantom Process Killer)
- **Batches largos:** wake-lock + foreground + `batch_robusto.sh`
- **Shell:** bash con `echo >>` para editar .md largos
- **Heredoc:** `<< 'EOF'` siempre

## Sesiones anteriores
- 2026-09-10: Validador federado + tests
- 2026-09-11: Lematizacion + clustering + 8 guardias
- 2026-09-15: DuckDB reconstruida + LLM + SQLi + 72 videos
- 2026-09-16: Batch + guardias + auditoria + Phantom Killer
- 2026-09-17: RAG + 5 bugs + config

Historia completa en `~/proyectos/nlp/BITACORA.md`

## Proximo paso
Chunking (2-3h) para RAG de calidad.

### Plan de chunking
1. `brainhub/chunking/chunker.py` (Clase Chunker)
2. `scripts/chunkear.py` (indexar .txt en tabla chunks)
3. Modificar `preguntar.py` para usar chunks
4. Test con video KV cache
5. Test con 4-5 preguntas

### Esquema chunks
    CREATE TABLE chunks (
        chunk_id INTEGER,
        video VARCHAR,
        posicion INTEGER,
        texto VARCHAR
    );

### Estrategias del Chunker
- `por_oraciones(texto, max_oraciones=10)`
- `por_parrafos(texto, max_parrafos=3)`
- `por_caracteres(texto, max_chars=2000, overlap=200)`

## Documentacion viva
- `BITACORA.md` — historia narrativa (1695 lineas)
- `README.md`, `TUTORIAL.md`, `ROADMAP.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
- `~/.brainhub/prompt_actual.md` — este archivo

## Comandos de arranque
    cd ~/proyectos/nlp
    git log --oneline -10
    cat ~/.brainhub/prompt_actual.md

### Cierre 2026-09-17: plantilla agregada

Documento nuevo: docs/PLANTILLA_CLASE_40MIN.md (152 lineas)

Caso de uso: preparar clase/ateneo a partir de un paper.
Flujo: analizar paper -> documento_8020 -> narrativa propia.
Ahorro: 2h 25min -> 40 min (1h 45min por clase).

Commits del dia: 11 total.
Ultimo: 328df2c (fix plantilla sin duplicacion + v7.2.0)

### Descartado hoy: Textstat
- Libreria de legibilidad (Flesch, Fernandez-Huerta, etc)
- Motivo: no resuelve ningun bug, agrega dependencia (pyphen, cmudict)
- Regla VigiSalud: no agregar features que no resuelvan un bug

### Roadmap largo plazo (diferido)
- Streamlit (demo interactiva)
- MCP server (exponer endpoints como tools)
- Jinja (templates para dashboard)
- PythonAnywhere (hosting publico)
- LiteLLM (multi-proveedor LLM)
- Grafos (8 bugs pendientes desde 2026-09-10)
- Denoise (limpieza de audio)

### Estado del proyecto al cierre
- 79 videos en DB (73+ con resumen LLM)
- RAG basico funcionando
- Config centralizado
- Prompt: 176 lineas (limpio)
- Bitacora: 957 lineas (completa)
- Plantilla: 152 lineas
- Todo pusheado a GitHub

### Proxima sesion: chunking
Plan detallado en seccion 'Proximo paso' de arriba.


### Comando nuevo: procesar PDF

    procesar archivo.pdf

Flujo completo:
1. pdftotext -layout -> txt
2. descolumnar.py (auto-deteccion)
   - Si guardia falla -> usa texto original
3. analizar -> analisis_completo_v6.5.py
4. documento_8020.sh -> documento markdown

### Bugs resueltos 2026-09-18
- procesar no detectaba PDFs
- procesar_paper.sh no encontraba analizar (era alias)
- KeyError en preguntas_debate.py (citas dict, terminos list)
- descolumnado forzado en PDFs de 1 columna

### Leccion
- Los alias NO funcionan dentro de scripts bash
- Validar isinstance() para datos que vienen en varios tipos
- /tmp no escribible en Termux -> usar ~/tmp
- Las guardias deben tener auto-fallback, no flag manual


### Fix: conceptos matcheaban por substring (2026-09-18)

Bug: 'anterior' activaba LESION_DEPORTIVA (substring matching).

Fix: word-boundary con re.search(rf"\b{re.escape(p)}\b", texto).
Aplicado en v6.3 (l.363), v6.4 (l.361), v6.5 (l.330).

Deuda técnica: v6.5 líneas 262, 319, 742 tienen substring matching sin bug confirmado.


---

### Deuda tecnica: documento 8020 (2026-09-18)

El generador 8020 (`documento_8020.sh`) funciona pero no rinde sin LLM.

**Sintoma**: contenido hueco o forzado en el documento generado.

**Causa**: dependencia de Ollama para modulos clave, y diccionarios chicos.

**Detalle**:
- Reflexiones Post-Analisis: vacias (depende de Ollama)
- MeSH Sugeridos: solo 1 match forzado ("hospital" -> "Safety-net Providers")
- Preguntas de Debate: plantillas genericas con variables, no especificas
- Resumen Ejecutivo: template rigido con variables (SALUD/TECNOLOGIA/FINANZAS)
- Jerarquia: FINANZAS y PSICOLOGIA dudosos para videos de gestion sanitaria

**Cuando mejora**: con RAM suficiente para Ollama, el contenido se vuelve real.

**Mejoras posibles** (backlog):
- Ampliar diccionario MeSH
- Templates especificos por nicho
- Fallback a heuristica cuando no hay LLM (en vez de seccion vacia)

**Decision**: no arreglar hoy. Anotar. El `_reporte.md` del analisis crudo
sigue siendo mas util que el 8020 sin LLM.


---

### Fix: analizar_github (2026-09-19)

Bug: analizaba repos equivocados por cache. El find con head -1
tomaba la primera carpeta *-main del directorio compartido.

Fix (commit 20d833c):
- Workdir con timestamp: ~/temp/github_analisis/run_YYYYMMDD_HHMMSS
- Symlink latest -> ultimo analisis
- Rotacion automatica (mantiene 5 corridas)
- Fix contador (process substitution en lugar de pipe)
- Excluye lock files (pnpm-lock, package-lock, yarn.lock, Cargo.lock)
- Excluye .json .yaml .yml .toml .xml .html .css (config/visual)

Verificado con midudev/libros-programacion-gratis:
- Antes: 11665 lineas, terminos de pnpm-lock.yaml
- Despues: 590 lineas, terminos de contenido (pdf, books, python)

### Deuda tecnica pendiente (motor analisis v6.4/v6.5)

1. **SQLite keywords.id explicito** (v6.4 linea ~518)
   - INSERT INTO keywords (id, analysis_id, ...) rompe idempotencia
   - Fix: sacar id del INSERT, dejar AUTOINCREMENT

2. **DuckDB progreso sin PK**
   - INSERT OR IGNORE INTO progreso falla con Binder Error
   - Fix: video VARCHAR PRIMARY KEY (mismo patron que content_control)

3. **Substring matching sin bug confirmado** (v6.5 lineas 262, 319, 742)


---

### Fix: analizar_github flag --docs-only (2026-09-20)

Repos de codigo puro dominaban el analisis con sintaxis del lenguaje
(self: 560, def: 134 en OracleCortex).

Fix: flag opt-in --docs-only que restringe a .md .txt .rst.

Uso:
  analizar_github.sh usuario/repo main              (default)
  analizar_github.sh usuario/repo main --docs-only  (solo docs)

Verificado en OracleCortex (30 -> 6 archivos) y midudev (sin regresion).


---

### Alineaciones con 'Scripting avanzado con Python' (2026-09-21)

Referencia: Alejandro G Vera, 'Scripting avanzado con Python', 2026.
Pensado para Kali Linux. Solo extraemos patrones arquitectonicos.

**NO aplicar**: Scapy (Cap 5), Nmap (Cap 6), Playwright (Cap 7),
framework de pentesting (Cap 12).



1. **Config con precedencia (Cap 1.3)** — 1-2h
   - default -> archivo -> env -> CLI
   - Aplicar a: ollama_client, abstract_llm, preguntar, rag_simple
   - deep_merge recursivo + build_settings + validacion
   - Cierra la deuda 'Migrar a brainhub_config (1h)'

2. **argparse con subcomandos (Cap 1.2)** — 2-3h
   - Unificar 30+ scripts en 'brainhub <comando>'
   - brainhub procesar / analizar / preguntar / pipeline
   - Codigos de salida documentados (0 ok, 2 input, 3 config, 4 op)

3. **retry_async con backoff + jitter (Cap 3)** — 1h
   - Para Ollama (muere cada 10-30 min)
   - Intentos limitados, solo errores transitorios
   - Resuelve parcialmente 'Ollama estable'

4. **Migraciones versionadas DuckDB (Cap 9.3)** — 3-4h
   - Reemplaza CREATE OR REPLACE de reconstruir_db.sh
   - MIGRATIONS dict + backup + user_version
   - No destructivo: preserva datos entre versiones

5. **Logging JSONL (Cap 1.4)** — 1-2h
   - JsonFormatter + RotatingFileHandler
   - Cada evento con run_id y profile
   - Reemplaza stdout

**Orden recomendado**: 1 -> 2 -> 3 -> 5 -> 4
El 4 es el mas invasivo. Los otros son incrementales.


---

### Regla: auditar codigo generado por IA (2026-09-21)

Codigo generado en AI Studio (Gemini) funciona en el sandbox de Google,
no en la maquina real. Antes de publicar o usar cualquier proyecto
generado por IA, auditar 5 cosas:

1. Versiones de dependencias contra npm publico
   (AI Studio inventa versiones que no existen: Vite 8, TS 7, etc.)

2. Modelos de IA contra la documentacion oficial
   (gemini-3.8-flash no existe fuera del sandbox)

3. Codigo muerto (archivos sin import, deps sin uso)
   (express, dotenv, src/server/geminiService.ts: nadie los usa)

4. Nombres por defecto del template
   ('react-example' en package.json)

5. Secretos hardcodeados o URLs expuestas

### Regla: no publicar como producto lo que no se escribio
- Codigo propio -> publicable
- Codigo generado -> auditar primero, publicar como caso de estudio
- Codigo generado y no auditado -> NO publicar

### BrainHub Studio (2026-09-21)
Estado: auditado, NO publicado, guardado en ~/brainhub-studio.
Si se retoma como herramienta personal:
  - package.json: nombre + versiones reales
  - rm -rf src/server/
  - Sacar express, dotenv, esbuild, @google/genai
  - Opcional: reemplazar Gemini por Ollama


---

### Concepto: Deuda de perimetro (2026-09-25)

Adaptado de un post de DevOps (Clarivate): el trabajo que aplazas
cuando construis el PoC fuera de los controles donde tendra que vivir.

**Regla**: antes de agregar un default, exponer un servicio o crear
un modulo nuevo, escribir 3 cosas:
1. A donde apunta por defecto
2. Quien puede acceder
3. Como se saca

**Categorizacion de deudas**:

Perimetro (seguridad + portabilidad):
- 18 defaults Python apuntan a data/analisis_consolidado.duckdb
- Ollama sin regla de host explicita (hoy seguro por default localhost)

Datos (funcionalidad):
- 115 JSONs huerfanos en /sdcard/Download/ sin consolidar

Higiene (limpieza, no bloquea):
- 2 DBs corruptas version 999 en data/ (renombradas)


### Deuda de perimetro: procesar playlists (2026-09-26)

`procesar` no acepta playlists. Detecta el ID de la playlist como si
fuera un video, extrae "PLLPJgUybOZ" y queda colgado.

**Workaround**: usar `yt-dlp` directo + `analizar` por cada `.txt`.

**Riesgo**: YouTube rate-limita (HTTP 429) si se descargan muchos
subtítulos seguidos. Esperar 1-6h entre intentos fallidos.

**Mejora posible**: nuevo script `procesar_playlist.sh` que:
- Acepta URL de playlist
- Baja subtitulos con delays grandes
- Convierte a .txt
- Corre analizar en batches de 5
- Consolida en DB

**Prioridad**: media. Util para cursos completos.

---

### Deuda de arquitectura: reconstruir_db destructivo (2026-09-26)

`reconstruir_db.sh` usa CREATE OR REPLACE TABLE en 5 tablas. NO toca
las tablas tecnicas (anatomia, mesh_terms, cache_mesh, v_terminos_tecnicos).

**Problema**: correr solo reconstruir_db.sh deja la DB sin tablas tecnicas.
Verificar con:
    duckdb /sdcard/Download/analisis_consolidado.duckdb "SHOW TABLES;"

Si falta anatomia o v_terminos_tecnicos, correr pipeline_db.sh completo.

**Prioridad**: alta.

### Deuda: analysis.filename no guarda path (2026-09-26)

`analysis` guarda filename, no el path completo. Analizar el mismo
archivo desde 2 directorios genera 2 filas con el mismo filename.
Fix manual: DELETE + reconstruir.

**Prioridad**: media.

### Hallazgo: v_terminos_tecnicos discrepa entre output y query (2026-09-26)

El pipeline imprime 3926 terminos tecnicos, pero la query directa
devuelve 4196. La vista se actualiza entre el paso 4 y el paso 5.

**Posible causa**: guardia_contaminacion.sh modifica la vista.

**Verificar**:
    grep -n "INSERT\|CREATE\|v_terminos" ~/proyectos/nlp/scripts/guardia_contaminacion.sh

**Prioridad**: baja.

---

### Sesion 2026-09-26: Curso LangGraph + fixes

**Contenido agregado**:
- 16 videos del curso 'Building Production AI Agents with LangGraph'
- 4 pendientes por rate limit: JOGT7_QUMHo, Yq-GQ-5FpYc, Z-EnYMPyrQg, EOZqDMJFnfk

**Workflow nuevo validado**:
- youtube_transcript_api (fallback de yt-dlp)
- Fallback idiomas: es -> es-US -> en
- Delays de 5-15s para evitar 429

**Numeros actualizados**: 99 analysis, 1782 terminos_raw, 4196 tecnicos

**Pendientes alta prioridad**:
1. Fix 18 defaults Python (data/ -> /sdcard/)
2. Fix reconstruir_db.sh (no toca tablas tecnicas)
3. Verificar 4 videos pendientes (esperar rate limit)

**Pendientes media prioridad**:
4. procesar_playlist.sh (formalizar workflow)
5. UNIQUE constraint en analysis.filename
6. Diccionario: agregar AGENTES_IA, LANGGRAPH

