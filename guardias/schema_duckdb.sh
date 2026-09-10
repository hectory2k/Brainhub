#!/bin/bash
# Guardia: verifica esquema de DuckDB
# Estrategia: busca DBs candidatas y valida que al menos una tenga las tablas

echo "🗄️ Verificando esquema de DuckDB..."

# Candidatos en orden de prioridad
CANDIDATOS=()
[ -n "$BRAINHUB_DB" ] && CANDIDATOS+=("$BRAINHUB_DB")
CANDIDATOS+=("$HOME/proyectos/nlp/data/databases/analisis_consolidado.duckdb")
CANDIDATOS+=("/sdcard/Download/analisis_consolidado.duckdb")

# Buscar todas las DBs en el proyecto
while IFS= read -r db; do
    CANDIDATOS+=("$db")
done < <(find "$HOME/proyectos/nlp" -name "*.duckdb" 2>/dev/null)

TABLAS_REQUERIDAS=("terminos_raw" "progreso")

DB_VALIDA=""
for db in "${CANDIDATOS[@]}"; do
    [ -f "$db" ] || continue
    echo "   Probando: $db"
    
    ok=true
    for tabla in "${TABLAS_REQUERIDAS[@]}"; do
        if ! duckdb "$db" -c "SHOW TABLES;" 2>/dev/null | grep -q "$tabla"; then
            ok=false
            echo "      ⚠️ Falta: $tabla"
            break
        fi
    done
    
    if $ok; then
        DB_VALIDA="$db"
        echo "   ✅ DB válida encontrada"
        break
    fi
done

if [ -z "$DB_VALIDA" ]; then
    echo "❌ Ninguna DB tiene las tablas requeridas"
    echo "   Requeridas: ${TABLAS_REQUERIDAS[*]}"
    echo "   Revisar: BRAINHUB_DB o data/databases/"
    exit 1
fi

echo "✅ Esquema DuckDB OK: $DB_VALIDA"
