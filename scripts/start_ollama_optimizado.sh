#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# start_ollama_optimizado.sh
# Arranca Ollama con configuración de bajo consumo para Termux:
#   - num_parallel=1 (una request a la vez)
#   - max_loaded_models=1 (un modelo en RAM)
#   - context_length=2048 (menos KV cache)
#   - keep_alive=0 (descarga modelo al terminar)
#   - load_timeout=10m (tolera carga lenta)
#   - no_cloud (desactiva telemetría)
#
# Uso:
#   scripts/start_ollama_optimizado.sh        # arranca
#   scripts/start_ollama_optimizado.sh stop   # para
# ============================================================

set -e

if [[ "${1:-}" == "stop" ]]; then
    echo "🛑 Parando Ollama..."
    pkill -f 'ollama serve|ollama runner' 2>/dev/null || true
    sleep 2
    echo "✅ Parado"
    exit 0
fi

# Verificar si ya está corriendo
if curl -fsS --connect-timeout 2 --max-time 5 \
    http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama ya está corriendo"
    exit 0
fi

echo "🛑 Limpiando procesos previos..."
pkill -f 'ollama serve|ollama runner' 2>/dev/null || true
sleep 2

# Configuración optimizada para Termux
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_CONTEXT_LENGTH=512
export OLLAMA_KEEP_ALIVE=0
export OLLAMA_LOAD_TIMEOUT=10m
export OLLAMA_NO_CLOUD=1

echo "🚀 Arrancando Ollama (optimizado)..."
mkdir -p "$HOME/logs"
nohup ollama serve >> "$HOME/logs/ollama.log" 2>&1 &

# Esperar que responda (con reintentos)
echo "⏳ Esperando que Ollama arranque..."
for i in $(seq 1 30); do
    if curl -fsS --connect-timeout 2 --max-time 5 \
        http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama activo (intento $i/30)"
        curl -s http://127.0.0.1:11434/api/tags | head -c 100
        echo
        exit 0
    fi
    sleep 2
done

echo "❌ Ollama no respondió tras 60s"
echo "Ver log:"
tail -20 "$HOME/logs/ollama.log"
exit 1
