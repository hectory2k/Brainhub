#!/data/data/com.termux/files/usr/bin/bash
# Guardia: valida invariantes de la DB DuckDB reconstruida
# Delega en scripts/test_regresion_db.sh
set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)"
exec "$SCRIPTS_DIR/test_regresion_db.sh" "$@"
