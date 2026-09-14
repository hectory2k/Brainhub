# Tutorial BrainHub

Guía de uso del ecosistema NLP para procesar contenido técnico.

## Requisitos

### Instalación base

```bash
git clone https://github.com/hectory2k/Brainhub.git
cd Brainhub
pip install -r requirements.txt
```

Las dependencias están en `requirements.txt`:

- `nltk`, `textblob`, `vaderSentiment` (NLP)
- `pyarrow`, `pandas` (datos)
- `flask`, `requests` (API)
- `pytest`, `pytest-cov` (tests)

### DuckDB CLI

```bash
# Termux
pkg install duckdb

# Linux/macOS
# Ver: https://duckdb.org/docs/installation
```

### NLTK WordNet (primera vez)

```bash
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### Opcionales según caso de uso

| Herramienta | Para qué | Cuándo |
|-------------|----------|--------|
| **yt-dlp** | Descargar de YouTube | Flujo 1 |
| **pdftotext** | Convertir PDF a texto | Flujo 2 |
| **poppler-utils** | Provee `pdftotext` | Flujo 2 |

**Instalar `pdftotext`:**
```bash
# Termux
pkg install poppler

# Ubuntu/Debian
apt install poppler-utils

# macOS
brew install poppler
```

## Los 2 flujos de trabajo

BrainHub tiene **2 flujos separados** según la fuente:

| Fuente | Flujo | Pipeline |
|--------|-------|----------|
| **Video YouTube** | Flujo 1 | `procesar.sh` → `analizar.sh` |
| **Paper PDF** | Flujo 2 | `procesar_paper.sh` → `analizar.sh` |

## Flujo 1: Video de YouTube

**2 comandos, 4 archivos generados.**

### Paso 1: Descargar transcript

```bash
procesar.sh "https://youtu.be/VIDEO_ID"
```

**Entrada:** URL de YouTube
**Salida:** `video_id.md` (transcripción en markdown)

Ejemplo:
```bash
procesar.sh "https://youtu.be/SbFbQ-Eie-U"
# → SbFbQ-Eie-U.md
```

### Paso 2: Analizar

```bash
analizar.sh VIDEO_ID.md
```

**Entrada:** el `.md` con la transcripción
**Salida:** 3 archivos:

1. **`db.VIDEO_ID`** — base de datos de términos y frecuencias
2. **`JSON.VIDEO_ID`** — análisis estructurado
3. **`Grafo_VIDEO_ID`** — grafo de conocimiento

Ejemplo:
```bash
analizar.sh SbFbQ-Eie-U.md
# → db.SbFbQ-Eie-U
# → JSON.SbFbQ-Eie-U
# → Grafo_SbFbQ-Eie-U
```

## Flujo 2: Paper PDF

**1 comando, hace todo el pipeline.**

### Procesar paper completo

```bash
procesar_paper.sh paper.pdf
```

**Pasos internos:**
1. **`pdftotext -layout`** — convierte PDF a texto preservando layout
2. **`descolumnar.py`** — separa las 2 columnas de papers académicos
3. **`paper.txt`** — texto limpio resultante
4. **`analizar.sh`** — pipeline NLP (nicho, términos, grafo)
5. **`documento_8020.sh`** — genera documento de estudio 80/20

**Entrada:** `paper.pdf`
**Salidas:**
- `paper_salida.txt` — texto crudo
- `paper_salida_continuo.txt` — texto descolumnado
- `db.paper` — base de datos
- `JSON.paper` — análisis
- `Grafo_paper` — grafo
- `documento_8020.md` — documento de estudio

### ¿Por qué descolumnar?

**Papers académicos suelen tener 2 columnas:**

```
┌─────────────────┬─────────────────┐
│ Columna izq 1   │ Columna der 1   │
│ Columna izq 2   │ Columna der 2   │
│ Columna izq 3   │ Columna der 3   │
└─────────────────┴─────────────────┘
```

**`pdftotext` sin descolumnar lee línea por línea:**
```
Columna izq 1   Columna der 1
Columna izq 2   Columna der 2
```

**`descolumnar.py` separa:**
```
Columna izq 1
Columna izq 2
Columna izq 3

Columna der 1
Columna der 2
Columna der 3
```

**Resultado:** texto lineal coherente para el análisis.

## Ejemplo completo (Flujo 1)

```bash
# 1. Procesar video de Kubernetes
procesar.sh "https://youtu.be/SbFbQ-Eie-U"
# → SbFbQ-Eie-U.md

# 2. Analizar
analizar.sh SbFbQ-Eie-U.md
# → db.SbFbQ-Eie-U
# → JSON.SbFbQ-Eie-U
# → Grafo_SbFbQ-Eie-U

# 3. Explorar
echo "=== Nicho ==="
jq '.nicho' JSON.SbFbQ-Eie-U

echo "=== Top términos ==="
duckdb db.SbFbQ-Eie-U -c "
  SELECT term, SUM(frequency) as total
  FROM terminos_raw
  GROUP BY term
  ORDER BY total DESC
  LIMIT 10;
"
```

## Ejemplo completo (Flujo 2)

```bash
# 1. Procesar paper completo
procesar_paper.sh attention_is_all_you_need.pdf

# 2. Ver documento 80/20
cat attention_is_all_you_need_documento_8020.md

# 3. Explorar análisis
jq '.nicho' JSON.attention_is_all_you_need
```

## Guardias (filosofía VigiSalud)

**Antes de procesar, verificar el sistema:**

```bash
bash guardias/startup_completo.sh
```

**8 guardias:**
1. identidad
2. schema_duckdb
3. stopwords
4. diccionarios
5. normalizacion
6. descolumnado
7. validador
8. terminos_raw

**Salida esperada:**
```
✅ Todas las guardias pasaron (8 verificadas)
🧠 BrainHub operativo
```

## Troubleshooting

### `procesar.sh: command not found`

```bash
ls ~/proyectos/nlp/procesar.sh
# O usar ruta completa
~/proyectos/nlp/procesar.sh "URL"
```

### `analizar.sh: command not found`

```bash
ls ~/proyectos/nlp/analizar.sh
```

### `pdftotext: command not found`

```bash
pkg install poppler    # Termux
apt install poppler-utils  # Ubuntu/Debian
brew install poppler   # macOS
```

### Error: `ModuleNotFoundError: modulos`

**Causa:** ejecutar desde directorio incorrecto.

**Fix:**
```bash
cd ~/proyectos/nlp
analizar.sh video_id.md
```

### Error: `Resource wordnet not found`

```bash
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## Estructura de archivos generados

### Flujo YouTube
```
proyectos/nlp/
├── SbFbQ-Eie-U.md           ← transcript (procesar.sh)
├── JSON.SbFbQ-Eie-U         ← análisis estructurado (analizar.sh)
├── db.SbFbQ-Eie-U           ← base de datos
└── Grafo_SbFbQ-Eie-U        ← grafo de conocimiento
```

### Flujo Paper
```
proyectos/nlp/
├── paper_salida.txt         ← pdftotext (crudo)
├── paper_salida_continuo.txt ← descolumnar (limpio)
├── JSON.paper               ← análisis estructurado
├── db.paper                 ← base de datos
├── Grafo_paper              ← grafo
└── paper_documento_8020.md  ← documento de estudio
```

## Recursos

- [README](README.md) — características y filosofía
- [CHANGELOG](CHANGELOG.md) — historial
- [ROADMAP](ROADMAP_ACTUALIZADO.md) — próximos pasos

---

¿Preguntas? Abrí un issue: https://github.com/hectory2k/Brainhub/issues
