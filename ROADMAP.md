# Roadmap de BrainHub

Estado actual: **v7.0.0**

> Filosofía: **"El sistema falla antes de fallar."**
> Cada versión agrega guardias, tests y módulos sin romper lo anterior.

## Estado actual (v7.0.0)

| Métrica | Valor |
|---------|-------|
| Módulos | 47+ |
| Tests | 112 passing |
| Guardias | 8 |
| Nichos | 9 (con HABLA) |
| Fuentes federadas | 5 |
| Plataformas | Termux, Linux, macOS, Windows |
| CI/CD | GitHub Actions (tests + guardias) |

## En progreso (v7.1)

- [ ] **Grafos mejorados** — 8 bugs identificados (nodos con ruido, path hardcoded)
- [ ] **Integración con denoise** — limpieza de audio antes de transcribir
- [ ] **Más módulos activados** — ~30 sin usar de 47 totales
- [ ] **Conftest.py simplificado** — eliminar 13 sys.path.insert redundantes

## Próximo (v7.2)

- [ ] **OCRmyPDF** — soporte para PDFs escaneados
- [ ] **Chunking** — procesamiento de documentos grandes (NDJSON)
- [ ] **JWT en Flask** — para uso multi-usuario
- [ ] **PostgreSQL opcional** — alternativa a DuckDB para producción

## Futuro (v8.0)

- [ ] **API pública** — REST con FastAPI + JWT
- [ ] **Dashboard web** — visualización de grafos y análisis
- [ ] **App móvil** — Android/iOS
- [ ] **Multi-idioma completo** — ES, EN, PT, CS

## Ideas a explorar

- [ ] **Embeddings semánticos** — sentence-transformers para clustering
- [ ] **RAG avanzado** — búsqueda semántica sobre los análisis
- [ ] **Integración con Obsidian** — exportar como vault
- [ ] **Voice cloning** — resúmenes en audio (ético)
- [ ] **Kubernetes deployment** — para uso en producción

## Cómo contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md)

## Cómo se decide el roadmap

1. **Bugs reales** — descubiertos con análisis de contenido real
2. **Feedback de usuarios** — issues en GitHub
3. **Filosofía VigiSalud** — si una feature mejora la robustez, entra
4. **Reutilización** — si un módulo existe sin usar, se activa

---

**Última actualización:** 2026-09-14

**¿Querés algo en el roadmap?** Abrí un issue o contactame.
