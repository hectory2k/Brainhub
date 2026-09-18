#!/bin/bash
# ==============================================
# PROCESAR - DESCARGA TRANSCRIPCIÓN
# Uso: procesar [URL|archivo|texto]
# ==============================================

ENTRADA="$1"

if [ -z "$ENTRADA" ]; then
    echo "❌ Uso: procesar [URL|archivo|texto]"
    echo ""
    echo "📋 Ejemplos:"
    echo "  procesar https://youtu.be/VIDEO_ID    # YouTube"
    echo "  procesar archivo.txt                 # Archivo local"
    echo "  procesar \"texto directo\"            # Texto directo"
    exit 1
fi

# ==============================================
# FUNCIÓN: FORZAR SUBS CON YT-DLP
# ==============================================
forzar_subs() {
    local url="$1"
    local video_id="$2"
    
    echo "🔄 Intentando con yt-dlp (fallback)..."
    
    yt-dlp \
        --write-auto-subs \
        --sub-langs es,en \
        --skip-download \
        --output "/sdcard/Download/$video_id.%(ext)s" \
        "$url" 2>&1 | grep -v "WARNING"
    
    vtt_file=$(find /sdcard/Download -maxdepth 1 -name "*$video_id*.vtt" -type f | head -1)
    
    if [ -f "$vtt_file" ]; then
        echo "✅ VTT descargado"
        output="/sdcard/Download/Transcript_${video_id}_ES_FORZADO.txt"
        
        awk '
            /^[0-9][0-9]:[0-9][0-9]:/ { next }
            /^WEBVTT/ { next }
            /^Kind:/ { next }
            /^Language:/ { next }
            /^[[:space:]]*$/ { next }
            {
                gsub(/<[^>]*>/, "")
                gsub(/^.*position:0%/, "")
                gsub(/^[[:space:]]+/, "")
                if (length > 0) print
            }
        ' "$vtt_file" | awk '!seen[$0]++' > "$output"
        
        echo "✅ Transcripción guardada: $output"

        # Guardar VTT con timestamps para grounding temporal
        vtt_timestamp="/sdcard/Download/Transcript_${video_id}_timestamps.vtt"
        cp "$vtt_file" "$vtt_timestamp"
        echo "✅ VTT con timestamps: $vtt_timestamp"
        echo "📊 Líneas: $(wc -l < $output)"
        echo ""
        echo "📋 Para analizar: analizar $output"
        return 0
    fi
    
    echo "❌ yt-dlp no encontró subtítulos"
    return 1
}

# ==============================================
# FUNCIÓN: TRANSCRIBIR CON WHISPER
# ==============================================
transcribir_con_whisper() {
    local url="$1"
    local video_id="$2"
    
    echo "🎙️ Intentando con Whisper (transcripción local)..."
    
    if ! command -v whisper &> /dev/null; then
        echo "📦 Instalando whisper..."
        pip install openai-whisper -q
    fi
    
    echo "📥 Descargando audio..."
    yt-dlp -x --audio-format mp3 "$url" -o "/sdcard/Download/$video_id.mp3" 2>/dev/null
    
    if [ ! -f "/sdcard/Download/$video_id.mp3" ]; then
        echo "❌ No se pudo descargar el audio"
        return 1
    fi
    
    echo "🎙️ Transcribiendo (puede tomar varios minutos)..."
    whisper /sdcard/Download/$video_id.mp3 \
        --model base \
        --language Spanish \
        --output_dir /sdcard/Download \
        --output_format txt 2>/dev/null
    
    if [ -f "/sdcard/Download/$video_id.txt" ]; then
        echo "✅ Transcripción guardada: /sdcard/Download/$video_id.txt"

        # Whisper genera SRT. Convertir a VTT si existe
        srt_file="/sdcard/Download/$video_id.srt"
        if [ -f "$srt_file" ]; then
            vtt_timestamp="/sdcard/Download/Transcript_${video_id}_timestamps.vtt"
            # Convertir SRT → VTT
            {
                echo "WEBVTT"
                echo ""
                cat "$srt_file" | sed 's/,/./g'
            } > "$vtt_timestamp"
            echo "✅ VTT con timestamps: $vtt_timestamp"
        fi
        echo "📋 Para analizar: analizar /sdcard/Download/$video_id.txt"
        return 0
    fi
    
    echo "❌ Whisper falló"
    return 1
}

# ==============================================
# PROCESAR YOUTUBE (SOLO DESCARGA)
# ==============================================
procesar_youtube() {
    local url="$1"
    
    echo "🎬 Procesando YouTube: $url"
    
    VIDEO_ID=$(echo "$url" | grep -oE '([a-zA-Z0-9_-]{11})' | head -1)
    
    if [ -z "$VIDEO_ID" ]; then
        echo "❌ No se pudo extraer el ID"
        return 1
    fi
    
    # 1. Intentar con ~/yt (API)
    echo "📥 Intentando con API..."
    ~/yt "$url"
    
    TXT_FILE="/sdcard/Download/Transcript_${VIDEO_ID}_ES.txt"
    
    if [ -f "$TXT_FILE" ] && [ $(wc -l < "$TXT_FILE") -gt 10 ]; then
        echo "✅ Transcripción obtenida: $TXT_FILE"
        echo "📊 Líneas: $(wc -l < $TXT_FILE)"
        echo ""
        echo "📋 Para analizar: analizar $TXT_FILE"
        echo "📋 Para consolidar: consolidar ${TXT_FILE%.txt}_analisis.db"
        return 0
    fi
    
    # 2. Fallback: yt-dlp
    if forzar_subs "$url" "$VIDEO_ID"; then
        return 0
    fi
    
    # 3. Fallback: Whisper
    if transcribir_con_whisper "$url" "$VIDEO_ID"; then
        return 0
    fi
    
    echo "❌ No se pudo obtener transcripción por ningún método"
    return 1
}

# ==============================================
# DETECTAR TIPO DE ENTRADA
# ==============================================

if [[ "$ENTRADA" == *"youtube.com"* ]] || [[ "$ENTRADA" == *"youtu.be"* ]]; then
    procesar_youtube "$ENTRADA"
    
elif [[ "$ENTRADA" == *.pdf ]]; then
    echo "📄 PDF detectado: $ENTRADA"
    procesar_paper "$ENTRADA"

elif [ -f "$ENTRADA" ]; then
    echo "📄 Archivo existente: $ENTRADA"
    echo "📋 Para analizar: analizar $ENTRADA"

else
    echo "📝 Texto directo detectado"
    mkdir -p ~/tmp
    echo "$ENTRADA" > ~/tmp/texto_directo.txt
    echo "✅ Guardado en: ~/tmp/texto_directo.txt"
    echo "📋 Para analizar: analizar ~/tmp/texto_directo.txt"
fi
