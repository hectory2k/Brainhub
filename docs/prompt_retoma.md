# BrainHub — Prompt de Retoma

## Bloque pegable (inicio de chat nuevo)

> Soy Héctor, traumatólogo y desarrollador. Trabajo en BrainHub, un
> ecosistema de NLP local-first que corre en Termux/Android (Moto G56,
> Python 3.14, DuckDB CLI 1.5.5). Procesa YouTube, PDFs, GitHub y webs,
> y genera análisis estructurados + RAG sobre Ollama local.
>
> Reglas: KISS, local-first, frugal. Sin Docker, sin cloud, sin APIs externas.
> No agregar features que no resuelvan un bug. Diagnóstico con evidencia
> antes de tocar. Documentar en BITACORA.md y docs/aprendizaje.md.
>
> Estado: v7.2.5, 103 analysis, 136 tests, RAG básico.
> Modelo LLM: brainhub-llama (gemma:2b, ~64s/video).
> Backup: scripts/brainhub_backup.sh.
>
> ✅ Hecho reciente (2026-10-09):
>    - Bug #21: polaridad sin acotar en extractor de citas (YouTube 108.4 → 55.8).
>    - Bug #15: DESCARTADO (falso positivo, frase 4x en fuente OracleCortex).
>    - Bugs #11-#14: entry-points (procesar GitHub, analizar_github→v6.5, DuckDB).
>    - Bug UX: analizar <URL> ahora guía al usuario.
>    - .gitignore: conflicto de merge resuelto + reglas consolidadas.
>    - bin/procesar versionado. Entry points auditados y documentados.
>    (Detalle en BITACORA.md, entradas 2026-10-09).
>
> PRÓXIMO (elegir 1):
> 1. Bug #9: nicho FINANZAS en video de combate (detectar_nicho).
> 2. Persistencia de Chunks: tabla DuckDB `chunks` + CLI `scripts/chunkear.py`.
> 3. Migrar a `brainhub_config` (centralizar versiones hardcodeadas).
> 4. Extractor de citas para papers (adaptar a PDFs).

## Fecha

Última actualización: 2026-10-09 19:36
