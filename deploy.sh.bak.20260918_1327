#!/bin/bash
# Deploy seguro: shadow test → commit → push

if [ -z "$1" ]; then
    echo "❌ Uso: deploy.sh 'mensaje del commit' [archivo_prueba]"
    echo "📋 Ejemplo: deploy.sh 'feat: nueva mejora' ~/pensar.txt"
    exit 1
fi

MENSAJE="$1"
ARCHIVO_PRUEBA="${2:-~/pensar.txt}"

echo "🚀 DEPLOY SEGURO"
echo "================"

# 1. Shadow test
echo "🧪 Ejecutando shadow test..."
RESULTADO=$(python3 ~/proyectos/nlp/modulos/shadow_testing.py "$ARCHIVO_PRUEBA" analisis_completo_v6.4.py 2>&1)

if echo "$RESULTADO" | grep -q "REGRESIÓN"; then
    echo "❌ Regresión detectada. Abortando deploy."
    echo "$RESULTADO"
    exit 1
fi

echo "✅ Shadow test OK"

# 2. Git add + commit + push
echo "📦 Preparando commit..."
cd ~/proyectos/nlp
git add .
git commit -m "$MENSAJE"

echo "📤 Subiendo a GitHub..."
git push origin main

echo ""
echo "✅ Deploy completado"
echo "   Commit: $MENSAJE"
echo "   Shadow test: OK"
echo "   Push: exitoso"
