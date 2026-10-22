#!/data/data/com.termux/files/usr/bin/python3
"""
Persiste chunks desde JSONs de análisis a DuckDB.
Uso: python persistir_chunks.py [--db PATH] [--dir PATH] [--patron PATTERN]
"""
import json
import os
import sys
import subprocess
import argparse
from pathlib import Path

DB_DEFAULT = os.environ.get('BRAINHUB_DB', '/sdcard/Download/analisis_consolidado.duckdb')
DIR_DEFAULT = "/sdcard/Download"
PATRON_DEFAULT = "Transcript_*_analisis_completo.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    video TEXT,
    posicion INTEGER,
    texto TEXT,
    start_char INTEGER,
    end_char INTEGER,
    n_oraciones INTEGER,
    estrategia TEXT,
    tier TEXT,
    metadata JSON,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chunks_video ON chunks(video);
CREATE INDEX IF NOT EXISTS idx_chunks_tier ON chunks(tier);
CREATE INDEX IF NOT EXISTS idx_chunks_posicion ON chunks(video, posicion);
"""


def _escape(valor):
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, dict):
        valor = json.dumps(valor, ensure_ascii=False)
    return "'" + str(valor).replace("'", "''") + "'"


def crear_tabla(db_path):
    result = subprocess.run(
        ['duckdb', db_path, '-c', SCHEMA],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Error creando tabla: {result.stderr}")
        return False
    return True


def insertar(chunks, db_path, lote=50):
    """Inserta chunks en lotes para evitar 'Argument list too long'."""
    if not chunks:
        return 0
    total = 0
    for i in range(0, len(chunks), lote):
        sublote = chunks[i:i+lote]
        valores = []
        for c in sublote:
            valores.append(
                f"({_escape(c.get('chunk_id'))}, "
                f"{_escape(c.get('video'))}, "
                f"{_escape(c.get('posicion'))}, "
                f"{_escape(c.get('texto'))}, "
                f"{_escape(c.get('start_char'))}, "
                f"{_escape(c.get('end_char'))}, "
                f"{_escape(c.get('n_oraciones'))}, "
                f"{_escape(c.get('estrategia'))}, "
                f"{_escape(c.get('tier'))}, "
                f"{_escape(c.get('metadata', {}))})"
            )
        sql = (
            "INSERT OR IGNORE INTO chunks "
            "(chunk_id, video, posicion, texto, start_char, end_char, "
            "n_oraciones, estrategia, tier, metadata) VALUES "
            + ",\n".join(valores) + ";"
        )
        result = subprocess.run(
            ['duckdb', db_path, '-c', sql],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ❌ Error lote {i//lote}: {result.stderr[:200]}")
            continue
        total += len(sublote)
    return total


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default=DB_DEFAULT)
    p.add_argument('--dir', default=DIR_DEFAULT)
    p.add_argument('--patron', default=PATRON_DEFAULT)
    args = p.parse_args()

    print("════════════════════════════════════════════════════════════")
    print("📦 PERSISTIR CHUNKS EN DUCKDB")
    print("════════════════════════════════════════════════════════════")

    print(f"▶️  Creando tabla chunks en {args.db}...")
    if not crear_tabla(args.db):
        sys.exit(1)

    print(f"▶️  Buscando JSONs con patrón {args.patron} en {args.dir}...")
    archivos = sorted(Path(args.dir).glob(args.patron))
    if not archivos:
        print(f"  ⚠️  No hay JSONs con patrón {args.patron}")
        sys.exit(0)

    total = 0
    for f in archivos:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            chunks = data.get('chunks', [])
            if chunks:
                n = insertar(chunks, args.db)
                total += n
                print(f"  → {f.name}: {n} chunks")
            else:
                print(f"  → {f.name}: sin chunks")
        except Exception as e:
            print(f"  ❌ {f.name}: {e}")

    print(f"\n✅ Total: {total} chunks persistidos en {args.db}")


if __name__ == '__main__':
    main()
