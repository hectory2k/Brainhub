#!/bin/bash
# Guardia: verifica que la normalización preserve ñ/Ñ
# Falla si la ñ se convierte en n, o si Ñ pierde mayúscula

echo "🔤 Verificando normalización (ñ/Ñ)..."

python3 -c "
import unicodedata
import re

def normalizar_preservando_enie(texto):
    PLACEHOLDER_LOWER = 'XYZPLACEHOLDERLOWERXYZ'
    PLACEHOLDER_UPPER = 'XYZPLACEHOLDERUPPERXYZ'
    texto = texto.replace('ñ', PLACEHOLDER_LOWER).replace('Ñ', PLACEHOLDER_UPPER)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = texto.replace(PLACEHOLDER_LOWER, 'ñ').replace(PLACEHOLDER_UPPER, 'Ñ')
    return re.sub(r'\\s+', ' ', texto).strip()

casos = {
    'años': 'años',
    'niño': 'niño',
    'diseño': 'diseño',
    'señal': 'señal',
    'mañana': 'mañana',
    'español': 'español',
    'añadir': 'añadir',
    'AÑO': 'AÑO',
    'ÑANDÚ': 'ÑANDU',
    'España': 'España',
    'ESPAÑA': 'ESPAÑA',
    'NiÑo': 'NiÑo',
    'acción': 'accion',
    'café': 'cafe',
    'análisis': 'analisis',
    'física': 'fisica',
    'méxico': 'mexico',
    'ñandú': 'ñandu',
    'pequeñín': 'pequeñin',
    'compañía': 'compañia',
    'AÑO 2026': 'AÑO 2026',
    'niño/a': 'niño/a',
}

fallos = []
for entrada, esperado in casos.items():
    resultado = normalizar_preservando_enie(entrada)
    if resultado != esperado:
        fallos.append(f'  ❌ {entrada!r} → {resultado!r} (esperado {esperado!r})')

if fallos:
    print('🚨 GUARDIA DE NORMALIZACIÓN FALLÓ:')
    print('\\n'.join(fallos))
    exit(1)

print(f'✅ Normalización OK: {len(casos)} casos verificados')
" || exit 1
