#!/bin/bash
# Guardia: verifica que descolumnar.py funcione correctamente
# Crea un archivo de prueba de 2 columnas y valida que el output sea coherente

echo "📐 Verificando descolumnado..."

python3 -c "
import sys
sys.path.insert(0, '.')
from descolumnar import procesar_columnas
import tempfile
import os

# Crear archivo de prueba con 2 columnas realistas
lineas = []
for i in range(50):
    izq = f'Linea izquierda numero {i:03d} con contenido'
    der = f'Linea derecha numero {i:03d} con contenido'
    # Pad izquierda a 48 chars
    lineas.append(izq.ljust(48) + der)

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('\n'.join(lineas))
    tmp_in = f.name

tmp_out = tmp_in.replace('.txt', '_out.txt')

try:
    resultado = procesar_columnas(tmp_in, tmp_out)
    valido, razon = resultado.es_valido()
    
    if not valido:
        print(f'🚨 GUARDIA DESCOLUMNADO FALLÓ: {razon}')
        sys.exit(1)
    
    # Verificar que el output tiene 2 secciones
    with open(tmp_out) as f:
        contenido = f.read()
    
    if '=== COLUMNA IZQUIERDA ===' not in contenido:
        print('🚨 Falta sección izquierda en output')
        sys.exit(1)
    if '=== COLUMNA DERECHA ===' not in contenido:
        print('🚨 Falta sección derecha en output')
        sys.exit(1)
    
    print(f'✅ Descolumnado OK: {resultado.lineas_izq} izq + {resultado.lineas_der} der')
finally:
    os.unlink(tmp_in)
    if os.path.exists(tmp_out):
        os.unlink(tmp_out)
" || exit 1
