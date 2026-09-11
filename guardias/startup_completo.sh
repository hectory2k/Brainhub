#!/bin/bash
# Startup completo de BrainHub - cadena de guardias
# Si CUALQUIER guardia falla, el pipeline no debe arrancar

set -e

GUARDIAS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 BrainHub - Verificación de startup"
echo "===================================="

GUARDIAS=(
    identidad.sh
    schema_duckdb.sh
    stopwords.sh
    diccionarios.sh
    normalizacion.sh
    descolumnado.sh
    validador.sh     # ← NUEVA
)

FALLADAS=()
for guardia in "${GUARDIAS[@]}"; do
    echo ""
    if ! bash "$GUARDIAS_DIR/$guardia"; then
        FALLADAS+=("$guardia")
    fi
done

echo ""
echo "===================================="
if [ ${#FALLADAS[@]} -gt 0 ]; then
    echo "❌ Guardias falladas: ${FALLADAS[*]}"
    exit 1
fi

echo "✅ Todas las guardias pasaron ($(( ${#GUARDIAS[@]} )) verificadas)"
echo "🧠 BrainHub operativo"
