#!/bin/bash
# Flujo completo para papers científicos PDF
# Uso: procesar_paper.sh archivo.pdf

if [ -z "$1" ]; then
    echo "❌ Uso: procesar_paper.sh archivo.pdf"
    exit 1
fi

PDF="$1"
BASE=$(basename "$PDF" .pdf)

echo "📄 Procesando paper: $BASE"
echo "=" * 40

# 1. Convertir PDF a texto con layout
echo "📝 Convirtiendo PDF..."
pdftotext -layout "$PDF" "${BASE}_salida.txt"

# 2. Descolumnar (si es PDF de 2 columnas)
echo "🔧 Descolumnando..."
python3 ~/proyectos/nlp/descolumnar.py "${BASE}_salida.txt"

# 3. Analizar con BrainHub
echo "🧠 Analizando..."
analizar "${BASE}_salida_continuo.txt"

# 4. Generar documento 80/20
echo "📚 Generando documento..."
~/proyectos/nlp/documento_8020.sh "${BASE}_salida_continuo_analisis_completo.json"

echo "✅ Paper procesado completo"
