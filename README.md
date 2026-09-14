# BrainHub

BrainHub es un ecosistema de aprendizaje personal que procesa contenido técnico (videos, papers, transcripciones) y lo transforma en conocimiento estructurado: grafos, jerarquías de nichos, resúmenes 80/20 y preguntas de debate.

No es una herramienta de vigilancia epidemiológica. Es un sistema de aprendizaje extensible.

## Características

- Pipeline completo: procesar, analizar, consolidar
- **47+ módulos especializados**
- **Validador federado** de 5 fuentes de conocimiento (stopwords, clínicos, técnicos, MeSH, anatomía)
- **9 nichos** con detección multietiqueta + priorización + coherencia
- **Clustering K-Means** casero (sin sklearn, funciona en Termux)
- **Lematización** NLTK + mapa español (deuda/deudores/deudoras)
- **AnalizadorNichos** (orquesta 3 módulos: multietiqueta, ponderación, coherencia)
- **8 guardias** orquestadas (filosofía VigiSalud: falla antes de fallar)
- Grafo de conocimiento visual (176 nodos, 670 relaciones + analogías)
- Detector de hablantes con modos (tutorial, ateneo, legal, auto)
- Stopwords dinámicas en 5 capas
- Jerarquización de nichos (núcleo → herramienta → contexto)
- Etiquetas híbridas automáticas (HEALTH-TECH, FIN-TECH, LEGAL-SECURITY)
- Fuzzy matching para errores de transcripción
- **112 tests automatizados** + CI/CD con GitHub Actions

## Comandos

| Comando | Entrada | Salida |
|---------|---------|--------|
| procesar URL | YouTube | Transcripción .txt + VTT |
| analizar archivo.txt | Texto | Análisis NLP completo |
| consolidar | SQLite | DuckDB |

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

*Demo completo: procesar video de YouTube → análisis NLP → consulta DuckDB*

## Instalación


git clone https://github.com/hectory2k/Brainhub.git
cd Brainhub
pip install -r requirements.txt

## Tests

python3 -m pytest tests/ -v

## Métricas

- Módulos: **47+**
- Tests: **112** (2 skipped)
- Guardias: **8**
- Nichos: **9** (SALUD, TECNOLOGIA, FINANZAS, LEGAL, CIBERSEGURIDAD, AI_SAFETY, COMPRAS_PUBLICAS, PSICOLOGIA, HABLA)
- Fuentes federadas: **5** (stopwords, clínicos, técnicos, MeSH, anatomía)
- Nodos en grafo: **176**
- Relaciones: **670**
- Contenidos procesados: **57**
- CI/CD: GitHub Actions (tests + guardias)
- Plataformas: Termux (Android), Windows, Linux, macOS

---

⭐ **Si te sirve o te parece interesante, dejá una estrella en GitHub**

## Atribución

### Datos anatómicos
- **BodyParts3D 4.0**: 3,432 conceptos anatómicos (CC BY 4.0)
  - Fuente: https://lifesciencedb.jp/bp3d/
- **Human Atlas** (ashemag): atlas.json con estructura de conceptos (MIT)
  - Repo: https://github.com/ashemag/human-atlas

BrainHub usa los conceptos anatómicos como diccionario de referencia para búsquedas MeSH.
