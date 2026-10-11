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
> Estado: v7.2.5, 103 analysis, 136 tests, RAG con chunks + BM25 + timestamp.
> Modelo LLM: brainhub-llama (gemma:2b, ~64s/video).
> Backup: scripts/brainhub_backup.sh.
>
> ✅ Hecho reciente (2026-10-11 09:50):
>    - Ingesta masiva: 155 PDFs de /sdcard/Download -> 58 documentos analizados.
>    - Pipeline end-to-end: pdftotext -> descolumnar -> V6.5 -> 80/20 -> DuckDB.
>    - Documento estrella: v1.pdf = "The Hitchhiker's Guide to Agentic Systems"
>      (H. Roitman, arXiv 2606.24937v1, 5555 segmentos, 21+ capítulos).
>    - 0 errores fatales. 142 MB. 12 escaneados pendientes de OCR.
>    - BITACORA.md y docs/aprendizaje.md actualizados.

> 📚 Aprendizaje nuevo:
>    - FTS nativo de DuckDB NO existe para linux_arm64_android (HTTP 404).
>    - Alternativa: bm25s en Python (mismo resultado, sin extensiones nativas).
>
> 🛠️ Scripts nuevos:
>    - scripts/persistir_chunks.py → JSONs a DuckDB (tabla chunks).
>    - scripts/buscar_chunks.py → búsqueda BM25 sobre chunks.
>
> ⚠️ PENDIENTE:
>    - Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
>    - Reprocesar 37 JSONs viejos sin chunks.
>    - Migrar a brainhub_config (centralizar versiones hardcodeadas).
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

> PRÓXIMO (elegir 1):
> 1. Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
> 2. Reprocesar 37 JSONs viejos sin chunks.
> 3. Migrar a brainhub_config (centralizar versiones hardcodeadas).
>
> ESTA SESIÓN (2026-10-11 09:50): ingesta masiva de PDFs.
>    - 155 PDFs de /sdcard/Download -> 58 documentos analizados (142 MB).
>    - Pipeline: pdftotext -> descolumnar -> V6.5 -> 80/20 -> DuckDB.
>    - Doc estrella: "Hitchhiker's Guide to Agentic Systems" (Roitman, arXiv).
>    - 0 errores fatales. 12 escaneados pendientes de OCR (locales).
>    - Bug #9 cerrado previamente (2026-10-10 23:03) con validación DuckDB completa.

> RECORDATORIO: leer BITACORA.md y docs/aprendizaje.md
> para hallazgos del 2026-10-11 (ingesta masiva PDFs, fallback, setsid nohup).

## Fecha

Última actualización: 2026-10-11 17:45
