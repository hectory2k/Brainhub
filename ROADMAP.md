# Roadmap de BrainHub

Estado actual: **v7.2.0**

> Filosofía: **"El sistema falla antes de fallar."**
> Cada versión agrega guardias, tests y módulos sin romper lo anterior.

## Estado actual (v7.2.0)

| Métrica | Valor |
|---------|-------|
| Módulos | 60+ |
| Tests | 116 passing |
| Guardias | 8 |
| Nichos | 9 (con HABLA) |
| Fuentes federadas | 5 |
| Análisis en DB | 99 |
| Terminos raw | 1782 |
| Plataformas | Termux, Linux, macOS, Windows |
| CI/CD | GitHub Actions (tests + guardias) |

## En progreso (v7.3)

- [ ] **Migrar ~/yt al flujo nuevo** — delegar a yt_transcript.py (2h)
- [ ] **Migrar los 4 videos pendientes** del curso LangGraph
- [ ] **DuckDB: tablas de transcripts** — transcript_segments, transcript_tracks, analysis_evidence
- [ ] **Chunks con start/end** — vincular análisis a rango temporal
- [ ] **Reportes con links** `&t=Xs` automáticos

## Próximo (v7.4)

- [ ] **Fix 18 defaults Python** (data/ → /sdcard/)
- [ ] **Fix reconstruir_db.sh** (no toca tablas técnicas)
- [ ] **115 JSONs huérfanos** — investigar por qué no se consolidan
- [ ] **Diccionario IA** — agregar AGENTES_IA, LANGGRAPH, MULTIAGENTE

## Futuro (v8.0)

- [ ] **Alineación semántica entre idiomas** — embeddings multilingües
- [ ] **API pública** — REST con FastAPI + JWT
- [ ] **Dashboard web** — visualización de grafos y análisis
- [ ] **OCRmyPDF** — soporte para PDFs escaneados
- [ ] **Chunking avanzado** — NDJSON + overlap temporal

## Ideas a explorar

- [ ] **Embeddings semánticos** — sentence-transformers para clustering
- [ ] **RAG avanzado** — búsqueda semántica sobre los análisis
- [ ] **Integración con Obsidian** — exportar como vault
- [ ] **Voice cloning** — resúmenes en audio (ético)
- [ ] **Kubernetes deployment** — para uso en producción

## Descartado (con motivo)

- **Unsloth** (2026-09-28): requiere GPU + Python 3.11-3.13, no aplica
- **BrainHub Studio** (2026-09-21): generado por IA, no publicado
- **Textstat** (2026-09-17): no resuelve bug, agrega dependencia

## Cómo contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md)

## Cómo se decide el roadmap

1. **Bugs reales** — descubiertos con análisis de contenido real
2. **Feedback de usuarios** — issues en GitHub
3. **Filosofía VigiSalud** — si una feature mejora la robustez, entra
4. **Reutilización** — si un módulo existe sin usar, se activa

---

**Última actualización:** 2026-09-28

**¿Querés algo en el roadmap?** Abrí un issue o contactame.
