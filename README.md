# BrainHub

BrainHub es un ecosistema de aprendizaje personal que procesa contenido técnico (videos, papers, transcripciones) y lo transforma en conocimiento estructurado: grafos, jerarquías de nichos, resúmenes 80/20 y preguntas de debate.

No es una herramienta de vigilancia epidemiológica. Es un sistema de aprendizaje extensible.

## Características

- Pipeline completo: procesar, analizar, consolidar
- 25+ módulos especializados
- Grafo de conocimiento visual (130 nodos, 503 relaciones)
- Detector de hablantes con modos (tutorial, ateneo, legal, auto)
- Stopwords dinámicas en 5 capas
- Jerarquización de nichos (núcleo → herramienta → contexto)
- Etiquetas híbridas automáticas (HEALTH-TECH, FIN-TECH, LEGAL-SECURITY)
- Fuzzy matching para errores de transcripción
- 48 tests automatizados

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

## Instalación


git clone https://github.com/hectory2k/Brainhub.git
cd Brainhub
pip install -r requirements.txt

## Tests

python3 -m pytest tests/ -v

## Métricas

- Módulos: 25+
- Tests: 48
- Nodos en grafo: 130
- Relaciones: 503
- Cobertura: 39%
- Contenidos procesados: 41

---

⭐ **Si te sirve o te parece interesante, dejá una estrella en GitHub**

## Atribución

### Datos anatómicos
- **BodyParts3D 4.0**: 3,432 conceptos anatómicos (CC BY 4.0)
  - Fuente: https://lifesciencedb.jp/bp3d/
- **Human Atlas** (ashemag): atlas.json con estructura de conceptos (MIT)
  - Repo: https://github.com/ashemag/human-atlas

BrainHub usa los conceptos anatómicos como diccionario de referencia para búsquedas MeSH.
