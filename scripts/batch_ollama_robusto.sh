#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# batch_ollama_robusto.sh
# Batch con chequeos de RAM + progreso persistente.
#
# A diferencia de batch_robusto.sh:
#   - Chequea RAM antes de cada video
#   - Pausa si RAM < 500 MB
#   - Reinicia Ollama si RAM < 800 MB
#   - Guarda progreso en JSON (resumible)
# ============================================================

set -u

JSONS_DIR="/sdcard/Download"
PROGRESO="$HOME/proyectos/nlp/logs/batch_progreso.json"
LOG="$HOME/proyectos/nlp/logs/batch_ollama_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$(dirname "$PROGRESO")"
mkdir -p "$(dirname "$LOG")"

# Inicializar progreso si no existe
if [ ! -f "$PROGRESO" ]; then
    echo '{"procesados":[],"errores":[]}' > "$PROGRESO"
fi

log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

get_ram_mb() {
    awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo
}

restart_ollama() {
    log "  🔄 Reiniciando Ollama..."
    pkill -f 'ollama serve|ollama runner' 2>/dev/null || true
    sleep 3
    
    export OLLAMA_HOST=127.0.0.1:11434
    export OLLAMA_NUM_PARALLEL=1
    export OLLAMA_MAX_LOADED_MODELS=1
    export OLLAMA_CONTEXT_LENGTH=512
    export OLLAMA_KEEP_ALIVE=0
    export OLLAMA_LOAD_TIMEOUT=10m
    export OLLAMA_NO_CLOUD=1
    
    nohup ollama serve >> ~/logs/ollama.log 2>&1 &
    
    for i in $(seq 1 30); do
        sleep 2
        if curl -fsS --connect-timeout 2 --max-time 5 \
            http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
            log "  ✅ Ollama relanzado tras $((i*2))s"
            return 0
        fi
    done
    log "  ❌ Ollama no revive"
    return 1
}

ya_procesado() {
    python3 -c "
import json
try:
    d = json.load(open('$1'))
    r = d.get('resumen_llm') or {}
    print(1 if r.get('modelo') == 'gemma:2b' else 0)
except: print(0)
" 2>/dev/null || echo 0
}

log "════════════════════════════════════════════════════"
log "BATCH OLLAMA ROBUSTO - $(date)"
log "RAM check + progreso persistente"
log "════════════════════════════════════════════════════"

procesados=0
saltados=0
errores=0

for txt in "$JSONS_DIR"/*.txt; do
    # Skip basura
    [[ "$txt" == *"_analisis"* ]] && continue
    [[ "$txt" == *"_resumen"* ]] && continue
    [[ "$txt" == *"_metricas"* ]] && continue
    [[ "$txt" == *"_legacy"* ]] && continue
    [[ "$txt" == *"_quarantine"* ]] && continue
    [[ "$txt" == *".motivo."* ]] && continue
    
    base=$(basename "$txt" .txt)
    json="$JSONS_DIR/${base}_analisis_completo.json"
    
    # ¿Ya tiene gemma:2b?
    if [ "$(ya_procesado "$json")" = "1" ]; then
        saltados=$((saltados + 1))
        continue
    fi
    
    # ─── Chequeo de RAM ───
    ram_mb=$(get_ram_mb)
    log ""
    log "▶️  $base"
    log "   RAM: ${ram_mb} MB disponibles"
    
    if [ "$ram_mb" -lt 500 ]; then
        log "   ❌ RAM crítica (<500 MB). Deteniendo batch."
        log "   ✅ Progreso guardado. Relanzá el script para retomar."
        break
    fi
    
    if [ "$ram_mb" -lt 800 ]; then
        log "   ⚠️  RAM baja (<800 MB). Reiniciando Ollama..."
        restart_ollama || break
    fi
    
    # ─── Procesar ───
    if bash "$HOME/proyectos/nlp/scripts/analizar.sh" "$txt" 2>&1 | grep -q "Resumen: gemma"; then
        procesados=$((procesados + 1))
        log "   ✅ OK con LLM"
    else
        errores=$((errores + 1))
        log "   ⚠️  Fallback a plantilla o error"
    fi
    
    sleep 2
done

log ""
log "════════════════════════════════════════════════════"
log "RESUMEN"
log "════════════════════════════════════════════════════"
log "Procesados con LLM:  $procesados"
log "Saltados (ya tenían): $saltados"
log "Errores:             $errores"
log ""
log "Log: $LOG"
log "✅ Batch terminado"
