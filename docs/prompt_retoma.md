# BrainHub — Prompt de Retoma

## Bloque pegable (inicio de chat nuevo)

> 🚨 PROTOCOLO DE INICIO (obligatorio ANTES de diagnosticar o tocar):
>   1. Correr `git log --oneline -15` y `git status`.
>   2. Leer docs/prompt_retoma.md COMPLETO (no solo el bloque pegable).
>   3. Leer BITACORA.md (últimas 100 líneas).
>   4. Contrastar el "próximo" del retoma con los commits recientes.
>   5. Si hay divergencia → PARAR, sincronizar retoma, después trabajar.
>
> Lección: "El retoma es deuda. Verificar contra git log al iniciar."
> Incidentes registrados: Bug #4 (duplicado), Bug #5 (fantasma),
> Bug #8 (chunker ya integrado, creímos huérfano).
>
> Soy Héctor, traumatólogo y desarrollador. Trabajo en BrainHub, un
> ecosistema de NLP local-first que corre en Termux/Android (Moto G56,
> Python 3.14, DuckDB CLI 1.5.5, bm25s). Procesa YouTube, PDFs, GitHub y webs,
> y genera análisis estructurados + RAG sobre Ollama local.
>
> Reglas: KISS, local-first, frugal. Sin Docker, sin cloud, sin APIs externas.
> No agregar features que no resuelvan un bug. Diagnóstico con evidencia
> antes de tocar. Documentar en BITACORA.md y docs/aprendizaje.md.
>
> Estado: v7.2.5, 103 analysis, 137 tests, RAG con chunks + BM25 (chunks aún sin minuto).
> Modelo LLM: qwen2.5:1.5b (~97s/prompt en batch, CPU ARM).
> Backup: scripts/brainhub_backup.sh.
>
> ✅ Hecho reciente (2026-10-31 00:30): Sesión de robustez en ingesta y RAG.
>    - Blindado `scripts/procesar` contra trampa de compilación de openai-whisper en Termux.
>    - Versionado `scripts/procesar` (movido de ~/.local/bin al repo con symlink).
>    - `scripts/buscar_chunks.py` adaptado al schema real de DuckDB (chunk_id, video, t_inicio, texto).
>    - `buscar_chunks.py` migrado a subprocess + CLI de DuckDB (evita dependencia de librería Python).
>    - Corregida extracción de YouTube ID (evitar falso positivo con "Transcript_" de 11 chars).
>    - Puente minuto→chunks validado al 100%: video wvMNNDw2sN0 (81 min, 87/87 chunks anclados).
>    - Resuelto conflicto SRT vs VTT: comas→puntos en timestamps mediante micro-script de conversión.
>    - Ingestadas notas de Mg. Daniel Andrés Birchner (Inteligencia y Contrainteligencia).
>
> 📚 Aprendizaje nuevo (2026-10-31):
>    - SRT usa comas para milisegundos (`00:00:00,000`), VTT usa puntos (`00:00:00.000`).
>      El alineador falla silenciosamente (0/N chunks) si no se convierte antes.
>    - `yt-dlp` en Termux puede fallar con SSL EOF o Error 429. Fallback robusto:
>      NewPipe (Android) → descarga .srt → conversión a .vtt → pipeline normal.
>    - `--cookies-from-browser chrome` NO funciona en Termux sin root (sandboxing Android).
>      Alternativa: exportar cookies manualmente con extensión del navegador.
>    - `buscar_chunks.py` debe usar subprocess + `duckdb -json` (CLI), no `import duckdb`,
>      porque la librería Python no siempre está instalada pero el CLI sí.
>    - Regex de YouTube ID: priorizar `Transcript_([A-Za-z0-9_-]{11})` antes que
>      patrón genérico, porque "Transcript_" también tiene 11 chars y genera falsos positivos.
>
> 🛠️ Scripts nuevos/actualizados:
>    - scripts/persistir_chunks.py → JSONs a DuckDB (tabla chunks). Usa tempfile para evitar Errno 7.
>    - scripts/buscar_chunks.py → búsqueda BM25 sobre chunks con timestamps y links YouTube.
>    - scripts/alinear_chunks_vtt.py → puente minuto→chunks (heurística 6 palabras, O(N)).
>    - scripts/procesar → orquestador de ingesta (versionado en repo, symlink en ~/.local/bin).
>
> ⚠️ ESTADO DE PENDIENTES (Única fuente de verdad):
>    - [x] Limpiar firma "Error 500" y blindar ingesta en v6.5.
>    - [x] Mantener 5 chunks contaminados en DB como profilaxis.
>    - [x] Decidir convención de nombres + filtro VigiSalud (migrado con UPDATE en afe13e6).
>    - [x] Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
>    - [x] Migración mínima a brainhub_config.
>    - [x] Limpieza segura de 32 registros pendientes/huérfanos.
>    - [x] Puente minuto → chunks: validado al 100% (wvMNNDw2sN0: 87/87 anclados).
>    - [ ] Auto-detección SRT/VTT en alinear_chunks_vtt.py (parche listo, falta aplicar y commitear).
>    - [ ] Test de regresión para Bug #8 (verificar que chunker está en pipeline).
>    - [ ] Centralizar versiones hardcodeadas en brainhub_config.
>    - [ ] Reprocesar 6 .txt rotos sin puntuación y 2 JSONs huérfanos.
>
> 🎯 PRÓXIMO ÚNICO: Aplicar auto-detección SRT/VTT en alinear_chunks_vtt.py.
> **Criterio de done:**
>   - El script detecta formato por contenido (WEBVTT al inicio → VTT, si no → SRT).
>   - Convierte comas→puntos en memoria, sin tocar el archivo original.
>   - Test con el .srt de wvMNNDw2sN0: debe anclar 87/87 chunks sin conversión manual previa.
> **🚨 GUARDIA EXPLÍCITA:** No ejecutar pipeline ni reprocesos si `git status` no está limpio.
>

> 🧰 MÉTODOS DE PARCHEO SEGURO (no romper código):
>
> 1. **Siempre hacer backup antes de tocar:**
>    `cp archivo.py archivo.py.PRE_CAMBIO`
>
> 2. **Usar Python con heredoc, no sed ni cat >**
>    - `sed` rompe con caracteres especiales (tildes, >, |, comillas).
>    - `cat >` sobrescribe sin validar.
>    - Python con `assert` valida que el bloque exista antes de reemplazar.
>
> 3. **Patrón de reemplazo:**
>    - Definir `viejo` con el texto exacto (incluyendo prefijo `> ` si aplica).
>    - Definir `nuevo` con el texto nuevo.
>    - `assert src.count(viejo) == 1` antes de reemplazar.
>    - `src = src.replace(viejo, nuevo)`.
>    - `p.write_text(src, encoding="utf-8")`.
>
> 4. **Ojo con el prefijo `> ` en bloques Markdown citados.**
>    Las líneas dentro del bloque pegable empiezan con `> `.
>    Si el assert falla con count 0, revisar si falta el `>`.
>
> 5. **Siempre actualizar timestamp:**
>    - Al inicio del bloque: `> ✅ Hecho reciente (YYYY-MM-DD HH:MM):`
>    - Al final del archivo: `Última actualización: YYYY-MM-DD HH:MM`
>
> 6. **Symlink ya configurado:**
>    `~/.brainhub/prompt_actual.md -> ~/proyectos/nlp/docs/prompt_retoma.md`
>    Editar uno = editar el otro. No hace falta `cp`.
>    Después: `retoma` para verificar, `retoma-copy` para copiar al clipboard.
>
> 7. **No tocar el resto del archivo.**
>    El bloque pegable va entre `## Bloque pegable` y `## Fecha`.
>    El alias `retoma` extrae exactamente ese rango.
>
> 8. **Scripts temporales van en `~/temp/`, no en `/tmp/`.**
>    - `/tmp` en Termux/Android no es confiable.
>    - Crear: `cat > ~/temp/script_nombre.py << 'PYEOF'` ... `PYEOF`
>    - Ejecutar: `python ~/temp/script_nombre.py` desde el workdir correcto.

> 9. **Alias no funcionan en `bash -c` no-interactivo.**
>    - Los alias (`analizar`, `procesar`) solo existen en sesión interactiva.
>    - En `nohup bash -c '...'` → `command not found`.
>    - Usar path completo: `python3 ~/proyectos/nlp/analisis_completo_v6.5.py`.
>
> 10. **Procesos largos en Android: `setsid nohup` + notificación `--ongoing`.**
>    - Combo: `termux-wake-lock` + `termux-notification --id X --ongoing` + `setsid nohup bash -c '...'`.
>    - Sin esto: Android mata el proceso a los ~10-15 min.
>    - Con esto: sobrevive incluso cerrando Termux.
>    - Verificar: `pgrep -f nombre_proceso` antes de asumir que murió.
>
> 11. **Deduplicar por hash de contenido, no por nombre.**
>    - `md5sum ~/temp/*_salida_continuo.txt | sort | uniq -w32 -D`.
>    - PDFs de Anna's Archive vienen con `(1)`, `(2)` duplicados.
>    - Detectar antes de analizar, no después.
>
> 12. **Slugify al borde para prevenir "File name too long".**
>    - Límite 255 bytes por componente en ext4/F2FS.
>    - Sufijos `_analisis_completo.json` (23 chars) → stem máx ~80 chars.
>    - Función: `unicodedata.normalize("NFKD")` + `re.sub(r"[^a-z0-9_-]+", "_", s)`.
>
> 13. **`comm` es frágil con Unicode/espacios.**
>    - `comm -23 <(find ...) <(ls ... | sed ...)` falla con ñ, á, ¡.
>    - Alternativa robusta: `while IFS= read -r txt; do ... done < lista.txt`.
>    - Con check explícito: `[ ! -f "$json" ] && echo "$txt" >> pendientes.txt`.
>
> 14. **`Última actualización:` aparece 2 veces en prompt_retoma.md.**
>    - Una en la documentación del punto 5 (formato `YYYY-MM-DD HH:MM`).
>    - Otra en `## Fecha` (formato real `2026-10-11 01:04`).
>    - Editar SOLO la real: regex `Última actualización: \d{4}-\d{2}-\d{2} \d{2}:\d{2}`.
>    - **Test mínimo obligatorio:** `assert len(re.findall(r'Última actualización: \d{4}-\d{2}-\d{2} \d{2}:\d{2}', src)) == 1` antes de guardar.

### 📝 Hallazgos y Ajustes Recientes (2026-10-13)

**1. Incidente: Inyección de "Error 500" en fuentes .txt**
- **Causa**: Basura de Google ("Error 500 (Server Error)!!1500...") inyectada en archivos `.txt` fuente.
- **Impacto**: 5 chunks contaminados en DuckDB (4 en `_en`, 1 en `_es`).
- **Resolución**: Limpieza con regex + backup. Archivos `.txt` saneados.
- **Profilaxis**: Los 5 chunks se mantienen en DB como evidencia forense (no se borran).

**2. Blindaje de Ingesta**
- Guardia de ingesta en `analisis_completo_v6.5.py:694`: rechaza archivos con firma "Error 500 (Server Error)!!1" (transcripciones YouTube mal bajadas). Fuentes ya saneadas en sesión previa.
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



> RECORDATORIO: leer BITACORA.md y docs/aprendizaje.md
> para hallazgos del 2026-10-12 (Ollama persistente, qwen2.5:1.5b, citas semánticas).

## Fecha

Última actualización: 2026-10-31 00:30
