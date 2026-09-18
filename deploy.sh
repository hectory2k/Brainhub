#!/bin/bash
# ============================================
# DEPLOY SEGURO - Versión idempotente
# Uso: deploy.sh "mensaje del commit" [archivo_prueba]
#
# Idempotente:
#   - Si no hay cambios: no commitea, pero pushea si hay algo pendiente
#   - Si hay cambios: hace commit + push
#   - Siempre verifica el estado final
# ============================================

MENSAJE="$1"
ARCHIVO_PRUEBA="${2:-$HOME/pensar.txt}"

if [ -z "$MENSAJE" ]; then
    echo "❌ Uso: deploy.sh 'mensaje del commit' [archivo_prueba]"
    echo "📋 Ejemplo: deploy.sh 'feat: nueva mejora' ~/pensar.txt"
    exit 1
fi

cd ~/proyectos/nlp || exit 1

echo "🚀 DEPLOY SEGURO (idempotente)"
echo "================================"

# 1. Shadow test
echo "🧪 Ejecutando shadow test..."
if [ -f "modulos/shadow_testing.py" ]; then
    RESULTADO=$(python3 modulos/shadow_testing.py "$ARCHIVO_PRUEBA" analisis_completo_v6.4.py 2>&1)
    if echo "$RESULTADO" | grep -q "REGRESIÓN"; then
        echo "❌ Regresión detectada. Abortando deploy."
        echo "$RESULTADO"
        exit 1
    fi
    echo "✅ Shadow test OK"
else
    echo "⚠️  shadow_testing.py no encontrado, saltando"
fi

# 2. Estado del working tree
CAMBIOS=$(git status --porcelain)

if [ -z "$CAMBIOS" ]; then
    echo "📭 Sin cambios para commitear"
    
    # Ver si hay commits pendientes de push
    AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
    
    if [ "$AHEAD" -gt 0 ]; then
        echo "📤 Hay $AHEAD commit(s) local(es) sin pushear"
        git push origin main || { echo "❌ Push falló"; exit 1; }
        echo "✅ Push completado"
    else
        echo "✅ Nada que hacer (working tree limpio, sin commits pendientes)"
    fi
    
    # Estado final
    echo ""
    echo "════════════════════════════════════"
    echo "📊 ESTADO FINAL"
    echo "════════════════════════════════════"
    git log --oneline -3
    echo ""
    git status -sb
    exit 0
fi

# 3. Hay cambios: commit + push
echo "📦 Cambios detectados:"
echo "$CAMBIOS" | head -10
echo ""

git add .
git commit -m "$MENSAJE" || { echo "❌ Commit falló"; exit 1; }

echo "📤 Subiendo a GitHub..."
git push origin main || { echo "❌ Push falló"; exit 1; }

# 4. Verificación final
echo ""
echo "════════════════════════════════════"
echo "📊 ESTADO FINAL"
echo "════════════════════════════════════"
git log --oneline -3
echo ""
git status -sb

echo ""
echo "✅ Deploy completado"
echo "   Commit: $MENSAJE"
echo "   Shadow test: OK"
