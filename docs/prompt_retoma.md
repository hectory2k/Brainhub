# BrainHub — Prompt de Retoma

## Bloque pegable (inicio de chat nuevo)

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

> 📚 Aprendizaje nuevo:
>    - FTS nativo de DuckDB NO existe para linux_arm64_android (HTTP 404).
>    - Alternativa: bm25s en Python (mismo resultado, sin extensiones nativas).
>    - Ollama tarda ~10s en arrancar. Chequeos con sleep 5 dan falsos negativos.
>    - `setsid nohup` mata Ollama en Termux. `nohup` sin setsid + termux-services funciona.
>    - `brainhub-llama` (2.1 GB REPACK) mata el proceso en Moto G56. qwen2.5:1.5b (1 GB) entra cómodo.
>    - `termux-services` + runit: demonización persistente, auto-restart, sobrevive cierres.
>
> 🛠️ Scripts nuevos:
>    - scripts/persistir_chunks.py → JSONs a DuckDB (tabla chunks).
>    - scripts/buscar_chunks.py → búsqueda BM25 sobre chunks.
>
> ⚠️ PENDIENTE:
>    - [x] Limpiar firma "Error 500" de fuentes .txt (archivos ya saneados).
>    - [x] Blindar ingesta: guardia en analisis_completo_v6.5.py (firma 'Error 500 (Server Error)!!1' -> exit 1). Falta el chequeo de firma en chequeo_salud.sh.
>    - [x] Mantener 5 chunks contaminados en DB como profilaxis de aprendizaje (evidencia fundamental).
>    - Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
>    - Migrar a brainhub_config (centralizar versiones hardcodeadas).
>    - Decidir convención de nombres + filtro VigiSalud en escritura (ver 🧭); luego migrar con UPDATE, no DELETE.
>    - Probar si DyhkXT_dgdk _en/_es son el mismo texto antes de decidir dedupe (el md5 exacto no alcanza).
>    - Reprocesar 6 .txt rotos sin puntuación y 2 JSONs huérfanos.
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
>    - Editar SOLO la real: regex `Última actualización: \d{4}-\d{2}-\d{2}` (matchea solo el formato real).
>    - NO usar `src.count("Última actualización:")` → dará 2 y romperá el assert.

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

> PRÓXIMO (elegir 1):
> 1. Contar términos extra vs stopwords; decidir convención y filtro; migrar con UPDATE (sin DELETE); parchar l.867 y consolidar.py:31.
> 2. Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
> 3. Migrar a brainhub_config (centralizar versiones hardcodeadas).
>


> RECORDATORIO: leer BITACORA.md y docs/aprendizaje.md
> para hallazgos del 2026-10-12 (Ollama persistente, qwen2.5:1.5b, citas semánticas).

## Fecha

Última actualización: 2026-10-14 09:00
