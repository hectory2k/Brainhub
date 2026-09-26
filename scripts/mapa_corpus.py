#!/usr/bin/env python3
"""
mapa_corpus.py — Genera un mapa navegable del corpus BrainHub.

Uso:
    mapa_corpus.py --tabla                    # Índice de documentos
    mapa_corpus.py --termino "supervisor"     # Documentos que mencionan X
    mapa_corpus.py --nicho TECNOLOGIA         # Filtrar por nicho
    mapa_corpus.py --stats                    # Métricas agregadas
    mapa_corpus.py --json                     # Output JSON (default: markdown)
    mapa_corpus.py --output archivo.md        # Guardar en archivo
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DB_PATH = os.environ.get(
    "BRAINHUB_DB",
    "/sdcard/Download/analisis_consolidado.duckdb"
)


def query(sql: str) -> list[dict]:
    """Ejecuta SQL y devuelve lista de dicts."""
    cmd = ["duckdb", "-json", DB_PATH, sql]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Error DuckDB: {result.stderr}")
    if not result.stdout.strip():
        return []
    return json.loads(result.stdout)


def escape_sql(value: str) -> str:
    """Escapa string para SQL (solo comillas simples)."""
    return value.replace("'", "''")


def tabla_documentos() -> list[dict]:
    """Índice de todos los documentos."""
    return query("""
        SELECT 
            id,
            filename,
            nicho,
            total_segmentos,
            sentimiento_polaridad
        FROM analysis
        ORDER BY filename
    """)


def docs_por_termino(termino: str) -> list[dict]:
    """Documentos que mencionan un término."""
    t = escape_sql(termino.lower())
    return query(f"""
        SELECT 
            t.video AS documento,
            t.term,
            t.frequency,
            a.nicho
        FROM terminos_raw t
        LEFT JOIN analysis a ON a.filename = t.video
        WHERE LOWER(t.term) = '{t}'
        ORDER BY t.frequency DESC
    """)


def docs_por_nicho(nicho: str) -> list[dict]:
    """Documentos de un nicho."""
    n = escape_sql(nicho)
    return query(f"""
        SELECT 
            id,
            filename,
            total_segmentos,
            sentimiento_polaridad
        FROM analysis
        WHERE nicho = '{n}'
        ORDER BY filename
    """)


def stats() -> dict:
    """Métricas agregadas del corpus."""
    total = query("SELECT count(*) AS n FROM analysis")[0]["n"]
    total_terminos = query("SELECT count(*) AS n FROM terminos_raw")[0]["n"]
    total_unicos = query("SELECT count(DISTINCT term) AS n FROM terminos_raw")[0]["n"]

    por_nicho = query("""
        SELECT nicho, count(*) AS n
        FROM analysis
        GROUP BY nicho
        ORDER BY n DESC
    """)

    top_terminos = query("""
        SELECT term, sum(frequency) AS total
        FROM terminos_raw
        GROUP BY term
        ORDER BY total DESC
        LIMIT 20
    """)

    return {
        "total_documentos": total,
        "total_terminos_raw": total_terminos,
        "terminos_unicos": total_unicos,
        "por_nicho": por_nicho,
        "top_terminos": top_terminos,
    }


# --- Formatters ---

def fmt_tabla_md(rows: list[dict]) -> str:
    if not rows:
        return "(sin datos)\n"

    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
        )
    return "\n".join(lines) + "\n"


def fmt_stats_md(s: dict) -> str:
    lines = [
        "# Stats del corpus BrainHub",
        "",
        f"- Documentos: **{s['total_documentos']}**",
        f"- Terminos raw (filas): **{s['total_terminos_raw']}**",
        f"- Terminos unicos: **{s['terminos_unicos']}**",
        "",
        "## Documentos por nicho",
        "",
        fmt_tabla_md(s["por_nicho"]),
        "## Top 20 terminos",
        "",
        fmt_tabla_md(s["top_terminos"]),
    ]
    return "\n".join(lines)


# --- Main ---

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera un mapa navegable del corpus BrainHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    mapa_corpus.py --tabla
    mapa_corpus.py --termino "supervisor"
    mapa_corpus.py --nicho TECNOLOGIA
    mapa_corpus.py --stats
    mapa_corpus.py --stats --json --output stats.json
        """,
    )
    parser.add_argument("--tabla", action="store_true",
                        help="Indice de documentos")
    parser.add_argument("--termino", type=str,
                        help="Documentos que mencionan un termino")
    parser.add_argument("--nicho", type=str,
                        help="Documentos de un nicho")
    parser.add_argument("--stats", action="store_true",
                        help="Metricas agregadas")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON (default: markdown)")
    parser.add_argument("--output", type=Path,
                        help="Guardar en archivo")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limitar filas en la salida (0 = sin limite)")

    args = parser.parse_args()

    if not any([args.tabla, args.termino, args.nicho, args.stats]):
        parser.print_help()
        return 1

    if args.tabla:
        rows = tabla_documentos()
        if args.limit:
            rows = rows[:args.limit]
        output = json.dumps(rows, indent=2, ensure_ascii=False) if args.json else fmt_tabla_md(rows)
    elif args.termino:
        rows = docs_por_termino(args.termino)
        if args.limit:
            rows = rows[:args.limit]
        output = json.dumps(rows, indent=2, ensure_ascii=False) if args.json else fmt_tabla_md(rows)
    elif args.nicho:
        rows = docs_por_nicho(args.nicho)
        if args.limit:
            rows = rows[:args.limit]
        output = json.dumps(rows, indent=2, ensure_ascii=False) if args.json else fmt_tabla_md(rows)
    elif args.stats:
        s = stats()
        output = json.dumps(s, indent=2, ensure_ascii=False) if args.json else fmt_stats_md(s)
    else:
        output = ""

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"OK Guardado: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
