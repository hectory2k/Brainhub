#!/bin/bash
echo "🔍 Verificando terminos_raw..."
D=$(duckdb "$BRAINHUB_DB" -noheader -list -c "SELECT COUNT(*) FROM (SELECT video, term FROM terminos_raw GROUP BY video, term HAVING COUNT(*) > 1);" 2>/dev/null)
T=$(duckdb "$BRAINHUB_DB" -noheader -list -c "SELECT COUNT(*) FROM terminos_raw;" 2>/dev/null)
if [ -z "$D" ] || [ -z "$T" ]; then
    echo "⚠️  No se pudo consultar la DB"
    exit 0
fi
if [ "$D" -gt 0 ]; then
    echo "❌ $D duplicados de $T filas"
    exit 1
fi
echo "✅ Sin duplicados ($T filas)"
