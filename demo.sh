#!/bin/bash
# demo.sh - Demo de BrainHub para video tutorial

set -e

echo "════════════════════════════════════════════════════════════"
echo "  BRAINHUB - DEMO"
echo "  Ecosistema NLP para procesar contenido técnico"
echo "════════════════════════════════════════════════════════════"
echo ""
sleep 1

# ─── PASO 1: GUARDIAS ───
echo "🔍 PASO 1: Guardias (filosofía VigiSalud)"
echo "────────────────────────────────────────────────────────────"
sleep 1
bash guardias/startup_completo.sh 2>&1 | tail -3
echo ""
sleep 2

# ─── PASO 2: PROCESAR (ya descargado) ───
echo "📥 PASO 2: Transcript descargado de YouTube"
echo "────────────────────────────────────────────────────────────"
echo "Video: Kubernetes en AWS desde cero"
echo "URL:   https://youtu.be/SbFbQ-Eie-U"
echo ""

TRANSCRIPT="/sdcard/Download/Transcript_SbFbQ-Eie-U_ES.txt"

if [ -f "$TRANSCRIPT" ]; then
    echo "✅ Transcript existente: $TRANSCRIPT"
    echo "   Líneas: $(wc -l < $TRANSCRIPT)"
else
    echo "Descargando..."
    bash ~/.local/bin/procesar "https://youtu.be/SbFbQ-Eie-U" 2>&1 | tail -5
fi
echo ""
sleep 2

# ─── PASO 3: ANALIZAR ───
echo "🧠 PASO 3: Analizar con BrainHub"
echo "────────────────────────────────────────────────────────────"
sleep 1

# Limpieza completa antes del análisis (idempotencia)
echo "🧹 Limpiando análisis previo..."
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_analisis.db 2>/dev/null || true
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_analisis.csv 2>/dev/null || true
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_analisis_completo.json 2>/dev/null || true
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_resumen.txt 2>/dev/null || true
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_reporte.md 2>/dev/null || true
rm -f /sdcard/Download/Transcript_SbFbQ-Eie-U_ES_metricas.json 2>/dev/null || true
duckdb "$BRAINHUB_DB" -c "DELETE FROM terminos_raw WHERE video LIKE '%SbFbQ%';" 2>/dev/null || true
echo ""

BRAINHUB_DB=/sdcard/Download/analisis_consolidado.duckdb \
    python3 analisis_completo_v6.5.py "$TRANSCRIPT"
echo ""
sleep 3

# ─── PASO 4: VER JSON ───
echo "📊 PASO 4: Estructura del JSON generado"
echo "────────────────────────────────────────────────────────────"
sleep 1

JSON_FILE="/sdcard/Download/Transcript_SbFbQ-Eie-U_ES_analisis_completo.json"

if [ -f "$JSON_FILE" ]; then
    python3 << 'PYEOF'
import json
with open('/sdcard/Download/Transcript_SbFbQ-Eie-U_ES_analisis_completo.json') as f:
    d = json.load(f)

print(f"📄 Documento: {d.get('documento', 'N/A')}")
print(f"🎯 Nicho:     {d.get('nicho', 'N/A')}")
print(f"📊 Segmentos: {d.get('total_segmentos', 0)}")
print()
print("📌 Top 5 términos clave:")
for t in d.get('terminos_clave', [])[:5]:
    if isinstance(t, dict):
        print(f"   {t.get('termino', t)}: {t.get('frecuencia', '')}")
    elif isinstance(t, (list, tuple)):
        print(f"   {t[0]}: {t[1]}")
    else:
        print(f"   {t}")

print()
print("🔗 Top 3 co-ocurrencias:")
for c in d.get('coocurrencias', [])[:3]:
    if isinstance(c, (list, tuple)) and len(c) >= 2:
        par = c[0]
        if isinstance(par, (list, tuple)) and len(par) == 2:
            print(f"   {par[0]} + {par[1]}: {c[1]}")
PYEOF
fi
echo ""
sleep 2

# ─── PASO 5: DB ───
echo "🗄️  PASO 5: Consulta a DuckDB"
echo "────────────────────────────────────────────────────────────"
sleep 1

duckdb /sdcard/Download/analisis_consolidado.duckdb -c "
    SELECT term, SUM(frequency) as total
    FROM terminos_raw
    WHERE video LIKE '%SbFbQ%'
    GROUP BY term
    ORDER BY total DESC
    LIMIT 8;
" 2>&1 | head -15
echo ""
sleep 2

# ─── CIERRE ───
echo "════════════════════════════════════════════════════════════"
echo "  ✅ DEMO COMPLETADO"
echo ""
echo "  Repo: https://github.com/hectory2k/Brainhub"
echo "  Docs: https://github.com/hectory2k/Brainhub/blob/main/TUTORIAL.md"
echo "════════════════════════════════════════════════════════════"
