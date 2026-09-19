#!/bin/bash
# ==============================================
# ANALIZAR REPOSITORIO DE GITHUB
# Uso: ./analizar_github.sh usuario/repo [rama]
# Ejemplo: ./analizar_github.sh midudev/libros-programacion-gratis main
# ==============================================

REPO="$1"
BRANCH="${2:-main}"

if [ -z "$REPO" ]; then
    echo "❌ Uso: ./analizar_github.sh usuario/repo [rama]"
    echo "📋 Ejemplo: ./analizar_github.sh midudev/libros-programacion-gratis main"
    exit 1
fi

# --- Workdir temporal con timestamp (evita cache entre corridas) ---
BASE_DIR="$HOME/temp/github_analisis"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
WORK_DIR="$BASE_DIR/run_$TIMESTAMP"
LATEST_LINK="$BASE_DIR/latest"

mkdir -p "$WORK_DIR"
ln -sfn "$WORK_DIR" "$LATEST_LINK"

# Rotacion: mantener solo las ultimas 5 corridas
ls -dt "$BASE_DIR"/run_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null

echo "🚀 ANALIZANDO REPOSITORIO: $REPO"
echo "================================="
echo "📂 Rama: $BRANCH"
echo "📁 Workdir: $WORK_DIR"
echo "🔗 Latest: $LATEST_LINK"
echo ""

# 1. Descargar el repositorio como ZIP
echo "📥 Descargando repositorio..."
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
ZIP_FILE="$WORK_DIR/${REPO//\//_}_$BRANCH.zip"

curl -L -o "$ZIP_FILE" "$ZIP_URL" 2>/dev/null
if [ $? -ne 0 ] || [ ! -s "$ZIP_FILE" ]; then
    echo "❌ Error al descargar: $ZIP_URL"
    exit 1
fi
echo "✅ ZIP descargado: $(basename "$ZIP_FILE")"

# 2. Extraer archivos
echo "📦 Extrayendo archivos..."
REPO_NAME=$(basename "$REPO")
EXTRACT_DIR="$WORK_DIR/${REPO_NAME}-$BRANCH"

unzip -q "$ZIP_FILE" -d "$WORK_DIR" 2>/dev/null

if [ ! -d "$EXTRACT_DIR" ]; then
    # Fallback: buscar cualquier carpeta extraida en ESTE workdir
    EXTRACT_DIR=$(find "$WORK_DIR" -maxdepth 1 -type d -name "*${REPO_NAME}*" | head -1)
fi

if [ -n "$EXTRACT_DIR" ] && [ -d "$EXTRACT_DIR" ]; then
    echo "✅ Extraído en: $(basename "$EXTRACT_DIR")"
else
    echo "❌ No se pudo encontrar la carpeta extraída"
    exit 1
fi

# 3. Buscar archivos de texto relevantes
echo "🔍 Buscando archivos relevantes..."
TEMP_FILE="$WORK_DIR/texto_combinado.txt"
> "$TEMP_FILE"

# Contar archivos encontrados (fix: process substitution)
FILE_COUNT=0
while read -r file; do
    echo "--- Archivo: $(basename "$file") ---" >> "$TEMP_FILE"
    cat "$file" 2>/dev/null >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    FILE_COUNT=$((FILE_COUNT + 1))
done < <(find "$EXTRACT_DIR" -type f \( \
    -name "*.md" -o \
    -name "*.txt" -o \
    -name "*.rst" -o \
    -name "*.py" -o \
    -name "*.js" -o \
    -name "*.java" -o \
    -name "*.c" -o \
    -name "*.cpp" -o \
    -name "*.h" -o \
    -name "*.go" -o \
    -name "*.rs" -o \
    -name "*.sh" \
\) \
-not -name "pnpm-lock.yaml" \
-not -name "package-lock.json" \
-not -name "yarn.lock" \
-not -name "poetry.lock" \
-not -name "Cargo.lock" \
-not -name "Gemfile.lock" \
-not -name "composer.lock" \
-not -name "*.lock" \
-not -path "*/.*" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" 2>/dev/null)

echo "✅ Archivos procesados: $FILE_COUNT"
echo "✅ Texto combinado guardado: $(basename "$TEMP_FILE")"
echo "📊 Líneas: $(wc -l < "$TEMP_FILE" 2>/dev/null || echo "0")"

# 4. Analizar el texto combinado
echo ""
echo "🔍 ANALIZANDO CONTENIDO..."

if [ -f "$TEMP_FILE" ] && [ $(wc -l < "$TEMP_FILE" 2>/dev/null || echo "0") -gt 10 ]; then
    if command -v analizar &> /dev/null; then
        analizar "$TEMP_FILE"
    else
        python3 ~/proyectos/nlp/analisis_completo_v6.4.py "$TEMP_FILE"
    fi
else
    echo "❌ El archivo combinado está vacío o no tiene contenido suficiente."
    echo "💡 El repositorio puede no tener archivos de texto relevantes."
    exit 1
fi

echo ""
echo "✅ Análisis completado"
echo "📁 Workdir: $WORK_DIR"
echo "🔗 Latest: $LATEST_LINK"
echo ""
echo "📄 Ver el último reporte:"
echo "   cat $LATEST_LINK/texto_combinado_reporte.md"
