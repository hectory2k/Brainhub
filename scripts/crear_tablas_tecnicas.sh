#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# crear_tablas_tecnicas.sh
# Agrega las tablas de términos técnicos a la DB de BrainHub:
#   - anatomia    (BodyParts3D: 3.432 conceptos)
#   - mesh_terms  (vacía, se llena on-demand desde NCBI)
#   - cache_mesh  (vacía, se llena con uso)
#   - v_terminos_tecnicos (vista unificada)
#
# Repara los módulos que dependen de estas tablas:
#   mesh_parquet, anatomia_parquet, mesh_cache,
#   sugerente_anatomia, pubmed_integracion, relaciones,
#   paginacion, integrar_duckdb, consolidar, exportar_sqlite
#
# Uso:
#   scripts/crear_tablas_tecnicas.sh [DB_PATH]
# ============================================================
set -euo pipefail

DB_PATH="${1:-${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}}"
# Resolver symlinks para que funcione desde ~/.local/bin/
SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_REAL")" && pwd)"
PROYECTO="$(cd "$SCRIPT_DIR/.." && pwd)"
CSV_ANATOMIA="$PROYECTO/data/anatomia/conceptos_bodyparts.csv"

if [[ ! -f "$DB_PATH" ]]; then
    echo "❌ DB no encontrada: $DB_PATH"
    exit 1
fi

if [[ ! -f "$CSV_ANATOMIA" ]]; then
    echo "❌ CSV de anatomía no encontrado: $CSV_ANATOMIA"
    exit 1
fi

echo "📂 DB:       $DB_PATH"
echo "📋 CSV:      $CSV_ANATOMIA"
echo

# ────────────────────────────────────────────────────────────
# Crear tablas (usando el CSV absoluto para evitar problemas de cwd)
# ────────────────────────────────────────────────────────────
duckdb "$DB_PATH" << SQL
-- ═══ Anatomía (3.432 conceptos BodyParts3D) ═══
CREATE OR REPLACE TABLE anatomia (
    concepto_id VARCHAR PRIMARY KEY,
    nombre_en VARCHAR,
    elementos INTEGER,
    -- columnas que el código Python espera pero el CSV no trae:
    nombre_es VARCHAR,
    mesh_id VARCHAR,
    sistema VARCHAR,
    categoria VARCHAR
);

COPY anatomia (concepto_id, nombre_en, elementos)
FROM '$CSV_ANATOMIA' (FORMAT CSV, HEADER);

-- ═══ MeSH (vacía, se llena on-demand desde NCBI) ═══
CREATE OR REPLACE TABLE mesh_terms (
    termino VARCHAR,
    mesh_id VARCHAR,
    sinonimos VARCHAR,
    categoria VARCHAR
);

-- ═══ Cache MeSH (vacía, se llena con uso) ═══
CREATE OR REPLACE TABLE cache_mesh (
    termino_busqueda VARCHAR PRIMARY KEY,
    mesh_id VARCHAR,
    traduccion VARCHAR,
    fecha_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══ Vista unificada de términos técnicos ═══
CREATE OR REPLACE VIEW v_terminos_tecnicos AS
SELECT DISTINCT lower(trim(nombre_en)) AS term, 'anatomia' AS fuente
FROM anatomia
WHERE nombre_en IS NOT NULL AND length(trim(nombre_en)) >= 3

UNION

SELECT DISTINCT lower(trim(nombre_es)) AS term, 'anatomia_es' AS fuente
FROM anatomia
WHERE nombre_es IS NOT NULL AND length(trim(nombre_es)) >= 3

UNION

SELECT DISTINCT lower(trim(termino)) AS term, 'mesh' AS fuente
FROM mesh_terms
WHERE termino IS NOT NULL AND length(trim(termino)) >= 3

UNION

SELECT DISTINCT lower(trim(unnest(string_split(sinonimos, ',')))) AS term,
       'mesh_sinonimo' AS fuente
FROM mesh_terms
WHERE sinonimos IS NOT NULL;
SQL

# ────────────────────────────────────────────────────────────
# Reporte
# ────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "📊 TABLAS TÉCNICAS"
echo "════════════════════════════════════════════════════════════"

duckdb "$DB_PATH" -c "
SELECT 'anatomia' AS tabla, count(*) AS filas FROM anatomia
UNION ALL SELECT 'mesh_terms', count(*) FROM mesh_terms
UNION ALL SELECT 'cache_mesh', count(*) FROM cache_mesh
UNION ALL SELECT 'v_terminos_tecnicos', count(*) FROM v_terminos_tecnicos
ORDER BY tabla;
"

echo
echo "── Muestra de anatomía ──"
duckdb "$DB_PATH" -c "
SELECT concepto_id, nombre_en, elementos
FROM anatomia
LIMIT 5;
"

echo
echo "✅ Tablas técnicas creadas"
