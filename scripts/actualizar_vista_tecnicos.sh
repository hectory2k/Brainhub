#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# actualizar_vista_tecnicos.sh
# Reconstruye v_terminos_tecnicos desde:
#   - Tabla anatomia
#   - Tabla mesh_terms
#   - CSVs en data/diccionarios/*.csv
# ============================================================
set -euo pipefail

DB_PATH="${1:-${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}}"
SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_REAL")" && pwd)"
PROYECTO="$(cd "$SCRIPT_DIR/.." && pwd)"
DICCIONARIOS="$PROYECTO/data/diccionarios"

if [[ ! -f "$DB_PATH" ]]; then
    echo "❌ DB no encontrada: $DB_PATH"
    exit 1
fi

if [[ ! -d "$DICCIONARIOS" ]]; then
    echo "❌ Directorio no existe: $DICCIONARIOS"
    exit 1
fi

CSVS=$(ls "$DICCIONARIOS"/*.csv 2>/dev/null || true)
if [[ -z "$CSVS" ]]; then
    echo "❌ No hay CSVs en $DICCIONARIOS"
    exit 1
fi

echo "📂 DB:          $DB_PATH"
echo "📁 Diccionarios: $DICCIONARIOS"
echo "📄 CSVs:"
for f in $CSVS; do
    n=$(wc -l < "$f")
    echo "   $(basename "$f"): $n"
done
echo

SQL_DICCIONARIOS=""
for f in $CSVS; do
    nombre=$(basename "$f" .csv)
    case "$nombre" in
        stopwords_full|vacios)
            continue
            ;;
    esac
    if [[ -n "$SQL_DICCIONARIOS" ]]; then
        SQL_DICCIONARIOS="$SQL_DICCIONARIOS UNION "
    fi
    SQL_DICCIONARIOS="${SQL_DICCIONARIOS}
SELECT DISTINCT lower(trim(column0)) AS term, '$nombre' AS fuente
FROM read_csv('$f', header=false, ignore_errors=true)
WHERE length(trim(column0)) >= 3"
done

duckdb "$DB_PATH" << SQL
CREATE OR REPLACE TABLE terminos_diccionarios AS
$SQL_DICCIONARIOS;

CREATE OR REPLACE VIEW v_terminos_tecnicos AS
SELECT DISTINCT lower(trim(nombre_en)) AS term, 'anatomia' AS fuente
FROM anatomia WHERE nombre_en IS NOT NULL AND length(trim(nombre_en)) >= 3
UNION
SELECT DISTINCT lower(trim(nombre_es)) AS term, 'anatomia_es' AS fuente
FROM anatomia WHERE nombre_es IS NOT NULL AND length(trim(nombre_es)) >= 3
UNION
SELECT DISTINCT lower(trim(termino)) AS term, 'mesh' AS fuente
FROM mesh_terms WHERE termino IS NOT NULL AND length(trim(termino)) >= 3
UNION
SELECT DISTINCT lower(trim(unnest(string_split(sinonimos, ',')))) AS term, 'mesh_sinonimo' AS fuente
FROM mesh_terms WHERE sinonimos IS NOT NULL
UNION
SELECT term, fuente FROM terminos_diccionarios;
SQL

echo "✅ Vista actualizada:"
duckdb "$DB_PATH" -c "
SELECT fuente, count(DISTINCT term) AS n
FROM v_terminos_tecnicos
GROUP BY fuente
ORDER BY n DESC;
"

echo
echo "── Total de términos únicos ──"
duckdb "$DB_PATH" -c "
SELECT count(DISTINCT term) AS terminos_unicos
FROM v_terminos_tecnicos;
"
