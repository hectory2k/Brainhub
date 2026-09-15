#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# guardia_contaminacion.sh
# Detecta términos sospechosos en terminos_raw:
#   - Aparecen en >= 2 documentos
#   - NO están en v_terminos_tecnicos
# ============================================================
set -euo pipefail

DB_PATH="${1:-${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}}"
MIN_DOCS="${2:-2}"

if [[ ! -f "$DB_PATH" ]]; then
    echo "❌ DB no encontrada: $DB_PATH"
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "🔍 Guardia de contaminación"
echo "📂 DB: $DB_PATH"
echo "🎯 Términos en >= $MIN_DOCS docs, no técnicos"
echo "════════════════════════════════════════════════════════════"
echo

echo "── Términos sospechosos (por nicho) ──"
duckdb "$DB_PATH" -c "
WITH sospechosos AS (
    SELECT
        a.nicho,
        t.term,
        count(DISTINCT t.video) AS n_docs,
        sum(t.frequency) AS freq_total
    FROM terminos_raw t
    JOIN analysis a ON a.filename = t.video
    WHERE t.term NOT IN (SELECT term FROM v_terminos_tecnicos)
    GROUP BY a.nicho, t.term
    HAVING count(DISTINCT t.video) >= $MIN_DOCS
)
SELECT nicho, term, n_docs, freq_total
FROM sospechosos
ORDER BY nicho, freq_total DESC
LIMIT 40;
"

echo
echo "── Resumen por nicho ──"
duckdb "$DB_PATH" -c "
WITH sospechosos AS (
    SELECT
        a.nicho,
        t.term,
        count(DISTINCT t.video) AS n_docs
    FROM terminos_raw t
    JOIN analysis a ON a.filename = t.video
    WHERE t.term NOT IN (SELECT term FROM v_terminos_tecnicos)
    GROUP BY a.nicho, t.term
    HAVING count(DISTINCT t.video) >= $MIN_DOCS
)
SELECT nicho, count(*) AS n_sospechosos
FROM sospechosos
GROUP BY nicho
ORDER BY n_sospechosos DESC;
"

echo
echo "── Cobertura ──"
duckdb "$DB_PATH" -c "
SELECT
    count(DISTINCT term) AS terminos_totales,
    count(DISTINCT CASE WHEN term IN (SELECT term FROM v_terminos_tecnicos)
                        THEN term END) AS terminos_tecnicos,
    round(100.0 * count(DISTINCT CASE WHEN term IN (SELECT term FROM v_terminos_tecnicos)
                                      THEN term END) / count(DISTINCT term), 1) AS cobertura_pct
FROM terminos_raw;
"
