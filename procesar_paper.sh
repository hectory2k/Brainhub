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
echo "========================================"

# 1. Convertir PDF a texto con layout
echo "📝 Convirtiendo PDF..."
pdftotext -layout "$PDF" "${BASE}_salida.txt"

# 2. Descolumnar (con auto-deteccion)
echo "🔧 Intentando descolumnar..."
RESULTADO=$(python3 ~/proyectos/nlp/descolumnar.py "${BASE}_salida.txt" 2>&1)
echo "$RESULTADO"

if echo "$RESULTADO" | grep -q "GUARDIA.*FALLÓ"; then
    echo "⚠️  Descolumnado falló (PDF de 1 columna?), usando texto original"
    cp "${BASE}_salida.txt" "${BASE}_salida_continuo.txt"
else
    echo "✅ Descolumnado OK"
fi

# 3. Analizar con BrainHub
echo "🧠 Analizando..."
python3 ~/proyectos/nlp/analisis_completo_v6.5.py "${BASE}_salida_continuo.txt"

# 4. Generar documento 80/20
echo "📚 Generando documento..."
~/proyectos/nlp/documento_8020.sh "${BASE}_salida_continuo_analisis_completo.json"

echo "✅ Paper procesado completo"
