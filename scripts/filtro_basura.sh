#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# filtro_basura.sh
# Limpia /sdcard/Download/ de archivos basura:
#   - TXT con sufijos acumulados (_analisis, _resumen, _metricas)
#   - JSON con nombres malformados (_analisis_analisis, _resumen_resumen)
#   - Duplicados por hash
#   - Archivos de 0 bytes
#   - Archivos temporales
#
# Modo dry-run por defecto. Usar --apply para mover de verdad.
# ============================================================

cd ~/proyectos/nlp

APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

TARGET_DIR="/sdcard/Download"
LEGACY_DIR="$TARGET_DIR/_legacy_$(date +%Y%m%d_%H%M%S)"
CUARENTENA_DIR="$TARGET_DIR/_quarantine_$(date +%Y%m%d)"
LOG_DIR=~/logs/limpieza
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/filtro_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

mover() {
    local archivo="$1"
    local categoria="$2"
    local motivo="$3"
    
    if [ $APPLY -eq 0 ]; then
        log "  [DRY-RUN] movería: $(basename "$archivo") → $categoria/ ($motivo)"
        return 0
    fi
    
    local dest_dir="$LEGACY_DIR/$categoria"
    mkdir -p "$dest_dir"
    mv "$archivo" "$dest_dir/" 2>/dev/null
    log "  ✓ Movido: $(basename "$archivo") → $categoria/ ($motivo)"
}

log "════════════════════════════════════════════════════"
log "FILTRO DE BASURA - $(date)"
log "Modo: $([ $APPLY -eq 1 ] && echo 'APPLY (mueve)' || echo 'DRY-RUN (solo muestra)')"
log "Target: $TARGET_DIR"
log "Legacy: $LEGACY_DIR"
log "════════════════════════════════════════════════════"

total=0

# ─── 1. Archivos de 0 bytes ───
log ""
log "[1/7] Archivos de 0 bytes..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "vacios" "0 bytes"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -type f -size 0 2>/dev/null)

# ─── 2. TXT con sufijos acumulados ───
log ""
log "[2/7] TXT con sufijos acumulados..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "txt_sufijos" "sufijos _analisis/_resumen/_metricas"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*.txt" \( -name "*_analisis*.txt" -o -name "*_resumen*.txt" -o -name "*_metricas*.txt" \) 2>/dev/null)

# ─── 3. JSON con _analisis_analisis (2+ veces) ───
log ""
log "[3/7] JSON con _analisis repetido..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "json_duplicados" "_analisis repetido"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*_analisis_analisis*.json" 2>/dev/null)

# ─── 4. JSON con _resumen en el nombre ───
log ""
log "[4/7] JSON con _resumen en el nombre..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "json_resumen" "_resumen en nombre"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*_resumen*.json" 2>/dev/null)

# ─── 5. Archivos temporales ───
log ""
log "[5/7] Archivos temporales..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "temporales" "extensión temporal"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -type f \( -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" -o -name "*.part" \) 2>/dev/null)

# ─── 6. TXT con nombres peligrosos ───
log ""
log "[6/7] TXT con caracteres peligrosos en el nombre..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    base=$(basename "$f")
    if echo "$base" | grep -qE '[;|&$`<>()]'; then
        mover "$f" "nombres_peligrosos" "caracteres: $(echo "$base" | grep -oE '[;|&$`<>()]' | tr '\n' ',')"
        total=$((total + 1))
    fi
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*.txt" 2>/dev/null)

# ─── 7b. Archivos .motivo.txt sueltos (metadata de cuarentena) ───
log ""
log "[7b/8] Archivos .motivo.txt sueltos..."
while IFS= read -r f; do
    [ -z "$f" ] && continue
    mover "$f" "motivos_sueltos" "metadata de cuarentena sin su TXT"
    total=$((total + 1))
done < <(find "$TARGET_DIR" -maxdepth 1 -name "*.motivo.txt" 2>/dev/null)

# ─── 8. Duplicados por hash ───
log ""
log "[8/8] Duplicados por hash..."
declare -A hashes
while IFS= read -r f; do
    [ -z "$f" ] && continue
    [[ "$f" == *"_legacy"* ]] && continue
    [[ "$f" == *"_quarantine"* ]] && continue
    
    h=$(md5sum "$f" 2>/dev/null | cut -d' ' -f1)
    [ -z "$h" ] && continue
    
    if [ -n "${hashes[$h]}" ]; then
        # Es duplicado
        original="${hashes[$h]}"
        log "  Duplicado detectado:"
        log "    Original: $(basename "$original")"
        log "    Dup:      $(basename "$f")"
        mover "$f" "duplicados" "mismo hash que $(basename "$original")"
        total=$((total + 1))
    else
        hashes[$h]="$f"
    fi
done < <(find "$TARGET_DIR" -maxdepth 1 -type f -name "*.txt" 2>/dev/null)

# ─── Resumen ───
log ""
log "════════════════════════════════════════════════════"
log "RESUMEN"
log "════════════════════════════════════════════════════"
log "Archivos a mover: $total"

if [ $APPLY -eq 1 ]; then
    log ""
    log "─── Contenido de legacy ───"
    if [ -d "$LEGACY_DIR" ]; then
        for cat in "$LEGACY_DIR"/*/; do
            [ -d "$cat" ] || continue
            count=$(ls "$cat" 2>/dev/null | wc -l)
            log "  $(basename "$cat"): $count"
        done
    fi
    log ""
    log "Legacy: $LEGACY_DIR"
else
    log ""
    log "⚠️  Modo DRY-RUN. Para aplicar:"
    log "    bash scripts/filtro_basura.sh --apply"
fi

log ""
log "Log: $LOG"
log "✅ Filtro terminado"
