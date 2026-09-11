#!/bin/bash
# Guardia: verifica que el validador federado esté operativo
# Previene que se sobreescriba accidentalmente (bug del 2026-09-11)

echo "🔍 Verificando validador federado..."

python3 -c "
from modulos.validador_preguntas import (
    ValidadorPreguntas,
    FuenteTerminos,
    get_validador,
)

# 1. Clase instanciable
v = ValidadorPreguntas()

# 2. Métodos críticos
for metodo in ['es_generico', 'es_tecnico', 'validar_conceptos', 'filtrar_terminos', 'stats', 'lematizar']:
    if not hasattr(v, metodo):
        print(f'❌ Falta método: {metodo}')
        exit(1)

# 3. Federación activa
stats = v.stats()
if stats['genericos'].get('terminos_vacios', 0) == 0:
    print('❌ Fuente terminos_vacios vacía')
    exit(1)
if stats['tecnicos'].get('nichos', 0) == 0:
    print('❌ Fuente nichos vacía')
    exit(1)

# 4. Funcionalidad básica
assert v.es_generico('word') == True, 'word debe ser genérico'
assert v.es_generico('transformer') == False, 'transformer NO debe ser genérico'
assert v.es_tecnico('transformer') == True, 'transformer debe ser técnico'

# 5. Lematización
assert v.lematizar('deudores') in ('deuda', 'deudor'), 'lematización de deudores falla'
assert v.lematizar('años') == 'año', 'lematización de años falla'

n_gen = sum(stats['genericos'].values())
n_tec = sum(stats['tecnicos'].values())
print(f'✅ Validador OK: {n_gen} genéricos, {n_tec} técnicos')
" || exit 1
