#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# batch_robusto.sh
# Batch de análisis con:
#   - Reintentos automáticos (3 por video)
#   - Logging detallado de cada intento y su causa de fallo
#   - Auto-relanzar Ollama si muere
#   - Cuarentena automática de TXT problemáticos
#   - Resumen final con motivos agregados
# ============================================================

cd ~/proyectos/nlp

QUARANTINE_DIR="/sdcard/Download/_quarantine_$(date +%Y%m%d)"
LOG_DIR=~/logs/batch
mkdir -p "$LOG_DIR" "$QUARANTINE_DIR"
mkdir -p "$QUARANTINE_DIR/corruptos"
mkdir -p "$QUARANTINE_DIR/encoding"
mkdir -p "$QUARANTINE_DIR/muy_cortos"
mkdir -p "$QUARANTINE_DIR/sin_json"
mkdir -p "$QUARANTINE_DIR/errores"

LOG="$LOG_DIR/batch_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="$LOG_DIR/errores_$(date +%Y%m%d_%H%M%S).log"

# ─── Helpers ───
log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

log_err() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG" "$ERROR_LOG"
}

# Mover a cuarentena con metadata
mover_a_cuarentena() {
    local txt="$1"
    local categoria="$2"  # corruptos|encoding|muy_cortos|sin_json|errores
    local motivo="$3"
    local detalle="${4:-}"
    
    local base=$(basename "$txt")
    local dest_dir="$QUARANTINE_DIR/$categoria"
    mkdir -p "$dest_dir"
    
    # Evitar sobrescribir
    local dest_txt="$dest_dir/$base"
    if [ -f "$dest_txt" ]; then
        dest_txt="${dest_dir}/${base%.txt}_$(date +%s).txt"
    fi
    
    # Mover el .txt
    mv "$txt" "$dest_txt" 2>/dev/null
    
    # Mover también el JSON si existe
    local base_no_ext="${base%.txt}"
    local json_src="/sdcard/Download/${base_no_ext}_analisis_completo.json"
    if [ -f "$json_src" ]; then
        mv "$json_src" "$dest_dir/" 2>/dev/null
    fi
    
    # Crear archivo de metadata
    local motivo_file="${dest_txt%.txt}.motivo.txt"
    cat > "$motivo_file" << MOTIVO_EOF
# Cuarentena de TXT
Fecha:         $(date)
Archivo:       $base
Categoría:     $categoria
Motivo:        $motivo
Detalle:       $detalle

# Metadata original
Tamaño:        $(wc -c < "$dest_txt" 2>/dev/null || echo "?") bytes
Líneas:        $(wc -l < "$dest_txt" 2>/dev/null || echo "?")
Hash MD5:      $(md5sum "$dest_txt" 2>/dev/null | cut -d' ' -f1 || echo "?")

# Primeras 3 líneas del TXT
$(head -3 "$dest_txt" 2>/dev/null || echo "  (no se pudo leer)")

# Para re-procesar manualmente:
#   1. Revisar si el TXT es recuperable (con: cat "$dest_txt")
#   2. Corregir el problema (encoding, formato, etc)
#   3. Mover de vuelta a /sdcard/Download/
#   4. Re-ejecutar: bash scripts/analizar.sh "$dest_txt"
MOTIVO_EOF
    
    log_err "  → Movido a cuarentena: $categoria/$(basename "$dest_txt")"
}

# Validar el TXT antes de procesar
validar_txt() {
    local txt="$1"
    local base=$(basename "$txt" .txt)
    
    # 1. ¿Existe?
    if [ ! -f "$txt" ]; then
        echo "NO_EXISTE"
        return 1
    fi
    
    # 2. ¿Es muy corto?
    local size=$(wc -c < "$txt" 2>/dev/null || echo 0)
    if [ "$size" -lt 200 ]; then
        echo "MUY_CORTO:${size}b"
        return 2
    fi
    
    # 3. ¿Encoding válido?
    if ! file -b "$txt" 2>/dev/null | grep -qiE "text|ascii|utf"; then
        echo "ENCODING_INVALIDO:$(file -b "$txt" 2>/dev/null)"
        return 3
    fi
    
    # 4. ¿Es binario? (usar file, no grep)
    if file -b "$txt" 2>/dev/null | grep -qiE "^data|binary"; then
        echo "BINARIO:$(file -b "$txt" 2>/dev/null | head -c 50)"
        return 4
    fi
    
    # 5. ¿Nombre raro con caracteres peligrosos?
    if echo "$base" | grep -qE '[;|&$`<>()\\]'; then
        echo "NOMBRE_RARO:caracteres peligrosos"
        return 5
    fi
    
    # 6. ¿Tiene extensión .txt pero no termina en .txt?
    # (por si alguien renombra algo raro)
    if [[ ! "$txt" == *.txt ]]; then
        echo "EXTENSION_RARA"
        return 6
    fi
    
    return 0  # OK
}

# Clasificar error de análisis (post-ejecución)
clasificar_error() {
    local salida="$1"
    local txt="$2"
    local base="$3"
    local json="/sdcard/Download/${base}_analisis_completo.json"
    
    if echo "$salida" | grep -qi "MemoryError\|OOM\|Cannot allocate"; then
        echo "OOM:memoria insuficiente"
    elif echo "$salida" | grep -qi "timeout\|timed out"; then
        echo "TIMEOUT:tardó más de lo esperado"
    elif echo "$salida" | grep -qi "unicode\|decode"; then
        echo "ENCODING:problema de encoding"
    elif echo "$salida" | grep -qi "connection refused\|ollama no disponible"; then
        echo "OLLAMA_DOWN:Ollama no respondió"
    elif echo "$salida" | grep -qi "KeyboardInterrupt"; then
        echo "INTERRUMPIDO:usuario canceló"
    elif [ ! -f "$json" ]; then
        echo "JSON_NO_GENERADO:el script no produjo $json"
    elif echo "$salida" | grep -qi "Traceback"; then
        local tb=$(echo "$salida" | grep -A 2 "Traceback" | head -3 | tr '\n' ' ')
        echo "TRACEBACK:$tb"
    elif echo "$salida" | grep -qi "IndexError"; then
        echo "INDEX_ERROR:estructura inesperada"
    elif echo "$salida" | grep -qi "KeyError"; then
        echo "KEY_ERROR:clave faltante en datos"
    else
        echo "DESCONOCIDO:sin firma de error reconocible"
    fi
}

# Procesar un video con reintentos + logging
procesar_video() {
    local txt="$1"
    local base="$2"
    local json="/sdcard/Download/${base}_analisis_completo.json"
    local max_intentos=3
    local intento=1
    
    while [ $intento -le $max_intentos ]; do
        log "  → Intento $intento/$max_intentos"
        
        local t0=$(date +%s)
        local salida
        salida=$(bash scripts/analizar.sh "$txt" 2>&1)
        local exit_code=$?
        local t1=$(date +%s)
        local duracion=$((t1 - t0))
        
        log "    exit_code=$exit_code, duración=${duracion}s"
        
        # ¿Terminó bien?
        if [ $exit_code -eq 0 ] && echo "$salida" | grep -q "Análisis completo finalizado"; then
            local modelo=$(python3 -c "
import json
try:
    d = json.load(open('$json'))
    r = d.get('resumen_llm') or {}
    print(r.get('modelo', 'sin'))
except: print('error')
" 2>/dev/null)
            
            case "$modelo" in
                gemma:2b) log "  ✅ OK con LLM"; return 0 ;;
                plantilla) log "  ⚠️  OK con plantilla"; return 1 ;;
                *) log "  ⚠️  OK sin resumen"; return 3 ;;
            esac
        fi
        
        # Falló: clasificar
        local causa=$(clasificar_error "$salida" "$txt" "$base")
        local tipo="${causa%%:*}"
        local detalle="${causa#*:}"
        
        log_err "  ❌ Intento $intento falló: $causa"
        echo "$salida" | tail -20 >> "$ERROR_LOG"
        echo "─────" >> "$ERROR_LOG"
        
        # Si es error no recuperable, no reintentar
        case "$tipo" in
            ENCODING|JSON_NO_GENERADO|INDEX_ERROR|KEY_ERROR)
                log_err "  ⛔ Error no recuperable, moviendo a cuarentena"
                mover_a_cuarentena "$txt" "corruptos" "$tipo" "$detalle"
                return 2
                ;;
        esac
        
        # Errores recuperables: esperar
        case "$tipo" in
            OLLAMA_DOWN) sleep 10 ;;
            OOM) sleep 15 ;;
            TIMEOUT) sleep 5 ;;
            *) sleep 5 ;;
        esac
        
        intento=$((intento + 1))
    done
    
    # Falló tras N intentos → cuarentena
    log_err "  ❌ FALLÓ tras $max_intentos intentos"
    mover_a_cuarentena "$txt" "errores" "FALLO_TRAS_${max_intentos}_INTENTOS" "ver log"
    return 2
}

# Asegurar Ollama vivo
asegurar_ollama() {
    if curl -s -m 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
        return 0
    fi
    
    log_err "⚠️  Ollama no responde. Relanzando..."
    nohup ollama serve > ~/ollama.log 2>&1 &
    sleep 10
    
    if curl -s -m 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
        log "✅ Ollama revivió"
        return 0
    fi
    
    log_err "❌ Ollama no revive tras 10s. Abortando batch."
    return 1
}

# ─── Inicio ───
log "════════════════════════════════════════════════════"
log "BATCH ROBUSTO CON CUARENTENA - $(date)"
log "Log:           $LOG"
log "Errores:       $ERROR_LOG"
log "Cuarentena:    $QUARANTINE_DIR"
log "════════════════════════════════════════════════════"

total=0
ok=0
fallback=0
sin_resumen=0
fallidos=0
cuarentena=0

for txt in /sdcard/Download/*.txt; do
    # Skip basura obvia
    [[ "$txt" == *"_analisis"* ]] && continue
    [[ "$txt" == *"_resumen"* ]] && continue
    [[ "$txt" == *"_metricas"* ]] && continue
    [[ "$txt" == *"_quarantine"* ]] && continue
    [[ "$txt" == *"_legacy"* ]] && continue
    
    base=$(basename "$txt" .txt)
    json="/sdcard/Download/${base}_analisis_completo.json"
    
    # ─── Validación previa ───
    log ""
    log "[$((total + 1))] Validando: $base"
    
    validacion=$(validar_txt "$txt")
    val_result=$?
    
    if [ $val_result -ne 0 ]; then
        motivo="${validacion%%:*}"
        detalle="${validacion#*:}"
        log_err "  ❌ Validación falló: $motivo"
        
        # Mover a cuarentena según el tipo
        case "$motivo" in
            NO_EXISTE)
                # No hay nada que mover
                continue
                ;;
            MUY_CORTO)
                mover_a_cuarentena "$txt" "muy_cortos" "$motivo" "$detalle"
                cuarentena=$((cuarentena + 1))
                continue
                ;;
            ENCODING_INVALIDO|BINARIO)
                mover_a_cuarentena "$txt" "encoding" "$motivo" "$detalle"
                cuarentena=$((cuarentena + 1))
                continue
                ;;
            NOMBRE_RARO|EXTENSION_RARA)
                mover_a_cuarentena "$txt" "corruptos" "$motivo" "$detalle"
                cuarentena=$((cuarentena + 1))
                continue
                ;;
        esac
    fi
    
    log "  ✅ Validación OK"
    
    # ¿Ya tiene gemma:2b?
    tiene=$(python3 -c "
import json
try:
    d = json.load(open('$json'))
    r = d.get('resumen_llm')
    print(1 if r and r.get('modelo') == 'gemma:2b' else 0)
except: print(0)
" 2>/dev/null || echo 0)
    if [ "$tiene" = "1" ]; then
        log "⏭️  SKIP $base (ya tiene gemma:2b)"
        continue
    fi
    
    total=$((total + 1))
    log "▶️  Procesando: $base"
    
    # Asegurar Ollama
    if ! asegurar_ollama; then
        log_err "❌ Abortando batch por Ollama irrecuperable"
        break
    fi
    
    # Procesar
    procesar_video "$txt" "$base"
    result=$?
    
    case $result in
        0) ok=$((ok + 1));;
        1) fallback=$((fallback + 1));;
        2) fallidos=$((fallidos + 1));;
        3) sin_resumen=$((sin_resumen + 1));;
    esac
    
    sleep 2
done

# ─── Resumen final ───
log ""
log "════════════════════════════════════════════════════"
log "RESUMEN FINAL - $(date)"
log "════════════════════════════════════════════════════"
log "Total procesados:      $total"
log "OK con LLM:            $ok"
log "Fallback plantilla:    $fallback"
log "Sin resumen:           $sin_resumen"
log "Fallidos:              $fallidos"
log "En cuarentena:         $cuarentena"
log ""
log "Log completo:          $LOG"
log "Errores:               $ERROR_LOG"
log "Cuarentena:            $QUARANTINE_DIR"

# ─── Análisis de errores ───
if [ $fallidos -gt 0 ] || [ $fallback -gt 0 ] || [ $cuarentena -gt 0 ]; then
    log ""
    log "─── Motivos de fallos ───"
    grep -oE "(TXT_NO_EXISTE|OOM|TIMEOUT|ENCODING|OLLAMA_DOWN|INTERRUMPIDO|JSON_NO_GENERADO|TRACEBACK|INDEX_ERROR|KEY_ERROR|DESCONOCIDO|MUY_CORTO|BINARIO|NOMBRE_RARO|FALLO_TRAS)" "$ERROR_LOG" 2>/dev/null \
        | sort | uniq -c | sort -rn \
        | while read count motivo; do
            log "  $motivo: $count"
        done
    
    log ""
    log "─── Contenido de cuarentena ───"
    for cat in corruptos encoding muy_cortos sin_json errores; do
        count=$(ls "$QUARANTINE_DIR/$cat" 2>/dev/null | grep -c "\.txt$" || echo 0)
        if [ "$count" -gt 0 ]; then
            log "  $cat: $count archivos"
        fi
    done
fi

log ""
log "✅ Batch terminado"
log "📂 Revisar cuarentena: ls -la $QUARANTINE_DIR"
