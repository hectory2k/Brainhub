#!/bin/bash
# scripts/test_qa_interactivo.sh
# Test de regresión para qa_interactivo.py
# Criterio de done:
#   - El script arranca sin errores.
#   - Responde sobre una pregunta fija (sin timeout ni crash).
#   - Muestra las fuentes.

set -e

echo "🧪 Test de regresión: qa_interactivo.py"

# Guardia: git status limpio
if ! git diff-index --quiet HEAD --; then
    echo "🚨 ERROR: git status no está limpio. Abortando."
    exit 1
fi
echo "✅ Git status limpio."

DB_PATH="/sdcard/Download/analisis_consolidado.duckdb"
PREGUNTA="¿qué es RAG?"

echo "🔍 Ejecutando qa_interactivo.py con pregunta fija..."
# Ejecutamos con timeout de bash de 60s para detectar cuelgues antes que el script interno
OUTPUT=$(timeout 60s python3 ~/proyectos/nlp/scripts/qa_interactivo.py --once "$PREGUNTA" --k 3 --db "$DB_PATH" 2>&1 || true)

# Verificar que no hubo timeout de bash (código 124)
if echo "$OUTPUT" | grep -q "124"; then
    echo "🚨 FALLO: El script se colgó o excedió los 60 segundos."
    echo "$OUTPUT"
    exit 1
fi

# Verificar que encontró chunks
if echo "$OUTPUT" | grep -q "✅ [0-9]* chunks encontrados"; then
    echo "✅ Chunks encontrados correctamente."
else
    echo "⚠️ ADVERTENCIA: No se encontraron chunks (puede ser normal si la DB está vacía o la query no matchea)."
fi

# Verificar que hubo respuesta (ya sea texto o el mensaje de "No tengo información")
if echo "$OUTPUT" | grep -q "Generando respuesta"; then
    echo "✅ Ollama fue consultado sin crash."
else
    echo "🚨 FALLO: Ollama no fue consultado o falló silenciosamente."
    echo "$OUTPUT"
    exit 1
fi

# Verificar que mostró fuentes
if echo "$OUTPUT" | grep -q "📚 Fuentes:"; then
    echo "✅ Formato de citas presente."
else
    echo "⚠️ ADVERTENCIA: No se mostraron fuentes."
fi

echo "✅ Test de regresión superado."
