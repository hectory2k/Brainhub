#!/usr/bin/env python3
"""
yt_transcript.py

CLI para gestionar transcripts de YouTube en BrainHub.

Uso:
    yt_transcript.py inspect VIDEO_ID
    yt_transcript.py fetch VIDEO_ID --lang LANG --role ROLE
    yt_transcript.py validate VIDEO_ID --track LANG_ROLE [--auto]
    yt_transcript.py status VIDEO_ID
"""

import argparse
import json
import sys
from pathlib import Path

# Asegurar que yt_lib sea importable
sys.path.insert(0, str(Path(__file__).parent))

from yt_lib import fetch as fetch_mod
from yt_lib import io
from yt_lib import validate as validate_mod


def cmd_inspect(args) -> int:
    pistas = fetch_mod.inspect(args.video_id)
    print(f"\nPistas disponibles para {args.video_id}:\n")
    print(f"{'Idioma':10} {'Nombre':45} {'Gen':5} {'Trad':5}")
    print("-" * 70)
    for p in pistas:
        print(
            f"{p['language_code']:10} "
            f"{p['language_name'][:44]:45} "
            f"{'si' if p['is_generated'] else 'no':5} "
            f"{'si' if p['is_translatable'] else 'no':5}"
        )
    print(f"\nTotal: {len(pistas)} pistas\n")
    return 0


def cmd_fetch(args) -> int:
    resultado = fetch_mod.fetch(args.video_id, args.lang, args.role)
    print(f"\nOK: {resultado['status']}")
    print(f"  Track: {resultado['lang']}.{resultado['role']}")
    print(f"  Path:  {resultado['path']}")
    if resultado.get("segments"):
        print(f"  Segmentos: {resultado['segments']}")
        print(f"  Metodo:    {resultado.get('method', 'cached')}")
    return 0


def cmd_validate(args) -> int:
    # Parsear track "en_source" -> ("en", "source")
    parts = args.track.rsplit("_", 1)
    if len(parts) != 2:
        print(f"ERROR: track invalido: {args.track}")
        print("Formato esperado: LANG_ROLE (ej: en_source)")
        return 1

    lang, role = parts
    resultado = validate_mod.validate(args.video_id, lang, role, auto=args.auto)

    print()
    print("=" * 70)
    print(f"RESULTADO: {resultado['status']}")
    print("=" * 70)
    if "max_offset_seconds" in resultado:
        print(f"  Offset maximo: {resultado['max_offset_seconds']}s")
    if "validated_count" in resultado:
        print(f"  Validados: {resultado['validated_count']}")
        print(f"  Fallidos:  {resultado['failed_count']}")
    print()
    return 0


def cmd_status(args) -> int:
    state = io.load_state(args.video_id)
    metadata = io.load_metadata(args.video_id)

    print(f"\nEstado de {args.video_id}\n")
    print(f"  Started:  {state.get('started_at', '?')}")
    print(f"  Updated:  {state.get('last_updated', '?')}")
    print()

    steps = state.get("steps", {})
    if steps:
        print("  Pasos:")
        for step, info in sorted(steps.items()):
            status = info.get("status", "?")
            extra = ""
            if info.get("segments"):
                extra = f" ({info['segments']} segs)"
            if info.get("source"):
                extra += f" [{info['source']}]"
            print(f"    {step:30} {status}{extra}")
    else:
        print("  (sin pasos ejecutados)")

    if metadata:
        print()
        print("  Tracks:")
        for t in metadata.get("tracks", []):
            print(
                f"    {t.get('track_id', '?'):25} "
                f"{t.get('segments', '?')} segs "
                f"[{t.get('method', '?')}] "
                f"sync={t.get('timestamp_status', 'sin validar')}"
            )

    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gestion de transcripts de YouTube para BrainHub",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Listar pistas")
    p_inspect.add_argument("video_id")
    p_inspect.set_defaults(func=cmd_inspect)

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Descargar pista")
    p_fetch.add_argument("video_id")
    p_fetch.add_argument("--lang", required=True)
    p_fetch.add_argument("--role", required=True,
                        choices=["source", "manual", "asr",
                                "translated", "dubbed", "unknown"])
    p_fetch.set_defaults(func=cmd_fetch)

    # validate
    p_val = subparsers.add_parser("validate", help="Validar sincronizacion")
    p_val.add_argument("video_id")
    p_val.add_argument("--track", required=True,
                      help="Track ID (ej: en_source)")
    p_val.add_argument("--auto", action="store_true",
                      help="Solo mostrar puntos, sin pedir confirmacion")
    p_val.set_defaults(func=cmd_validate)

    # status
    p_status = subparsers.add_parser("status", help="Ver estado")
    p_status.add_argument("video_id")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
