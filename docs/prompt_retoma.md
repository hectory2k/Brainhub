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
> ✅ Hecho reciente (2026-10-11 01:04):
>    - Bug #9 CERRADO: nicho DEPORTES agregado a taxonomía.
>    - Causa: keyword FINANZAS "market" demasiado genérica para contexto deportivo.
>    - Fix: detectar_nicho.py + diccionario_nichos.json + limpieza DB (0 casos restantes).
>    - BITACORA.md y docs/aprendizaje.md actualizados.
>
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

> PRÓXIMO (elegir 1):
> 1. Integrar persistir_chunks.py al pipeline_db.sh como paso 6.
> 2. Reprocesar 37 JSONs viejos sin chunks.
> 3. Migrar a brainhub_config (centralizar versiones hardcodeadas).
>
> ESTA SESIÓN: Bug #9 completamente cerrado. Listo para el siguiente objetivo.

> RECORDATORIO: leer BITACORA.md y docs/aprendizaje.md
> para hallazgos del 2026-10-11 (analizar_github, Bilibili, cloudflared).

## Fecha

Última actualización: 2026-10-11 01:04
