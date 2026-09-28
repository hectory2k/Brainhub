"""
yt_lib/links.py

Generacion de links verificables a YouTube con timestamp.

Uso:
    from yt_lib.links import build_timestamped_url
    url = build_timestamped_url("HNClGfpmSfk", 225)
    # https://youtu.be/HNClGfpmSfk?t=225
"""

from __future__ import annotations

import re


# Patrones para extraer el video ID de distintos formatos de URL
_VIDEO_ID_PATTERNS = [
    # Formatos estandar
    r'(?:v=|/v/|embed/|youtu\.be/|/shorts/|watch\?v=)([a-zA-Z0-9_-]{11})',
    # Fallback: ID suelto al final o entre separadores
    r'(?:^|/)([a-zA-Z0-9_-]{11})(?:[?&#/]|$)',
]


def extract_video_id(url: str) -> str:
    """
    Extrae el ID de video de YouTube de multiples formatos de URL.

    Formatos soportados:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID

    Raises:
        ValueError: si no se puede extraer un ID valido.
    """
    if not url or not url.strip():
        raise ValueError("URL vacia")

    for pattern in _VIDEO_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"No se pudo extraer un ID de YouTube de: {url}")


def build_timestamped_url(
    video_id_or_url: str,
    start_seconds: float,
    *,
    full_url: bool = False,
) -> str:
    """
    Construye un link de YouTube con timestamp.

    Args:
        video_id_or_url: ID (11 chars) o URL completa de YouTube.
        start_seconds: segundo exacto del video.
        full_url: si True, devuelve youtube.com/watch?v=ID&t=Xs.
                  si False (default), devuelve youtu.be/ID?t=Xs.

    Returns:
        URL de YouTube con timestamp.
    """
    # Detectar si es ID o URL
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id_or_url):
        video_id = video_id_or_url
    else:
        video_id = extract_video_id(video_id_or_url)

    # Asegurar entero no negativo
    total_seconds = max(0, int(start_seconds))

    if full_url:
        return f"https://www.youtube.com/watch?v={video_id}&t={total_seconds}s"

    return f"https://youtu.be/{video_id}?t={total_seconds}"


def build_from_minutes_seconds(
    video_id_or_url: str,
    minutes: int,
    seconds: int,
    *,
    full_url: bool = False,
) -> str:
    """
    Construye un link con min:seg. Util para timestamps humanos.

    Ejemplo:
        build_from_minutes_seconds("HNClGfpmSfk", 3, 45)
        # https://youtu.be/HNClGfpmSfk?t=225
    """
    total = max(0, (minutes * 60) + seconds)
    return build_timestamped_url(video_id_or_url, total, full_url=full_url)


def format_timestamp(seconds: float) -> str:
    """
    Convierte segundos a formato legible MM:SS o HH:MM:SS.
    """
    total = int(seconds)
    horas, resto = divmod(total, 3600)
    minutos, seg = divmod(resto, 60)
    if horas:
        return f"{horas:02d}:{minutos:02d}:{seg:02d}"
    return f"{minutos:02d}:{seg:02d}"


def parse_timestamp(value: str) -> int:
    """
    Convierte 'MM:SS' o 'HH:MM:SS' a segundos.

    Ejemplo:
        parse_timestamp("3:45")    -> 225
        parse_timestamp("1:02:30") -> 3750
    """
    partes = value.strip().split(":")

    try:
        if len(partes) == 2:
            minutos, segundos = map(int, partes)
            return max(0, minutos * 60 + segundos)
        elif len(partes) == 3:
            horas, minutos, segundos = map(int, partes)
            return max(0, horas * 3600 + minutos * 60 + segundos)
        else:
            raise ValueError
    except ValueError:
        raise ValueError(f"Formato de timestamp invalido: {value}")


if __name__ == "__main__":
    # Demo del modulo
    video_ejemplo = "https://www.youtube.com/watch?v=HNClGfpmSfk"

    menciones = [
        {"tema": "Ateneo medico - Dr. Z", "min": 8, "seg": 15},
        {"tema": "Explicacion del paper X", "min": 12, "seg": 34},
        {"tema": "Verificacion de audio", "min": 3, "seg": 45},
    ]

    print("=== LINKS GENERADOS POR BRAINHUB ===\n")
    for m in menciones:
        link = build_from_minutes_seconds(
            video_ejemplo, m["min"], m["seg"], full_url=True
        )
        timestamp = f"{m['min']}:{m['seg']:02d}"
        print(f"  {m['tema']} ({timestamp})")
        print(f"  {link}\n")
