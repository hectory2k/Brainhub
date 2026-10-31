#!/usr/bin/env python3
"""
Alinea chunks de un video con su archivo VTT para agregar timestamps (t_inicio, t_fin).
Uso: python3 alinear_chunks_vtt.py --video <ID_VIDEO> --vtt <RUTA_VTT> [--db <RUTA_DB>]
"""
import os, re, json, subprocess, unicodedata, argparse
from pathlib import Path

DB_DEFAULT = os.environ.get('BRAINHUB_DB', '/sdcard/Download/analisis_consolidado.duckdb')
TS = re.compile(r"(\d+):(\d+):(\d+)\.(\d+) --> ")

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", s)

def cues(path):
    out, start, buf = [], None, []
    content = Path(path).read_text(encoding="utf-8")
    
    # 🧠 AUTO-DETECCIÓN Y CONVERSIÓN (Hace el sistema intuitivo a SRT)
    if not content.strip().startswith("WEBVTT"):
        content = "WEBVTT\n\n" + content.strip()
    # Convierte comas a puntos en los timestamps (SRT -> VTT)
    content = re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2 --> \3.\4', content)
    
    for line in content.splitlines() + [""]:
        m = TS.match(line)
        if m:
            h, mi, s, ms = map(int, m.groups())
            start, buf = h * 3600 + mi * 60 + s + ms / 1000, []
        elif line.strip() == "" and start is not None:
            out.append((start, " ".join(buf)))
            start, buf = None, []
        elif start is not None:
            buf.append(re.sub(r"<[^>]+>", "", line))
    return out

def main():
    p = argparse.ArgumentParser(description="Alinea chunks con VTT para agregar timestamps")
    p.add_argument('--video', required=True, help="ID del video en la DB (ej: Transcript_XXX_ES)")
    p.add_argument('--vtt', required=True, help="Ruta al archivo .vtt")
    p.add_argument('--db', default=DB_DEFAULT, help="Ruta a la DuckDB")
    args = p.parse_args()

    if not Path(args.vtt).exists():
        print(f"❌ VTT no encontrado: {args.vtt}")
        return

    print(f"🔗 Alineando: {args.video} con {Path(args.vtt).name}")
    
    # 1. Asegurar schema (agregar columnas si no existen)
    sql_schema = """
    ALTER TABLE chunks ADD COLUMN IF NOT EXISTS t_inicio REAL;
    ALTER TABLE chunks ADD COLUMN IF NOT EXISTS t_fin REAL;
    """
    subprocess.run(['duckdb', args.db, '-c', sql_schema], capture_output=True)

    # 2. Obtener chunks del video
    video_safe = args.video.replace("'", "''")
    sql_select = f"SELECT chunk_id, posicion, texto FROM chunks WHERE video='{video_safe}' ORDER BY posicion"
    res = subprocess.run(['duckdb', args.db, '-readonly', '-json', '-c', sql_select], capture_output=True, text=True)
    try:
        filas = json.loads(res.stdout)
    except Exception as e:
        print(f"❌ Error leyendo chunks de la DB: {e}")
        return

    if not filas:
        print("⚠️ No se encontraron chunks para este video en la DB.")
        return

    # 3. Parsear VTT
    vtt_data = cues(args.vtt)
    pal, tiempo = [], []
    for st, tx in vtt_data:
        for w in norm(tx):
            pal.append(w)
            tiempo.append(st)

    # 4. Alinear (Heurística de 6 palabras, O(N))
    k, hits, updates = 0, 0, []
    for fila in filas:
        a = norm(fila["texto"])[:6]
        if len(a) < 6:
            updates.append((None, None, fila["chunk_id"]))
            continue
        
        matched = False
        for i in range(k, len(pal) - 5):
            if pal[i:i + 6] == a:
                hits += 1
                k = i
                t_inicio = tiempo[i]
                t_fin = tiempo[i+5] if (i+5) < len(tiempo) else t_inicio + 2.0
                updates.append((t_inicio, t_fin, fila["chunk_id"]))
                matched = True
                break
        
        if not matched:
            updates.append((None, None, fila["chunk_id"]))

    # 5. Ejecutar updates en batch
    print(f"📊 Encontrados {hits}/{len(filas)} chunks anclados. Actualizando DB...")
    sql_updates = []
    for t_inicio, t_fin, chunk_id in updates:
        cid_safe = chunk_id.replace("'", "''")
        if t_inicio is not None:
            sql_updates.append(f"UPDATE chunks SET t_inicio = {t_inicio}, t_fin = {t_fin} WHERE chunk_id = '{cid_safe}';")
        else:
            sql_updates.append(f"UPDATE chunks SET t_inicio = NULL, t_fin = NULL WHERE chunk_id = '{cid_safe}';")
    
    if sql_updates:
        batch_sql = "\n".join(sql_updates)
        res_up = subprocess.run(['duckdb', args.db, '-c', batch_sql], capture_output=True, text=True)
        if res_up.returncode != 0:
            print(f"❌ Error actualizando DB: {res_up.stderr}")
        else:
            print(f"✅ Completado. {hits} chunks con timestamp, {len(filas)-hits} sin ancla (NULL).")

if __name__ == '__main__':
    main()
