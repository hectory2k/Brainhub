#!/data/data/com.termux/files/usr/bin/bash
# Invariantes del pipeline. Solo lectura. Uso: chequeo_salud.sh [DB]
DB="${1:-${BRAINHUB_DB:-/sdcard/Download/analisis_consolidado.duckdb}}"
FAIL=0
q()    { duckdb -readonly -noheader -csv "$DB" "$1" 2>&1; }
ok()   { echo "✅ $1"; }
warn() { echo "⚠️  $1"; }
bad()  { echo "❌ $1"; FAIL=1; }

[ -f "$DB" ] || { bad "DB no existe: $DB"; exit 1; }
echo "DB: $DB"

TABLAS=$(q "SELECT table_name FROM information_schema.tables WHERE table_schema='main'")
for t in analysis chunks terminos_raw; do
  echo "$TABLAS" | grep -qx "$t" && ok "tabla $t" || bad "falta tabla $t"
done
[ "$FAIL" = 1 ] && exit 1

N=$(q "SELECT count(DISTINCT c.video) FROM chunks c WHERE NOT EXISTS (SELECT 1 FROM analysis a WHERE a.filename = c.video)")
[ "$N" = "0" ] && ok "chunks ⊆ analysis" || bad "videos de chunks sin fila en analysis: $N"

N=$(q "SELECT (count(*)-count(DISTINCT chunk_id)) + count(*) FILTER (WHERE length(trim(texto))=0) FROM chunks")
[ "$N" = "0" ] && ok "chunks: ids únicos, sin textos vacíos" || bad "chunks con ids duplicados o vacíos: $N"

V=$(q "SELECT substr(video,12,11), string_agg(DISTINCT video, ' | ') FROM chunks WHERE starts_with(video,'Transcript_') GROUP BY 1 HAVING count(DISTINCT video)>1")
if [ -z "$V" ]; then ok "sin variantes de nombre por ID de YouTube"
else warn "mismo ID (11 chars) con varios nombres:"; echo "$V"; fi

if echo "$TABLAS" | grep -qx segmentos_timestamp; then
  N=$(q "SELECT count(DISTINCT c.video) FROM chunks c WHERE NOT EXISTS (SELECT 1 FROM segmentos_timestamp s WHERE s.video_id IN (c.video, substr(c.video,12,11)))")
  [ "$N" = "0" ] && ok "timestamps: todos los videos con segmentos" || warn "videos con chunks sin segmentos_timestamp: $N"
else
  warn "no existe segmentos_timestamp: las respuestas no pueden citar el minuto"
fi
exit $FAIL
