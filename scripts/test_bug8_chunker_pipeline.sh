#!/bin/bash
# Test de regresión para Bug #8: Verificar que el chunker está activo y segmenta correctamente.
# Criterio de fallo: Si un texto con estructura clara se devuelve como 1 solo chunk, el chunker está desconectado o roto.

echo "🧪 [Bug #8] Test de regresión: Chunker en pipeline"

TEST_DIR=~/temp/test_bug8_$(date +%s)
mkdir -p "$TEST_DIR"
INPUT_FILE="$TEST_DIR/test_input.txt"

# 1. Generar un texto realista con estructura clara (6 oraciones en total)
cat > "$INPUT_FILE" << 'EOF'
Este es el primer párrafo de prueba para el chunker. 
Debe ser lo suficientemente largo para justificar su propio bloque de análisis.

Este es el segundo párrafo de prueba, completamente independiente del anterior. 
El chunker debería detectar el salto de línea doble y separar estos bloques lógicos.

Este es el tercer párrafo de prueba. 
Si el chunker está desconectado o roto, todo este texto será un solo chunk gigante.
EOF

# 2. Ejecutar el chunker real, pasando la ruta como argumento
# NOTA: Usamos max_oraciones=2 para forzar la segmentación de las 6 oraciones de prueba en múltiples chunks.
RESULTADO=$(python3 - "$INPUT_FILE" << 'PYEOF' || true
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/proyectos/nlp')
from brainhub.chunking import Chunker

input_file = sys.argv[1]
with open(input_file, 'r', encoding='utf-8') as f:
    texto = f.read()

# Forzamos max_oraciones=2 para garantizar que las 6 oraciones de prueba se dividan en >= 3 chunks
chunker = Chunker(estrategia='oraciones', max_oraciones=2)
chunks = chunker.chunkear(texto, "test_bug8_video")

print(f"CANTIDAD:{len(chunks)}")
if len(chunks) == 1 and len(chunks[0].texto) > 200:
    print(f"ERROR_LEN:{len(chunks[0].texto)}")
    sys.exit(1)
PYEOF
)

echo "📊 Resultado del chunker: $(echo "$RESULTADO" | tr '\n' ' ')"

# 3. Validar que no haya fallado
if echo "$RESULTADO" | grep -q "ERROR_LEN"; then
    echo "❌ FALLÓ: El chunker devolvió 1 chunk gigante para un texto estructurado."
    echo "   Esto indica que el chunker está desconectado o configurado incorrectamente."
    rm -rf "$TEST_DIR"
    exit 1
fi

CANTIDAD=$(echo "$RESULTADO" | grep "CANTIDAD:" | cut -d: -f2)
if [ -z "$CANTIDAD" ] || [ "$CANTIDAD" -lt 2 ]; then
    echo "❌ FALLÓ: El chunker no generó múltiples chunks para un texto con estructura clara."
    echo "   Chunks encontrados: $CANTIDAD (esperado >= 2)"
    rm -rf "$TEST_DIR"
    exit 1
fi

# 4. Limpieza exitosa
rm -rf "$TEST_DIR"
echo "✅ [Bug #8] Test pasado: El chunker está activo y segmentó correctamente ($CANTIDAD chunks)."
echo "ℹ️  Nota: Textos sin puntuación pueden generar chunks grandes, pero son mitigados por la guardia en persistir_chunks.py"
exit 0
