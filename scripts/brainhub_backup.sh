#!/data/data/com.termux/files/usr/bin/bash
# brainhub_backup.sh — Backup portable de BrainHub
# Formato: tar.gz (nativo Termux, universal)
# Uso: bash scripts/brainhub_backup.sh
#
# Portabilidad:
# - RAIZ usa $HOME (resuelve en runtime)
# - DEST_DIR configurable via BRAINHUB_BACKUP_DIR (default /sdcard/Download)
# - DB_SRC configurable via BRAINHUB_DB (coherente con el pipeline)
# - Requisitos: tar, gzip (nativos). duckdb opcional (verificacion).
# - Para Linux/desktop: export BRAINHUB_BACKUP_DIR=~/backups
set -euo pipefail

FECHA=$(date +%Y%m%d_%H%M)
NOMBRE="brainhub_backup_$FECHA"
TMP="$HOME/.cache/$NOMBRE"
DEST_DIR="${BRAINHUB_BACKUP_DIR:-/sdcard/Download}"
DEST_FILE="$DEST_DIR/$NOMBRE.tar.gz"
RAIZ="$HOME/proyectos/nlp"

echo "📦 BrainHub Backup — $FECHA"
echo "================================"

# 0. Verificaciones
[ -f "$RAIZ/BITACORA.md" ] || { echo "❌ BITACORA.md no existe"; exit 1; }
[ -f "$RAIZ/docs/prompt_retoma.md" ] || { echo "❌ prompt_retoma.md no existe"; exit 1; }

rm -rf "$TMP"
mkdir -p "$TMP"/{docs,config,db,jsons}

# 1. Docs
cp "$RAIZ/docs/prompt_retoma.md" "$TMP/docs/"
cp "$RAIZ/docs/aprendizaje.md"   "$TMP/docs/"
cp "$RAIZ/BITACORA.md"           "$TMP/docs/"
echo "✅ docs copiados"

# 2. Config
[ -f "$RAIZ/brainhub_config.json" ] && cp "$RAIZ/brainhub_config.json" "$TMP/config/"
[ -f "$RAIZ/stopwords.json" ]      && cp "$RAIZ/stopwords.json"       "$TMP/config/"
echo "✅ config copiado"

# 3. DB
DB_SRC="${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}"
if [ -f "$DB_SRC" ]; then
    cp "$DB_SRC" "$TMP/db/"
    echo "✅ DB copiada ($(du -h "$DB_SRC" | cut -f1))"
else
    echo "⚠️  DB no encontrada en $DB_SRC"
fi

# 4. JSONs
N_JSONS=$(ls /sdcard/Download/Transcript_*_analisis_completo.json 2>/dev/null | wc -l)
if [ "$N_JSONS" -gt 0 ]; then
    cp /sdcard/Download/Transcript_*_analisis_completo.json "$TMP/jsons/"
    echo "✅ $N_JSONS JSONs copiados"
else
    echo "⚠️  no hay JSONs de análisis"
fi

# 5. README_BACKUP.md
COMMIT=$(cd "$RAIZ" && git log -1 --oneline)
cat > "$TMP/README_BACKUP.md" <<MDEOF
# BrainHub Backup — $FECHA

**Commit**: $COMMIT
**Versión**: v7.2.0

## Contenido

- docs/ — BITACORA.md, prompt_retoma.md, aprendizaje.md
- config/ — brainhub_config.json, stopwords.json
- db/ — analisis_consolidado.duckdb
- jsons/ — $N_JSONS análisis completos

## Pipeline BrainHub

\`\`\`mermaid
flowchart TD
    A[procesar URL] --> B[Transcript .txt]
    B --> C[analizar V6.5]
    C --> D[DB analisis_consolidado.duckdb]
    C --> E[JSON + MD + SQLite]
    D --> F[chunkear]
    F --> G[preguntar RAG]
\`\`\`

## Restaurar

\`\`\`bash
tar xzf $NOMBRE.tar.gz
bash $NOMBRE/restore.sh
\`\`\`
MDEOF

# 6. restore.sh
cat > "$TMP/restore.sh" <<'RSEOF'
#!/data/data/com.termux/files/usr/bin/bash
set -e
RAIZ="$HOME/proyectos/nlp"
BASE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$RAIZ/docs"

cp "$BASE/docs/prompt_retoma.md" "$RAIZ/docs/"
cp "$BASE/docs/aprendizaje.md"   "$RAIZ/docs/"
cp "$BASE/docs/BITACORA.md"      "$RAIZ/BITACORA.md"

[ -d "$BASE/config" ] && cp "$BASE/config/"* "$RAIZ/" 2>/dev/null || true
[ -f "$BASE/db/analisis_consolidado.duckdb" ] && \
    cp "$BASE/db/analisis_consolidado.duckdb" /sdcard/Download/
[ -d "$BASE/jsons" ] && cp "$BASE/jsons/"*.json /sdcard/Download/ 2>/dev/null || true

echo "✅ Restaurado. Verificar: cd $RAIZ && git status"
RSEOF
chmod +x "$TMP/restore.sh"

# 7. Empaquetar
echo ""
echo "🗜️  Empaquetando..."
cd "$(dirname "$TMP")"
tar czf "$DEST_FILE" "$NOMBRE"
rm -rf "$TMP"

# 8. Verificar
echo ""
echo "================================"
if [ -f "$DEST_FILE" ]; then
    echo "✅ Backup listo:"
    ls -lh "$DEST_FILE"
    echo ""
    echo "📋 Contenido:"
    tar tzf "$DEST_FILE" | head -20
else
    echo "❌ Backup FALLÓ"
    exit 1
fi
