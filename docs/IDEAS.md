# BrainHub — Ideas Aparcadas

Ideas que **no son deuda** ni **aprendizaje** ni **estado actual**.
Son posibilidades para explorar cuando el pipeline esté maduro.

**Ciclo de vida:**
- **Aparcada acá** → cuando surge la idea
- **→ BITACORA.md** → cuando se implementa (con hash de commit)
- **→ docs/aprendizaje.md** → cuando se prueba y enseña algo (funcione o no)
- **→ Se borra** → cuando se descarta (con razón)

**Regla:** ninguna idea acá obliga a implementarla. Es un registro para no perder
contexto, no una hoja de ruta.

---

## Índice

1. [RRF para hybrid search](#1-rrf-para-hybrid-search)
2. [Section-aware + overlap para papers](#2-section-aware--overlap-para-papers)
3. [Query rewriting](#3-query-rewriting)
4. [Document grading (umbral score)](#4-document-grading-umbral-score)
5. [Guardrails out-of-domain](#5-guardrails-out-of-domain)
6. [Streaming responses (SSE)](#6-streaming-responses-sse)
7. [Cache de respuestas en DuckDB](#7-cache-de-respuestas-en-duckdb)
8. [BM25 first — validación](#8-bm25-first--validación)
9. [YouTube → Shorts con IA](#9-youtube--shorts-con-ia)

---

## 1. RRF para hybrid search

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 4.

**Qué es:** Reciprocal Rank Fusion. Fusiona dos listas de ranking (BM25 + vector)
por **posición**, no por score. Evita el problema de comparar escalas incompatibles.

    RRF_score(doc) = Σ 1 / (k + rank_i(doc))    # k ≈ 60

**Por qué aplica a BrainHub:**
- Cuando se agregue búsqueda vectorial (embeddings), hay que fusionar con BM25
- Weighted sum de scores **falla** (BM25 no es comparable con cosine)
- RRF es ~10 líneas de Python, sin dependencia

**Cuándo:** Fase 2 de chunking (después de BM25 con chunks funcionando).

**Prioridad:** Alta.

---

## 2. Section-aware + overlap para papers

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 4.

**Qué es:** Chunking que respeta secciones del documento (Abstract, Methods,
Results, Discussion) y agrega overlap entre chunks para no perder contexto
en los límites.

**Por qué aplica a BrainHub:**
- El `Chunker` actual ya tiene `overlap` como parámetro (default 0)
- Para **transcripts de YouTube**, overlap=0 es correcto (evidencia del video MCP)
- Para **PDFs científicos** (que ya procesás con `pubmed_integracion.py`),
  overlap ~200 chars + corte por sección mejora calidad

**Diferencia con la decisión actual:**
- Input = transcript → sin overlap, corte por oraciones
- Input = paper → con overlap, corte por secciones

**Cuándo:** cuando se procesen PDFs de papers sistemáticamente (sesión aparte).

**Prioridad:** Media.

---

## 3. Query rewriting

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 7.

**Qué es:** Si el retrieval devuelve pocos/no relevantes resultados, el LLM
reformula la query automáticamente antes de reintentar.

**Por qué aplica a BrainHub:**
- En `preguntar.py`, si BM25 da 0 docs con score > umbral, hoy falla
- Reformular con sinónimos / MESH terms puede recuperar
- **Requiere LLM** → ~10-20s en CPU Termux

**Cuándo:** Fase 3 de RAG (después de chunking + BM25 + embeddings).

**Prioridad:** Baja.

**Nota:** en CPU solo si el retrieval falla — no en el camino feliz.

---

## 4. Document grading (umbral score)

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 7.

**Qué es:** Después de recuperar top-K docs, filtrar por relevancia antes de
pasarlos al LLM de generación.

**Por qué aplica a BrainHub:**
- Reduce tokens de input (baja el cuello de botella real: prompt eval)
- Versión KISS: **umbral de score BM25**. Sin LLM, sin dependencia
- Si el score < X, descartar antes de armar el contexto

**Cuándo:** revisar `preguntar.py` primero (¿ya lo hace?). Después decidir.

**Prioridad:** Media.

---

## 5. Guardrails out-of-domain

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 7.

**Qué es:** Detectar si la query está fuera del dominio del corpus y abstenerse
en lugar de alucinar.

**Por qué aplica a BrainHub:**
- Si la query no matchea ningún término en `terminos_raw` / `mesh_terms` / `anatomia`,
  **no llamar al LLM** — responder "no tengo información sobre esto"
- Ya tenés precedente de abstención: `Resumen: abstencion` cuando no hay citas
- Mismo patrón, otra capa

**Cuándo:** Fase 3 de RAG (calidad).

**Prioridad:** Media.

---

## 6. Streaming responses (SSE)

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 5.

**Qué es:** Server-Sent Events para mostrar tokens al usuario a medida que
el LLM los genera, en lugar de esperar la respuesta completa.

**Por qué aplica a BrainHub:**
- El LLM en Termux tarda 30-60s
- Sin streaming: el usuario espera en silencio 60s
- Con streaming: ve tokens llegar **desde el segundo 3**
- Ollama API soporta `stream=true` nativo

**Impacto UX:** el más visible de todas las ideas.

**Cuándo:** sesión aparte (UX/CLI).

**Prioridad:** Alta.

**Costo:** ~20 líneas en `preguntar.py`.

---

## 7. Cache de respuestas en DuckDB

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 6.

**Qué es:** Cachear respuestas por hash de query. Si la pregunta es idéntica
a una anterior, devolver la respuesta guardada (0s en vez de 60s).

**Por qué aplica a BrainHub:**
- Consultas repetidas son instantáneas
- **Redis es overkill** para un usuario único
- Versión KISS: tabla `cache_respuestas` en DuckDB (`hash(query) → respuesta`)

**Esquema tentativo:**

    CREATE TABLE IF NOT EXISTS cache_respuestas (
        query_hash VARCHAR PRIMARY KEY,
        query TEXT,
        respuesta TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hits INTEGER DEFAULT 0
    );

**Cuándo:** sesión aparte (performance).

**Prioridad:** Media.

**Costo:** ~30 líneas en `preguntar.py` + schema en DB.

---

## 8. BM25 first — validación

**Fuente:** [arxiv-paper-curator](https://github.com/jamwithai/production-agentic-rag-course), Week 3.

**Qué es:** No es una idea a implementar. Es **validación externa** de una
decisión ya tomada.

**Cita del README:**
> "Unlike tutorials that jump straight to vector search, we follow the
> professional path: master keyword search foundations first, then enhance
> with vectors for hybrid retrieval."

**Por qué importa:**
- Confirma que el camino de BrainHub (BM25 antes de embeddings) es el correcto
- No es atajo, es **camino profesional**
- Cita textual para futuras discusiones de diseño

**Acción:** ninguna. Solo referencia.

**Prioridad:** N/A (documentación).

---

## 9. YouTube → Shorts con IA

**Fuente:** Idea propia (2026-09-30), inspirada en MoneyPrinterTurbo.

**Qué es:** Pipeline que toma un video de YouTube, lo analiza con BrainHub,
y genera un short vertical (9:16) con TTS + imágenes de stock.

**Componentes del flowchart propuesto:**
- `procesar` → transcript
- `analizar` → términos clave + co-ocurrencias
- Query builder → query para búsqueda de imágenes
- Pexels API → imágenes verticales
- edge-tts → voz
- moviepy → render 1080x1920

**Problemas identificados:**
- **Rompe local-first**: Pexels (API externa) + edge-tts (llamada a Microsoft)
- **No es feature de BrainHub**: consume BrainHub, no lo mejora
- **El análisis no está listo**: conceptos dominantes flojos, sentimiento default

**Reformulación correcta:**
- Proyecto aparte (`~/proyectos/moneyprinter_kiss/`)
- Consume los JSONs de BrainHub
- Local-first alternativo: `piper` TTS, imágenes locales
- Sin Pexels, o con Pexels si el usuario acepta romper offline

**Cuándo:** después de cerrar la deuda de BrainHub (chunking, timestamps,
sentimiento). No mezclar.

**Prioridad:** Baja.

---

## Notas sobre este archivo

- **No es hoja de ruta.** Es un registro.
- **No genera deuda.** No cuenta en `prompt_retoma.md` como Deuda VIVA.
- **No bloquea sesiones.** Las prioridades son orientativas.
- **Se poda.** Ideas obsoletas se borran (con razón).

Ver también:
- `docs/aprendizaje.md` — lecciones ya aprendidas
- `BITACORA.md` — historia de hechos
- `docs/prompt_retoma.md` — estado actual + próximo paso
