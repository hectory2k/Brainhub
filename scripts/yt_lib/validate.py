"""
yt_lib/validate.py

Validacion de sincronizacion de una pista contra el video real.

Genera 5 puntos distribuidos y muestra:
- URL para abrir el video en ese segundo
- Texto esperado (del transcript)
- Pide al usuario confirmar si coincide

Registra el resultado en metadata.json.
"""

from __future__ import annotations

from typing import Any

from . import io


# Proporciones de la duracion para muestrear
PUNTOS_PROPORCIONES = [0.02, 0.25, 0.50, 0.75, 0.93]

# Umbrales de offset aceptable (segundos)
OFFSET_EXCELENTE = 2.0
OFFSET_ACEPTABLE = 4.0


def generar_puntos(video_id: str, lang: str, role: str) -> list[dict[str, Any]]:
    """
    Genera 5 puntos de validacion distribuidos en el video.
    """
    segmentos = io.read_jsonl(io.track_jsonl(video_id, lang, role))
    if not segmentos:
        raise RuntimeError(f"No hay segmentos en {lang}.{role}")

    duracion_total = segmentos[-1]["end"]
    puntos = []

    for prop in PUNTOS_PROPORCIONES:
        objetivo = duracion_total * prop

        # Buscar el segmento cuyo start este mas cerca del objetivo
        mejor = min(segmentos, key=lambda s: abs(s["start"] - objetivo))

        puntos.append({
            "proporcion": prop,
            "objetivo_seconds": round(objetivo, 1),
            "start_seconds": round(mejor["start"], 1),
            "texto": mejor["text"],
            "url": f"https://www.youtube.com/watch?v={video_id}&t={int(mejor['start'])}s",
        })

    return puntos


def mostrar_puntos(puntos: list[dict[str, Any]]) -> None:
    """Muestra los puntos en consola."""
    print()
    print("=" * 70)
    print("VALIDACION DE SINCRONIZACION")
    print("=" * 70)
    print()
    print("Abrí cada URL y verificá si el texto coincide con lo que dice el video.")
    print("Al terminar, volvé acá y respondé las preguntas.")
    print()

    for i, p in enumerate(puntos, 1):
        print(f"[{i}/{len(puntos)}] {p['start_seconds']}s")
        print(f"  Texto esperado: {p['texto'][:80]}")
        print(f"  URL: {p['url']}")
        print()


def pedir_validacion(puntos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Pide al usuario validar cada punto.
    Devuelve la lista de puntos con el offset observado.
    """
    print("=" * 70)
    print("Ahora respondé para cada punto:")
    print("=" * 70)
    print()

    for i, p in enumerate(puntos, 1):
        while True:
            respuesta = input(
                f"[{i}/{len(puntos)}] {p['start_seconds']}s — "
                f"¿El audio coincide? [s/n/offset en segundos]: "
            ).strip().lower()

            if respuesta in ("s", "si", "yes", "y"):
                p["validado"] = True
                p["offset_seconds"] = 0.0
                break
            elif respuesta in ("n", "no"):
                p["validado"] = False
                p["offset_seconds"] = None
                break
            else:
                # Intentar parsear como numero
                try:
                    offset = float(respuesta)
                    p["validado"] = True
                    p["offset_seconds"] = offset
                    break
                except ValueError:
                    print("  Respuesta invalida. Usar s/n o un numero (ej: 2.5)")
                    continue

    return puntos


def analizar_resultados(puntos: list[dict[str, Any]]) -> dict[str, Any]:
    """Determina el estado de validacion."""
    validados = [p for p in puntos if p.get("validado")]
    no_validados = [p for p in puntos if not p.get("validado")]

    if not validados:
        return {
            "status": "failed",
            "reason": "ningun punto valido",
            "validated_count": 0,
            "failed_count": len(no_validados),
        }

    offsets = [
        abs(p["offset_seconds"])
        for p in validados
        if p.get("offset_seconds") is not None
    ]

    max_offset = max(offsets) if offsets else 0.0

    if max_offset <= OFFSET_EXCELENTE and not no_validados:
        status = "validated"
    elif max_offset <= OFFSET_ACEPTABLE and len(no_validados) <= 1:
        status = "approximate"
    else:
        status = "not_for_navigation"

    return {
        "status": status,
        "validated_count": len(validados),
        "failed_count": len(no_validados),
        "max_offset_seconds": round(max_offset, 2),
        "offsets_seconds": [round(o, 2) for o in offsets],
        "checked_points_seconds": [p["start_seconds"] for p in puntos],
    }


def guardar_resultado(
    video_id: str,
    lang: str,
    role: str,
    resultado: dict[str, Any],
) -> None:
    """Guarda el resultado en metadata.json."""
    metadata = io.load_metadata(video_id) or {"video_id": video_id, "tracks": []}

    track_id = io.track_id(lang, role)
    tracks = metadata.get("tracks", [])

    for t in tracks:
        if t.get("track_id") == track_id:
            t["timestamp_status"] = resultado["status"]
            t["timestamp_validation"] = resultado
            break

    metadata["tracks"] = tracks
    io.save_metadata(video_id, metadata)


def validate(video_id: str, lang: str, role: str, auto: bool = False) -> dict[str, Any]:
    """
    Valida la sincronizacion de un track.

    auto=True: solo muestra los puntos (sin pedir confirmacion).
    auto=False (default): pide confirmacion interactiva.
    """
    step = f"validate_{lang}_{role}"

    # Verificar que exista
    if not io.track_exists(video_id, lang, role):
        raise RuntimeError(
            f"El track {lang}.{role} no existe. Correr fetch primero."
        )

    puntos = generar_puntos(video_id, lang, role)
    mostrar_puntos(puntos)

    if auto:
        resultado = {
            "status": "pending_validation",
            "reason": "modo auto: requiere confirmacion manual",
            "checked_points_seconds": [p["start_seconds"] for p in puntos],
        }
    else:
        puntos_validados = pedir_validacion(puntos)
        resultado = analizar_resultados(puntos_validados)

    guardar_resultado(video_id, lang, role, resultado)
    io.mark_step(video_id, step, "done", validation_status=resultado["status"])

    return resultado
