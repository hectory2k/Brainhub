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
> Estado: v7.2.4, 99 analysis, RAG basico, 125 tests.
> Chunker MVP implementado (brainhub/chunking/).
> Backup portable: scripts/brainhub_backup.sh.
> Modelo LLM: brainhub-llama (gemma:2b + Modelfile optimizado).
> Entry point análisis: analisis_completo_v6.5.py (legacy que consume brainhub/).
>
> AUDITORIA V6.5 (Alta #1): 5 de 5 bugs cerrados con evidencia.
> ✅ Bug #1 (stopwords incompletas) — 4b4cc34
> ✅ Bug #2 (nicho mal clasificado) — 61f503c
>    Fase 1b: word boundary + precompilacion en modulos/.
>    Fase 2: MARGEN_MIN=5 en brainhub/analisis/nichos.py.
> ✅ Bug #3a (sentimiento en español) — d153863
>    Lexico ES curado (200 terminos) + automatizado (~8000).
>    Reemplaza textblob (que usaba lexico ingles).
> ✅ Bug #3b (reporte "DESCONOCIDO" confuso) — 586f0b1
>    Renombrar a SENTIMIENTO GLOBAL cuando no hay hablantes.
> ✅ Bug #4 (analisis temporal colapsado) — c755329
>    Default honesto NO_CLASIFICADO en clasificar_contexto.
>
> AUDITORIA V6.5 (Alta #1): CERRADA.
>
> PROXIMO: Bug #5 (citas clave random) — evidencia fresca en P1:
> citas con [DESCONOCIDO] y texto fragmentado sin valor clinico.
>
> Observaciones colaterales pendientes de triage:
> - Nicho GENERAL en video de gaming (posible regresion #2).
> - hablantes_detectados=0 siempre (bug latente).
> - Recall de clasificar_contexto ≈1.8% (ticket de mejora).
>
> Aprendizajes:
> - Output confuso != bug funcional (#3b).
> - Default silencioso != clasificacion real (#4).
> - Protocolo: grep → snippet → output → fix. 2 bugs cerrados con 3 lineas.
