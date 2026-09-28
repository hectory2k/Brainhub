# BrainHub

BrainHub es un ecosistema de aprendizaje personal que procesa contenido técnico (videos, papers, transcripciones) y lo transforma en conocimiento estructurado: grafos, jerarquías de nichos, resúmenes 80/20 y preguntas de debate.

No es una herramienta de vigilancia epidemiológica. Es un sistema de aprendizaje extensible.

## Características

- Pipeline completo: procesar, analizar, consolidar
- **57 módulos especializados**
- **Validador federado** de 5 fuentes de conocimiento (stopwords, clínicos, técnicos, MeSH, anatomía)
- **9 nichos** con detección multietiqueta + priorización + coherencia
- **Clustering K-Means** casero (sin sklearn, funciona en Termux)
- **Lematización** NLTK + mapa español (deuda/deudores/deudoras)
- **AnalizadorNichos** (orquesta 3 módulos: multietiqueta, ponderación, coherencia)
- **8 guardias** orquestadas (filosofía VigiSalud: falla antes de fallar)
- Grafo de conocimiento visual con analogías
- Detector de hablantes con modos (tutorial, ateneo, legal, auto)
- Stopwords dinámicas en 5 capas
- Jerarquización de nichos (núcleo → herramienta → contexto)
- Etiquetas híbridas automáticas (HEALTH-TECH, FIN-TECH, LEGAL-SECURITY)
- Fuzzy matching para errores de transcripción
- **Trazabilidad temporal**: cada mención tiene timestamp verificable
- **116 tests automatizados** + CI/CD con GitHub Actions

## Comandos

| Comando | Entrada | Salida |
|---------|---------|--------|
| procesar URL | YouTube | Transcripción .txt + VTT |
| analizar archivo.txt | Texto | Análisis NLP completo |
| consolidar | SQLite | DuckDB |
| yt_transcript.py inspect VIDEO_ID | YouTube | Lista de pistas disponibles |
| yt_transcript.py fetch VIDEO_ID | YouTube | Corpus estructurado con roles |
| yt_transcript.py validate VIDEO_ID | Pista | Validación de sincronización |
| yt_transcript.py link VIDEO_ID --at MM:SS | Pista | Link al minuto exacto |

## Trazabilidad temporal

BrainHub guarda el timestamp de cada tema, idea y mención. Y no los inventa — los verifica.

**La diferencia con otras herramientas de IA**: cuando un LLM te dice "esto se dijo en el minuto 5:20", puede estar alucinando. El minuto lo genera el modelo, no el video.

En BrainHub, el minuto viene del video mismo (via `youtube_transcript_api`). El modelo no puede inventarlo. Y antes de confiar en él, se valida: 5 puntos distribuidos en el video, contra el audio real.

**Ejemplo**:

    $ yt_transcript.py link HNClGfpmSfk --at 3:45
    https://youtu.be/HNClGfpmSfk?t=225

## Aprendizaje

| Comando | Descripción |
|---------|-------------|
| aprender | Menú interactivo maestro |
| sigue | Próximo contenido pendiente |
| listo <id> | Marca contenido como completado |
| estado | Muestra progreso general |

## Filosofía

**"El sistema falla antes de fallar."**

BrainHub usa **8 guardias** que detectan problemas antes de que lleguen al usuario:

- Cambios en stopwords → `guardias/stopwords.sh`
- Cambios en diccionarios → `guardias/diccionarios.sh`
- ñ rota en normalización → `guardias/normalizacion.sh`
- Validador federado roto → `guardias/validador.sh`
- Duplicados en DB → `guardias/terminos_raw.sh`
- Schema DuckDB cambiado → `guardias/schema_duckdb.sh`
- Identidad de contenido → `guardias/identidad.sh`
- Descolumnado inválido → `guardias/descolumnado.sh`

**Arquitectura de federación:**

Agregar conocimiento = editar JSON, no código.
Nueva fuente = 1 archivo JSON + 1 método `_cargar_X()`.

**Idempotencia:**

Cada análisis es idempotente: DELETE antes de INSERT, sin duplicados.

## Demo

[![asciicast](https://asciinema.org/a/EqWi4xkuVw3Bvsp0.svg)](https://asciinema.org/a/EqWi4xkuVw3Bvsp0)

*Demo: procesar video de YouTube → análisis NLP → consulta DuckDB*

## Instalación

    git clone https://github.com/hectory2k/Brainhub.git
    cd Brainhub
    pip install -r requirements.txt

## Tests

    python3 -m pytest tests/ -v

## Métricas

- Módulos: **57**
- Tests: **116**
- Guardias: **8**
- Nichos: **9** (SALUD, TECNOLOGIA, FINANZAS, LEGAL, CIBERSEGURIDAD, AI_SAFETY, COMPRAS_PUBLICAS, PSICOLOGIA, HABLA)
- Fuentes federadas: **5** (stopwords, clínicos, técnicos, MeSH, anatomía)
- Análisis en DB: **99**
- Términos raw: **1782**
- Términos técnicos: **4196**
- Anatomía: **3432** conceptos
- Plataformas: Termux (Android), Windows, Linux, macOS

---

⭐ **Si te sirve o te parece interesante, dejá una estrella en GitHub**

## Proyectos relacionados

Parte de un ecosistema más amplio:

- 🏥 **[VigiSalud](https://github.com/hectory2k/VigiSalud)** — Vigilancia epidemiológica con NLP
  *Procesa datos de salud pública y detecta patrones.*

- 🇦🇷 **[Argentina Hub](https://github.com/hectory2k/argentina-hub)** — Datos abiertos de Argentina
  *Agrega, normaliza y visualiza datos públicos.*

- 🎵 **[denoise](https://github.com/CristianRojas-SoftwareEngineer/Denoise)** — Limpieza de audio (Rust + ONNX)
  *Proyecto amigo. Limpia audio de videos antes de transcribir.*

**Sinergia:**

    denoise (audio limpio) → BrainHub (transcripción + análisis) → VigiSalud (epidemiología)
                                                                  ↘ Argentina Hub (datos abiertos)

## Autor

**Héctor López** — Ingeniero, entusiasta de NLP y automatización.

- 🔗 [LinkedIn](https://www.linkedin.com/in/hectorlopezit)
- 💻 [GitHub](https://github.com/hectory2k)
- 📧 beat006@gmail.com

*BrainHub nació como herramienta personal y creció hasta convertirse en un ecosistema extensible.*

## Atribución

### Datos anatómicos
- **BodyParts3D 4.0**: 3,432 conceptos anatómicos (CC BY 4.0)
  - Fuente: https://lifesciencedb.jp/bp3d/
- **Human Atlas** (ashemag): atlas.json con estructura de conceptos (MIT)
  - Repo: https://github.com/ashemag/human-atlas

BrainHub usa los conceptos anatómicos como diccionario de referencia para búsquedas MeSH.
