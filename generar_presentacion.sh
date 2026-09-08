#!/bin/bash
# Genera presentación para clase desde análisis BrainHub

if [ -z "$1" ]; then
    echo "❌ Uso: generar_presentacion.sh archivo_analisis.json"
    exit 1
fi

python3 << PYEOF
import json
import sys

with open('$1', 'r') as f:
    datos = json.load(f)

terminos = datos.get('terminos_clave', [])
coocurrencias = datos.get('coocurrencias', [])
nicho = datos.get('nicho', 'GENERAL')

print("# 📚 Presentación - Paper")
print("=" * 60)
print()

# 1. Título y contexto
print("## 🎯 Idea Central")
print(f"El paper analiza **{terminos[0][0] if terminos else 'el tema'}** en el contexto de {nicho}.")
print()

# 2. Puntos clave (top 3 co-ocurrencias)
print("## 🔑 Puntos Clave")
for i, co in enumerate(coocurrencias[:3], 1):
    if isinstance(co, list) and len(co) >= 2:
        par, freq = co
        print(f"{i}. **{par[0]}** + **{par[1]}** → {freq} menciones")
print()

# 3. Términos principales
print("## 📊 Términos Dominantes")
for t, f in terminos[:5]:
    print(f"- {t}: {f}")
print()

# 4. Preguntas para discusión
print("## 💬 Preguntas para Debate")
print("1. ¿Qué mecanismos explican la relación entre los conceptos clave?")
print("2. ¿Qué implicaciones prácticas tiene para el uso de IA?")
print("3. ¿Qué limitaciones presenta el estudio?")
print()

# 5. Cierre
print("## ✅ Conclusión")
print(f"BrainHub detectó {len(terminos)} términos clave y {len(coocurrencias)} relaciones.")
print("Documento generado automáticamente en segundos.")
PYEOF
