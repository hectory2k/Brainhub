# BrainHub - Documentación y Roadmap

## Fecha
2026-09-05

## Visión General
Sistema de procesamiento de conocimiento técnico con NLP, grafos, jerarquización de nichos y generación de documentos de estudio.

---

## 🎯 LOGROS ALCANZADOS

### Pipeline de Procesamiento
- [x] `procesar`: descarga transcripciones + VTT con timestamps
- [x] `analizar` v6.5: NLP completo sin DEBUG, sin hardcodear
- [x] `consolidar`: DuckDB con idempotencia
- [x] Métricas KISS: tiempo por etapa + total

### Módulos (25+)
- [x] `content_id.py`: identificación única
- [x] `content_hash.py`: detección de cambios (100% cobertura)
- [x] `detectar_nicho.py`: detección de nicho + fallback fuzzy
- [x] `fuzzy_nicho.py`: tolerancia a errores de transcripción
- [x] `nicho_multietiqueta.py`: clasificación simultánea con confianza
- [x] `etiquetas_hibridas.py`: motor de híbridos (HEALTH-TECH, FIN-TECH, LEGAL-SECURITY)
- [x] `ponderacion_nichos.py`: jerarquización multicriterio (núcleo vs secundarios)
- [x] `stopwords_manager.py`: 224 ES + EN en 5 capas
- [x] `diccionario_clinico.py`: 12 conceptos clínicos (ES + EN)
- [x] `nichos_manager.py`: diccionario de nichos desde JSON
- [x] `detector_hablantes.py`: modos tutorial, ateneo, legal, auto
- [x] `config_modos.py`: configuración separada
- [x] `relaciones.py`: extracción de relaciones
- [x] `centralidad.py`: betweenness centrality
- [x] `ontologia.py`: OntologyEngine + HealthOntology
- [x] `analogias.py`: metadata de conceptos Python
- [x] `timestamps.py`: grounding temporal
- [x] `metricas.py`: medición de pipeline
- [x] `generar_abstract.py`: resúmenes jerárquicos
- [x] `preguntas_debate.py`: generación de debate
- [x] `generar_documento.py`: documento 80/20 completo

### Clasificación Jerárquica
- [x] Fuzzy matching para errores de transcripción
- [x] Multietiqueta con scoring de confianza
- [x] Etiquetas híbridas dinámicas (sin hardcodear)
- [x] Ponderación multicriterio (densidad + posición + sintáctica)
- [x] Jerarquía: núcleo → herramienta → contexto

### Generación de Documentos
- [x] Abstract jerárquico (3 párrafos: núcleo, herramienta, contexto)
- [x] Preguntas de debate (tensión entre nichos, gaps, escalabilidad)
- [x] Documento 80/20 completo
- [x] Corrección de errores de transcripción

### Grafo de Conocimiento
- [x] 130 nodos, 503 relaciones
- [x] Betweenness centrality (datos: 0.648, salud: 0.037)
- [x] Grounding temporal (timestamps)
- [x] Exportación: PNG, HTML, JSON, Cypher, GEXF

### Gestión de Aprendizaje
- [x] `aprender`: script maestro interactivo V2
- [x] `sigue`: próximo contenido pendiente
- [x] `listo`: marcar completado
- [x] `estado`: progreso general
- [x] `alias_contenidos.csv`: nombres legibles

### Tests (48)
- [x] `test_criticos.py`: 11 tests
- [x] `test_duckdb.py`: 10 tests
- [x] `test_relaciones.py`: 3 tests
- [x] `test_detector_hablantes.py`: 5 tests
- [x] `test_timestamps.py`: 7 tests
- [x] `test_content_hash.py`: 3 tests
- [x] `test_detectar_modo.py`: 3 tests
- [x] `test_grounding.py`: 2 tests
- [x] `test_stopwords_manager.py`: 4 tests
- [x] TOTAL: 48 tests, 39% cobertura

### Almacenamiento
- [x] DuckDB: 1100+ términos, 41 contenidos
- [x] SQLite: exportación interoperable
- [x] JSON: datos estructurados
- [x] Markdown: documentos 80/20
- [x] Parquet: linkedin_insights (opcional)

### Contenidos Procesados (41)
- [x] DP-700 (2 archivos)
- [x] CAIS 2026 (3 días)
- [x] AFRICAI-RI
- [x] DefCon34
- [x] PyTorch
- [x] papers (cognitive offloading)
- [x] Y más...

---

## 📋 CHECKLIST PENDIENTE

### Publicación
- [ ] GitHub (README listo, requirements listo, .gitignore listo)
- [ ] Ejemplo público DP-700 (en `ejemplos/`)
- [ ] Dashboard Streamlit (opcional)

### VigiSalud
- [ ] Ingesta de reportes epidemiológicos
- [ ] Diccionario de vigilancia
- [ ] Series temporales

### Optimización
- [ ] OpenTelemetry (cuando haya más usuarios)
- [ ] Cobertura de tests > 50%
- [ ] GitHub Actions

---

## 🚀 PRÓXIMO PASO INMEDIATO

1. **Publicar en GitHub** (todo listo)
2. **VigiSalud proof-of-concept**
3. **Procesar más contenido clínico**

---

## 🧠 REFLEXIÓN FINAL

BrainHub evolucionó de un pipeline NLP a un sistema completo de:
- Clasificación jerárquica de nichos
- Generación de documentos de estudio
- Preguntas de debate automáticas
- Grafo de conocimiento con centralidad
- Gestión de aprendizaje personal

**El siguiente salto**: Publicar y aplicar a VigiSalud.

### Módulos Nuevos (2026-09-06)
- [x] schemas.py: validación Pydantic opcional
- [x] adapters_fuente.py: detección de fuente (YouTube, GitHub, PDF, texto)
- [x] rag_simple.py: RAG con BM25, Recall@3=1.0
- [x] guardias/: cadena de 4 precondiciones de startup
- [x] fuzzy_nicho.py: tolerancia a errores de transcripción
- [x] nicho_multietiqueta.py: clasificación simultánea con confianza
- [x] etiquetas_hibridas.py: motor de híbridos (HEALTH-TECH, FIN-TECH, LEGAL-SECURITY)
- [x] ponderacion_nichos.py: jerarquización multicriterio
- [x] generar_abstract.py: resúmenes jerárquicos
- [x] preguntas_debate.py: generación de debate
- [x] generar_documento.py: documento 80/20 completo
- [x] metricas.py: medición de pipeline (KISS)

## Actualización 2026-09-07

### CI/CD (NUEVO)
- [x] GitHub Actions: tests automáticos (28s)
- [x] GitHub Actions: guardias (9s)
- [x] deploy.sh: shadow test + commit + push
- [x] shadow_testing.py: detecta regresiones

### Módulos Nuevos
- [x] coherencia_nichos.py: valida jerarquía lógica
- [x] paginacion.py: cursor pagination DuckDB
- [x] reflexion.py: reflexiones post-análisis

### Mejoras
- [x] Scoring por densidad en detectar_nicho
- [x] Preguntas bilingües (ES/EN)
- [x] Preguntas dinámicas desde co-ocurrencias
- [x] Documento 80/20 con reflexiones integradas

## Actualización 2026-09-09

### Multiplataforma (NUEVO)
- [x] config.py centralizado
- [x] BRAINHUB_DB variable de entorno
- [x] 20 archivos sin rutas hardcodeadas
- [x] Windows compatible (PyCharm + Python 3.12)
- [x] Tests: 60 passed Termux, 52+skips CI

### Anatomía (NUEVO)
- [x] BodyParts3D: 3,432 conceptos anatómicos
- [x] Parquet 51KB en data/anatomia
- [x] Sugerente de búsquedas anatómicas
- [x] Atribución CC BY 4.0 + MIT

### Papers Científicos
- [x] Cash et al 2026 (cognición)
- [x] Hirsch et al 2026 (sesgo trans)
- [x] Flujo PDF → descolumnar → analizar

### Comparación PISA
- [x] Argentina vs El Salvador vs Costa Rica
- [x] Narrativas opuestas detectadas
