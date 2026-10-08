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
> Estado: v7.2.5, 99 analysis, 136 tests, RAG básico.
> Modelo LLM: brainhub-llama (gemma:2b, ~64s/video).
> Backup: scripts/brainhub_backup.sh.
>
> ✅ Hecho: Auditoría V6.5 (5 bugs), Chunker integrado (2d47445),
>    Feature #1 citas semánticas (034f812), Bug #8 timestamps.
>    (Detalle completo en BITACORA.md).
>
> PRÓXIMO (elegir 1):
> 1. Validar pesos del extractor de citas (mini set de 3-5 videos).
> 2. Persistencia de Chunks: tabla DuckDB `chunks` + CLI `scripts/chunkear.py`.
> 3. Migrar a `brainhub_config` (centralizar 4 archivos).
> 4. Extractor de citas para papers (adaptar a PDFs).
>
> Regla: Diagnóstico con evidencia (grep/sed) antes de tocar código.
