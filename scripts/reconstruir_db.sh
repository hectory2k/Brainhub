#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# reconstruir_db.sh
# Reconstruye analisis_consolidado.duckdb desde los JSONs
# de análisis, aplicando el filtro VigiSalud (stopwords +
# términos vacíos) equivalente a brainhub/db/reconstruir.py
#
# Uso:
#   scripts/reconstruir_db.sh                    # defaults
#   scripts/reconstruir_db.sh /ruta/a/jsons      # dir custom
#   scripts/reconstruir_db.sh /ruta DB.duckdb    # dir + db custom
#
# Variables:
#   REGEN_STOPWORDS=0   # no regenerar stopwords.csv (usa el existente)
# ============================================================
set -euo pipefail

JSONS_DIR="${1:-/sdcard/Download}"
DB_PATH="${2:-$JSONS_DIR/analisis_consolidado.duckdb}"
STOPWORDS_CSV="$JSONS_DIR/stopwords.csv"

# Detectar raíz del proyecto (2 niveles arriba de este script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROYECTO="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "📂 JSONs:      $JSONS_DIR"
echo "💾 DB:         $DB_PATH"
echo "📋 Stopwords:  $STOPWORDS_CSV"
echo "🏠 Proyecto:   $PROYECTO"
echo

# ────────────────────────────────────────────────────────────
# 1. Regenerar stopwords.csv desde el proyecto Python
# ────────────────────────────────────────────────────────────
if [[ ! -f "$STOPWORDS_CSV" || "${REGEN_STOPWORDS:-1}" == "1" ]]; then
    echo "🔍 Extrayendo stopwords desde $PROYECTO..."
    cd "$PROYECTO"
    python3 << PYEOF
import json, sys
from pathlib import Path
sys.path.insert(0, "$PROYECTO")

todos = set()

# Stopwords del manager (todos los nichos + base, es + en)
try:
    from modulos.stopwords_manager import StopwordsManager
    sm = StopwordsManager()
    for nicho in ["GENERAL", "SALUD", "CIBERSEGURIDAD", "TECNOLOGIA",
                  "FINANZAS", "LEGAL", "AI_SAFETY", "COMPRAS_PUBLICAS"]:
        for lang in ["es", "en"]:
            todos |= sm.get_stopwords(nicho, lang)
except Exception as e:
    print(f"⚠️  stopwords_manager: {e}", file=sys.stderr)

# Términos vacíos
p = Path("$PROYECTO/terminos_vacios.json")
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))
    todos |= set(data.get("es", [])) | set(data.get("en", []))

# Coloquiales / ruido detectado empíricamente
EXTRA = {"mira", "pues", "bueno", "entonces", "este"}
todos |= EXTRA

# Normalizar
todos = {t.lower().strip() for t in todos if t and str(t).strip()}

# Escribir CSV
out = Path("$STOPWORDS_CSV")
with open(out, "w", encoding="utf-8") as f:
    for t in sorted(todos):
        f.write(f'"{t.replace(chr(34), chr(34)*2)}"\n')

print(f"✅ {len(todos)} stopwords escritas en {out}", file=sys.stderr)
PYEOF
fi

# ────────────────────────────────────────────────────────────
# 2. Reconstruir la DB
# ────────────────────────────────────────────────────────────
echo "🏗️  Reconstruyendo DB..."
cd "$JSONS_DIR"
rm -f "$DB_PATH"

duckdb "$DB_PATH" << SQL
-- ═══ Stopwords ═══
CREATE TABLE stopwords AS
SELECT lower(trim(column0)) AS term
FROM read_csv('$STOPWORDS_CSV', header=false, quote='"', escape='"');

-- ═══ analysis ═══
CREATE TABLE analysis AS
SELECT
    row_number() OVER () AS id,
    regexp_replace(
        regexp_replace(filename, '^\./', ''),
        '_analisis_completo\.json$', ''
    ) AS filename,
    COALESCE(json_extract_string(content, '\$.nicho'), 'GENERAL') AS nicho,
    COALESCE(json_extract(content, '\$.total_segmentos')::INTEGER, 0) AS total_segmentos,
    COALESCE(json_extract(content, '\$.total_dialogos')::INTEGER, 0) AS total_dialogos,
    COALESCE(json_extract(content, '\$.sentimiento_global.polaridad')::DOUBLE, 0) AS sentimiento_polaridad,
    COALESCE(json_extract(content, '\$.sentimiento_global.subjetividad')::DOUBLE, 0) AS sentimiento_subjetividad,
    json_extract_string(content, '\$.resumen_llm.texto') AS resumen_llm,
    json_extract_string(content, '\$.resumen_llm.modelo') AS resumen_modelo
FROM read_text('*_analisis_completo.json') t(filename, content);

-- ═══ terminos_raw (con filtro VigiSalud) ═══
CREATE TABLE terminos_raw AS
WITH explotado AS (
    SELECT
        regexp_replace(
            regexp_replace(filename, '^\./', ''),
            '_analisis_completo\.json$', ''
        ) AS video,
        unnest(CAST(json_extract(content, '\$.terminos_clave') AS VARCHAR[])) AS par_str
    FROM read_text('*_analisis_completo.json') t(filename, content)
),
parseado AS (
    SELECT
        video,
        json_extract_string(par_str, '\$[0]') AS term_raw,
        json_extract(par_str, '\$[1]')::INTEGER AS frequency
    FROM explotado
),
normalizado AS (
    SELECT
        video,
        lower(trim(term_raw)) AS term,
        frequency
    FROM parseado
    WHERE term_raw IS NOT NULL
      AND length(trim(term_raw)) >= 3
)
SELECT video, term, frequency
FROM normalizado n
WHERE term NOT IN (SELECT term FROM stopwords)
QUALIFY row_number() OVER (PARTITION BY video, term) = 1;

-- ═══ content_control (ESTADO: preservar/reconstruir) ═══
CREATE OR REPLACE TABLE content_control (
    content_id VARCHAR PRIMARY KEY,
    source_type VARCHAR,
    source_url VARCHAR,
    status VARCHAR DEFAULT 'pending',
    processed_at TIMESTAMP,
    error_message VARCHAR
);

-- Reconstruir desde los Transcript_*.txt existentes
INSERT INTO content_control (content_id, source_type, source_url, status, processed_at)
SELECT DISTINCT
    'youtube:' || regexp_extract(file, 'Transcript_([^_]+)', 1),
    'youtube',
    'https://youtu.be/' || regexp_extract(file, 'Transcript_([^_]+)', 1),
    'completed',
    CURRENT_TIMESTAMP
FROM glob('$JSONS_DIR/Transcript_*.txt')
WHERE regexp_extract(file, 'Transcript_([^_]+)', 1) != ''
ON CONFLICT (content_id) DO NOTHING;

-- ═══ progreso ═══
CREATE TABLE progreso AS
SELECT DISTINCT filename AS video, 'completado' AS estado FROM analysis;

-- ═══ Índices para consultas rápidas ═══
CREATE INDEX idx_terminos_term ON terminos_raw(term);
CREATE INDEX idx_terminos_video ON terminos_raw(video);
CREATE INDEX idx_analysis_nicho ON analysis(nicho);
SQL

# ────────────────────────────────────────────────────────────
# 3. Reporte final
# ────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════════════════"
echo "📊 MÉTRICAS DE RECONSTRUCCIÓN"
echo "════════════════════════════════════════════════════════════"
duckdb "$DB_PATH" << 'SQL'
SELECT 'analysis' AS tabla, count(*) AS filas FROM analysis
UNION ALL SELECT 'terminos_raw', count(*) FROM terminos_raw
UNION ALL SELECT 'progreso', count(*) FROM progreso
UNION ALL SELECT 'stopwords', count(*) FROM stopwords
ORDER BY tabla;

SELECT '── Nichos ──' AS seccion;
SELECT nicho, count(*) AS n FROM analysis GROUP BY nicho ORDER BY n DESC;

SELECT '── Top 10 términos ──' AS seccion;
SELECT term, sum(frequency) AS total
FROM terminos_raw
GROUP BY term
ORDER BY total DESC
LIMIT 10;
SQL

echo
echo "✅ DB reconstruida: $DB_PATH"
