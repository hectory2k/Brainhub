#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# pipeline_db.sh
# Orquesta la reconstrucción completa de la DB:
#   1. reconstruir_db.sh        → analysis, terminos_raw, progreso, stopwords
#   2. crear_tablas_tecnicas.sh → anatomia, mesh_terms, cache_mesh
#   3. extraer_diccionarios.py  → CSVs en data/diccionarios/
#   4. actualizar_vista_tecnicos.sh → v_terminos_tecnicos
#   5. guardia_contaminacion.sh → reporte de cobertura
# ============================================================
set -euo pipefail

SCRIPT_REAL="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_REAL")" && pwd)"

echo "════════════════════════════════════════════════════════════"
echo "🏗️  PIPELINE COMPLETO DE LA DB"
echo "════════════════════════════════════════════════════════════"

echo
echo "▶️  [1/5] Reconstruir tablas de análisis..."
"$SCRIPT_DIR/reconstruir_db.sh"

echo
echo "▶️  [2/5] Crear tablas técnicas (anatomía, MeSH)..."
"$SCRIPT_DIR/crear_tablas_tecnicas.sh"

echo
echo "▶️  [3/5] Extraer diccionarios a CSV..."
python3 "$SCRIPT_DIR/extraer_diccionarios.py"

echo
echo "▶️  [4/5] Actualizar vista unificada de técnicos..."
"$SCRIPT_DIR/actualizar_vista_tecnicos.sh"

echo
echo "▶️  [5/5] Guardia de contaminación..."
"$SCRIPT_DIR/guardia_contaminacion.sh" || true

echo
echo "════════════════════════════════════════════════════════════"
echo "✅ Pipeline completo"
echo "════════════════════════════════════════════════════════════"
