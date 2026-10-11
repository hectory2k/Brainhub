#!/usr/bin/env python3
"""
pdf2txt.py — PDF → TXT → descolumnar en batch. Multiplataforma.

Portabilidad:
  - Home se resuelve vía Path.home() (respeta $HOME en Termux/Linux, %USERPROFILE% en Windows).
  - Temp configurable: --temp DIR  |  env PDF2TXT_TEMP  |  default: <home>/temp
  - Out configurable: --out DIR   |  env PDF2TXT_OUT   |  default: mismo que temp
  - Acepta ~ y $HOME en cualquier ruta.
  - pdftotext se resuelve vía PATH.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Importar descolumnar desde el mismo dir que este script (portable)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from descolumnar import procesar_columnas  # noqa: E402


# ---------- config portable ----------

HOME = Path.home()  # respeta $HOME / %USERPROFILE%
MIN_TEXTO_VALIDO = 50


def resolver_temp(cli_temp: Path | None) -> Path:
    """Prioridad: --temp  >  $PDF2TXT_TEMP  >  <home>/temp"""
    if cli_temp is not None:
        return cli_temp.expanduser().resolve()
    env = os.environ.get("PDF2TXT_TEMP")
    if env:
        return Path(env).expanduser().resolve()
    return (HOME / "temp").resolve()


def resolver_out(cli_out: Path | None, temp: Path) -> Path:
    """Prioridad: --out  >  $PDF2TXT_OUT  >  temp"""
    if cli_out is not None:
        return cli_out.expanduser().resolve()
    env = os.environ.get("PDF2TXT_OUT")
    if env:
        return Path(env).expanduser().resolve()
    return temp


# ---------- utilidades ----------

def tiene_contenido(path: Path, minimo: int = MIN_TEXTO_VALIDO) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return len(txt.strip()) >= minimo


def extraer_pdf(pdf: Path, txt: Path) -> tuple[bool, str]:
    """pdftotext -layout, resuelto por PATH (portable)."""
    try:
        r = subprocess.run(
            ["pdftotext", "-layout", str(pdf), str(txt)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout pdftotext"
    except FileNotFoundError:
        return False, "pdftotext no está en PATH"

    if r.returncode != 0:
        return False, f"pdftotext rc={r.returncode}: {r.stderr.strip()[:120]}"

    if not tiene_contenido(txt):
        return False, "PDF probablemente escaneado (texto vacío)"

    return True, "ok"


# ---------- núcleo por PDF ----------

def procesar_pdf(pdf: Path, temp: Path, out_dir: Path, *,
                 force: bool = False,
                 clean_raw: bool = False,
                 dry_run: bool = False) -> dict:
    base = pdf.stem
    raw_txt = temp / f"{base}_salida.txt"
    final_txt = out_dir / f"{base}_salida_continuo.txt"

    resultado = {"pdf": pdf, "estado": None, "motivo": "",
                 "raw": raw_txt, "final": final_txt}

    if final_txt.exists() and tiene_contenido(final_txt) and not force:
        resultado["estado"] = "skip"
        resultado["motivo"] = f"ya existe ({final_txt})"
        return resultado

    if dry_run:
        resultado["estado"] = "dry"
        resultado["motivo"] = f"→ {final_txt}"
        return resultado

    ok, motivo = extraer_pdf(pdf, raw_txt)
    if not ok:
        resultado["estado"] = "escaneado" if "escaneado" in motivo else "error"
        resultado["motivo"] = motivo
        if raw_txt.exists() and not tiene_contenido(raw_txt):
            raw_txt.unlink()
        return resultado

    try:
        res = procesar_columnas(str(raw_txt), str(final_txt))
        valido, razon = res.es_valido()
    except Exception as e:
        valido, razon, res = False, f"descolumnar excepción: {e}", None

    if valido and tiene_contenido(final_txt):
        resultado["estado"] = "ok"
        li = getattr(res, "lineas_izq", "?")
        ld = getattr(res, "lineas_der", "?")
        resultado["motivo"] = f"{li}izq+{ld}der"

    elif valido and not tiene_contenido(final_txt):
        shutil.copyfile(raw_txt, final_txt)
        if not tiene_contenido(final_txt):
            resultado["estado"] = "error"
            resultado["motivo"] = "descolumnar vacío y crudo también"
            return resultado
        resultado["estado"] = "fallback"
        resultado["motivo"] = "descolumnar devolvió salida vacía"

    else:
        shutil.copyfile(raw_txt, final_txt)
        if not tiene_contenido(final_txt):
            resultado["estado"] = "error"
            resultado["motivo"] = f"fallback vacío ({razon})"
            return resultado
        resultado["estado"] = "fallback"
        resultado["motivo"] = razon

    if clean_raw and raw_txt.exists():
        raw_txt.unlink()

    return resultado


# ---------- CLI ----------

def parse_args():
    p = argparse.ArgumentParser(
        description="PDF → TXT → descolumnar en batch (portable, temp configurable)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Variables de entorno:
  PDF2TXT_TEMP   carpeta de intermedios  (default: <home>/temp)
  PDF2TXT_OUT    carpeta de salida final (default: igual a TEMP)

Ejemplos:
  python3 pdf2txt.py paper.pdf
  python3 pdf2txt.py --dir ~/pdfs --recursive
  PDF2TXT_TEMP=/tmp/pdfwork python3 pdf2txt.py a.pdf b.pdf
  python3 pdf2txt.py --temp /tmp/x --out ~/txt --dir ~/pdfs
""",
    )
    p.add_argument("pdfs", nargs="*", type=Path,
                   help="archivos PDF (aceptan ~ y $HOME)")
    p.add_argument("--dir", type=Path, default=None,
                   help="carpeta con PDFs (acepta ~ y $HOME)")
    p.add_argument("--recursive", "-r", action="store_true",
                   help="buscar PDFs recursivamente en --dir")
    p.add_argument("--temp", type=Path, default=None,
                   help="carpeta de intermedios (default: $PDF2TXT_TEMP o <home>/temp)")
    p.add_argument("--out", type=Path, default=None,
                   help="carpeta de salida final (default: $PDF2TXT_OUT o igual a --temp)")
    p.add_argument("--force", "-f", action="store_true",
                   help="reprocesar aunque exista el _continuo.txt")
    p.add_argument("--clean-raw", action="store_true",
                   help="borrar el <base>_salida.txt tras descolumnar OK")
    p.add_argument("--dry-run", action="store_true",
                   help="no escribe nada, solo muestra qué haría")
    return p.parse_args()


def recolectar_pdfs(args) -> list[Path]:
    pdfs = [p.expanduser() for p in args.pdfs if p.suffix.lower() == ".pdf"]
    if args.dir:
        d = args.dir.expanduser()
        pat = "**/*.pdf" if args.recursive else "*.pdf"
        pdfs += sorted(d.glob(pat))
    vistos, out = set(), []
    for p in pdfs:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp not in vistos and rp.exists() and rp.is_file():
            vistos.add(rp)
            out.append(p)
    return out


def main():
    args = parse_args()
    pdfs = recolectar_pdfs(args)

    if not pdfs:
        print("❌ No hay PDFs para procesar.", file=sys.stderr)
        print("   Uso: python3 pdf2txt.py archivo.pdf")
        print("        python3 pdf2txt.py --dir ~/pdfs --recursive")
        sys.exit(1)

    temp = resolver_temp(args.temp)
    out_dir = resolver_out(args.out, temp)
    temp.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📚 {len(pdfs)} PDF(s)")
    print(f"🏠 home        : {HOME}")
    print(f"📂 intermedios : {temp}")
    print(f"📂 salida final: {out_dir}\n")

    contadores = {k: 0 for k in ("ok", "fallback", "escaneado", "skip", "error", "dry")}
    detalles = []

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf.name}")
        res = procesar_pdf(
            pdf, temp, out_dir,
            force=args.force,
            clean_raw=args.clean_raw,
            dry_run=args.dry_run,
        )
        contadores[res["estado"]] += 1

        icono = {"ok": "✅", "fallback": "⚠️ ", "escaneado": "🖼️ ",
                 "skip": "⏭️ ", "error": "❌", "dry": "🧪"}[res["estado"]]
        print(f"        {icono} {res['estado']}: {res['motivo']}")
        detalles.append((pdf.name, res["estado"], res["motivo"]))

    print("\n" + "=" * 50)
    print("📊 Resumen")
    print("=" * 50)
    for k in ("ok", "fallback", "escaneado", "skip", "error", "dry"):
        if contadores[k]:
            print(f"  {k:10s}: {contadores[k]}")

    errores = [d for d in detalles if d[1] == "error"]
    if errores:
        print("\n❌ Errores (no se generó .txt):")
        for nombre, _, motivo in errores:
            print(f"   - {nombre}: {motivo}")

    fallbacks = [d for d in detalles if d[1] == "fallback"]
    if fallbacks:
        print("\n⚠️  Fallbacks (crudo copiado sin descolumnar):")
        for nombre, _, motivo in fallbacks:
            print(f"   - {nombre}: {motivo}")

    sys.exit(1 if contadores["error"] else 0)


if __name__ == "__main__":
    main()
