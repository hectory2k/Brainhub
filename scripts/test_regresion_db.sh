#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# test_regresion_db.sh
# Valida que la DB reconstruida mantiene los invariantes
# esperados (bugs resueltos no vuelven).
#
# Uso:
#   scripts/test_regresion_db.sh [DB_PATH]
#
# Retorna:
#   0 si todos los tests pasan
#   1 si alguno falla
# ============================================================
set -euo pipefail

DB_PATH="${1:-/sdcard/Download/analisis_consolidado.duckdb}"

if [[ ! -f "$DB_PATH" ]]; then
    echo "❌ DB no encontrada: $DB_PATH"
    exit 1
fi

PASS=0
FAIL=0

# Helper: compara el resultado de una query con el valor esperado
check() {
    local nombre="$1"
    local query="$2"
    local esperado="$3"
    local actual

    actual=$(duckdb "$DB_PATH" -csv -noheader -c "$query" 2>&1 | tr -d '[:space:]' | head -1)

    if [[ "$actual" == "$esperado" ]]; then
        echo "  ✅ $nombre"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $nombre"
        echo "     esperado: $esperado"
        echo "     actual:   $actual"
        FAIL=$((FAIL + 1))
    fi
}

echo "════════════════════════════════════════════════════════════"
echo "🧪 Tests de regresión DB"
echo "📂 $DB_PATH"
echo "════════════════════════════════════════════════════════════"

echo
echo "── Estructura ──"
check "tabla analysis existe" \
    "SELECT count(*) FROM information_schema.tables WHERE table_name='analysis'" \
    "1"
check "tabla terminos_raw existe" \
    "SELECT count(*) FROM information_schema.tables WHERE table_name='terminos_raw'" \
    "1"
check "tabla progreso existe" \
    "SELECT count(*) FROM information_schema.tables WHERE table_name='progreso'" \
    "1"
check "tabla stopwords existe" \
    "SELECT count(*) FROM information_schema.tables WHERE table_name='stopwords'" \
    "1"

echo
echo "── Conteos base ──"
check "analysis tiene 19 filas" \
    "SELECT count(*) FROM analysis" \
    "19"
check "progreso tiene 19 filas" \
    "SELECT count(*) FROM progreso" \
    "19"
check "terminos_raw > 200" \
    "SELECT CASE WHEN count(*) > 200 THEN 1 ELSE 0 END FROM terminos_raw" \
    "1"
check "stopwords > 500" \
    "SELECT CASE WHEN count(*) > 500 THEN 1 ELSE 0 END FROM stopwords" \
    "1"

echo
echo "── Bug #1: HABLA incompleto (muletillas filtradas) ──"
check "'cierto' NO está en terminos_raw" \
    "SELECT count(*) FROM terminos_raw WHERE term='cierto'" \
    "0"
check "'muchas' NO está en terminos_raw" \
    "SELECT count(*) FROM terminos_raw WHERE term='muchas'" \
    "0"
check "'mira' NO está en terminos_raw" \
    "SELECT count(*) FROM terminos_raw WHERE term='mira'" \
    "0"
check "'pues' NO está en terminos_raw" \
    "SELECT count(*) FROM terminos_raw WHERE term='pues'" \
    "0"

echo
echo "── Bug #5: video industrial clasifica como CIBERSEGURIDAD ──"
check "ME_lJOHAPUo es CIBERSEGURIDAD" \
    "SELECT nicho FROM analysis WHERE filename LIKE '%ME_lJOHAPUo%' LIMIT 1" \
    "CIBERSEGURIDAD"
check "ME_lJOHAPUo tiene top término ciberseguridad/planta/industrial" \
    "SELECT CASE WHEN term IN ('ciberseguridad','planta','industrial') THEN 1 ELSE 0 END
     FROM terminos_raw
     WHERE video LIKE '%ME_lJOHAPUo%'
     GROUP BY term
     ORDER BY sum(frequency) DESC
     LIMIT 1" \
    "1"

echo
echo "── Sin términos genéricos en top 10 ──"
check "ningún genérico obvio en top 10" \
    "SELECT count(*) FROM (
        SELECT term FROM terminos_raw
        GROUP BY term ORDER BY sum(frequency) DESC LIMIT 10
     ) WHERE term IN ('the','and','que','para','con','como','este','esta')" \
    "0"

echo
echo "── Sin prefijo ./ en filename ──"
check "sin prefijo ./ en analysis" \
    "SELECT count(*) FROM analysis WHERE filename LIKE './%'" \
    "0"
check "sin prefijo ./ en terminos_raw" \
    "SELECT count(*) FROM terminos_raw WHERE video LIKE './%'" \
    "0"

echo
echo "════════════════════════════════════════════════════════════"
echo "📊 RESULTADO: $PASS pasados, $FAIL fallados"
echo "════════════════════════════════════════════════════════════"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
