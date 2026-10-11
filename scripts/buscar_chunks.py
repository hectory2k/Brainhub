#!/data/data/com.termux/files/usr/bin/python3
"""Búsqueda BM25 sobre chunks en DuckDB.

Uso:
    python buscar_chunks.py 'tu query'
    python buscar_chunks.py 'fuerza velocidad' --k 10
"""
import sys
import json
import subprocess
import argparse
from pathlib import Path

import bm25s

DB_DEFAULT = "/sdcard/Download/analisis_consolidado.duckdb"


def cargar_chunks(db_path):
    r = subprocess.run(
        ['duckdb', db_path, '-json', '-c',
         "SELECT chunk_id, video, posicion, texto FROM chunks;"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"❌ Error DuckDB: {r.stderr}")
        sys.exit(1)
    if not r.stdout.strip():
        return []
    return json.loads(r.stdout)


def main():
    p = argparse.ArgumentParser(description="Búsqueda BM25 sobre chunks")
    p.add_argument('query', nargs='+', help="Términos de búsqueda")
    p.add_argument('--k', type=int, default=5, help="Cantidad de resultados")
    p.add_argument('--db', default=DB_DEFAULT, help="Path a DuckDB")
    args = p.parse_args()

    query = ' '.join(args.query)
    chunks = cargar_chunks(args.db)

    if not chunks:
        print("⚠️  No hay chunks en la DB")
        sys.exit(0)

    print(f"📦 {len(chunks)} chunks cargados desde {args.db}")

    textos = [c['texto'] for c in chunks]
    corpus = bm25s.tokenize(textos, stopwords="es")

    retriever = bm25s.BM25()
    retriever.index(corpus)

    q = bm25s.tokenize([query], stopwords="es")
    k = min(args.k, len(chunks))
    results, scores = retriever.retrieve(q, k=k)

    print(f"\n🔍 Query: {query}\n")
    for i, idx in enumerate(results[0]):
        c = chunks[idx]
        score = scores[0][i]
        print(f"  [{score:.3f}] {c['video']} pos={c['posicion']}")
        print(f"       {c['texto'][:150].replace(chr(10), ' ')}...")
        print()


if __name__ == '__main__':
    main()
