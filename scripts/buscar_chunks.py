#!/usr/bin/env python3
"""Búsqueda optimizada de chunks con BM25s + filtros + highlight + timestamps."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import bm25s
except ImportError:
    print("❌ Falta bm25s. Instalá: pip install bm25s")
    sys.exit(1)

DB_PATH = Path("/sdcard/Download/analisis_consolidado.duckdb")
if not DB_PATH.exists():
    DB_PATH = Path.home() / "proyectos/nlp/data/analisis_consolidado.duckdb"


def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.replace("\\n", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", texto).strip()


def recortar_en_palabra(texto: str, max_chars: int = 70) -> str:
    if len(texto) <= max_chars:
        return texto
    recorte = texto[:max_chars]
    ultimo_espacio = recorte.rfind(" ")
    if ultimo_espacio > max_chars * 0.7:
        recorte = recorte[:ultimo_espacio]
    return recorte.rstrip() + "…"


def highlight(texto: str, query: str) -> str:
    if not query:
        return texto
    terminos = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    for t in terminos:
        texto = re.sub(f"({re.escape(t)})", r"\033[1;33m\1\033[0m", texto, flags=re.IGNORECASE)
    return texto


def minuto_a_seg(minuto) -> int:
    """Convierte float (segundos) o string 'MM:SS' a segundos enteros."""
    if isinstance(minuto, (int, float)):
        return int(minuto)
    if isinstance(minuto, str) and ":" in minuto:
        partes = [int(p) for p in minuto.split(":")]
        if len(partes) == 2:
            return partes[0] * 60 + partes[1]
        if len(partes) == 3:
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
    return 0


def formato_minuto(segundos: float) -> str:
    if segundos is None:
        return "??:??"
    m = int(segundos // 60)
    s = int(segundos % 60)
    return f"{m:02d}:{s:02d}"


def extraer_youtube_id(video_nombre: str) -> str:
    # 1. Intentar extraer lo que viene después de "Transcript_"
    match = re.search(r'Transcript_([A-Za-z0-9_-]{11})', video_nombre)
    if match:
        return match.group(1)
    # 2. Fallback: buscar cualquier bloque de 11 chars que NO sea "Transcript_"
    for m in re.finditer(r'[A-Za-z0-9_-]{11}', video_nombre):
        if m.group(0) != "Transcript_":
            return m.group(0)
    return video_nombre


def cargar_chunks(db_path: Path, video_id: str = None):
    """Carga chunks usando el CLI de DuckDB."""
    sql = "SELECT chunk_id, video, t_inicio, texto FROM chunks WHERE texto IS NOT NULL"
    if video_id:
        video_safe = video_id.replace("'", "''")
        sql += f" AND video = '{video_safe}'"
    sql += " ORDER BY video, t_inicio"
    
    result = subprocess.run(
        ['duckdb', '-readonly', '-json', str(db_path), '-c', sql],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error ejecutando DuckDB: {result.stderr}")
        sys.exit(1)
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Error parseando JSON de DuckDB")
        sys.exit(1)


def buscar_bm25(chunks, query: str, top_k: int = 5):
    if not chunks:
        return []
    textos = [limpiar_texto(c['texto']) for c in chunks]
    corpus = [re.findall(r"\w+", t.lower()) for t in textos]
    
    retriever = bm25s.BM25()
    retriever.index(corpus)
    
    query_tokens = re.findall(r"\w+", query.lower())
    results, scores = retriever.retrieve([query_tokens], k=min(top_k, len(textos)))
    
    salida = []
    for i, idx in enumerate(results[0]):
        chunk = chunks[idx]
        salida.append({
            "chunk_id": chunk['chunk_id'],
            "video": chunk['video'],
            "t_inicio": chunk['t_inicio'],
            "fragmento": textos[idx],
            "score": float(scores[0][i]),
        })
    return salida


def imprimir_resultados(resultados, query: str, ancho: int = 70):
    if not resultados:
        print(f"\n🔍 Sin resultados para: {query}\n")
        return

    print(f"\n🔍 {len(resultados)} resultado(s) para: '{query}'\n")
    print("┌" + "─" * (ancho + 2) + "┐")

    for r in resultados:
        frag = recortar_en_palabra(r["fragmento"], max_chars=ancho - 4)
        frag = highlight(frag, query)
        minuto_str = formato_minuto(r['t_inicio'])
        yt_id = extraer_youtube_id(r['video'])
        segundos = minuto_a_seg(r['t_inicio'])
        meta = f"[{yt_id} @ {minuto_str}]"
        
        print(f"│ {meta:<{ancho}} │")
        print(f"│ {frag:<{ancho}} │")
        print(f"│ score: {r['score']:.3f}  →  https://youtu.be/{yt_id}?t={segundos}")
        print("├" + "─" * (ancho + 2) + "┤")

    print("└" + "─" * (ancho + 2) + "┘\n")


def main():
    ap = argparse.ArgumentParser(description="Búsqueda BM25 sobre chunks con timestamps.")
    ap.add_argument("query", help="Términos a buscar")
    ap.add_argument("-k", "--top", type=int, default=5, help="Cantidad de resultados")
    ap.add_argument("-v", "--video", help="Filtrar por video (ej: Transcript_XXX_ES)")
    ap.add_argument("--ancho", type=int, default=70, help="Ancho de salida")
    ap.add_argument("--db", default=str(DB_PATH), help="Ruta a DuckDB")
    args = ap.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ No existe la DB: {args.db}")
        sys.exit(1)

    chunks = cargar_chunks(db_path, video_id=args.video)
    resultados = buscar_bm25(chunks, args.query, top_k=args.top)
    imprimir_resultados(resultados, args.query, ancho=args.ancho)

if __name__ == "__main__":
    main()
