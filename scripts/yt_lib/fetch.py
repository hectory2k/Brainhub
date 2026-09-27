"""
yt_lib/fetch.py

Descarga de transcripts desde YouTube con:
- Fallback en cascada: youtube_transcript_api -> yt-dlp
- Idempotencia: si el track ya existe, no re-descarga
- State: marca el paso como done/failed
- Normalizacion a formato canonico (jsonl + clean + timestamped)
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import io

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None


# Idiomas en orden de preferencia (para inspect)
IDIOMAS_PREFERIDOS = ["es", "es-US", "es-419", "en"]


def limpiar_texto(texto: str) -> str:
    """Colapsa espacios y limpia."""
    return re.sub(r"\s+", " ", texto).strip()


# --- Inspeccion ---

def inspect(video_id: str) -> list[dict[str, Any]]:
    """
    Lista las pistas disponibles de un video.
    No descarga nada.
    """
    if YouTubeTranscriptApi is None:
        raise RuntimeError(
            "youtube_transcript_api no esta instalado. "
            "Instalar: pip install youtube-transcript-api"
        )

    api = YouTubeTranscriptApi()
    pistas = []

    try:
        for t in api.list(video_id):
            pistas.append({
                "language_code": t.language_code,
                "language_name": t.language,
                "is_generated": bool(t.is_generated),
                "is_translatable": bool(t.is_translatable),
            })
    except Exception as e:
        raise RuntimeError(f"No se pudieron listar pistas: {e}")

    return pistas


# --- Descarga via API ---

def descargar_via_api(video_id: str, lang: str) -> tuple[list[dict], str]:
    """
    Descarga via youtube_transcript_api.
    Devuelve (segmentos_normalizados, idioma_usado).
    """
    if YouTubeTranscriptApi is None:
        raise RuntimeError("youtube_transcript_api no instalado")

    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=[lang])

    segmentos = []
    for i, snippet in enumerate(transcript):
        texto = limpiar_texto(snippet.text)
        if not texto:
            continue

        inicio = float(snippet.start)
        duracion = float(snippet.duration)

        segmentos.append({
            "video_id": video_id,
            "segment_id": i,
            "start": inicio,
            "end": inicio + duracion,
            "duration": duracion,
            "text": texto,
        })

    return segmentos, lang


# --- Descarga via yt-dlp (fallback) ---

def descargar_via_ytdlp(video_id: str, lang: str) -> tuple[list[dict], str]:
    """
    Fallback: descarga subtitulos via yt-dlp.
    Devuelve (segmentos_normalizados, idioma_usado).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        url = f"https://www.youtube.com/watch?v={video_id}"

        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-lang", lang,
            "--sub-format", "json3/vtt/srt",
            "--sleep-requests", "3",
            "-o", str(tmppath / "%(id)s.%(ext)s"),
            url,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        sub_files = (
            list(tmppath.glob("*.json3"))
            + list(tmppath.glob("*.vtt"))
            + list(tmppath.glob("*.srt"))
        )

        if not sub_files:
            raise RuntimeError(
                f"yt-dlp no genero subtitulos. "
                f"stderr: {result.stderr[:200]}"
            )

        # Preferir json3 > vtt > srt
        sub_file = None
        for ext in ["json3", "vtt", "srt"]:
            candidates = [f for f in sub_files if f.suffix[1:] == ext]
            if candidates:
                sub_file = candidates[0]
                break

        if not sub_file:
            raise RuntimeError("No se encontro subtitulo valido")

        segmentos = parsear_subtitulo(sub_file, video_id)
        return segmentos, lang


def parsear_subtitulo(path: Path, video_id: str) -> list[dict[str, Any]]:
    """Convierte VTT/SRT a segmentos normalizados."""
    contenido = path.read_text(encoding="utf-8", errors="replace")

    # Regex: inicio --> fin \n texto
    patron = re.compile(
        r"(\d{1,2}:\d{2}:\d{2})[.,](\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2})[.,](\d{3})\s*\n(.*?)(?=\n\n|\n\d+\n|$)",
        re.DOTALL,
    )

    segmentos = []
    for i, match in enumerate(patron.finditer(contenido)):
        start_str, start_ms, end_str, end_ms, texto = match.groups()

        h1, m1, s1 = map(int, start_str.split(":"))
        start = h1 * 3600 + m1 * 60 + s1 + int(start_ms) / 1000

        h2, m2, s2 = map(int, end_str.split(":"))
        end = h2 * 3600 + m2 * 60 + s2 + int(end_ms) / 1000

        texto_limpio = re.sub(r"<[^>]+>", "", texto)
        texto_limpio = limpiar_texto(texto_limpio)

        if texto_limpio:
            segmentos.append({
                "video_id": video_id,
                "segment_id": i,
                "start": start,
                "end": end,
                "duration": end - start,
                "text": texto_limpio,
            })

    return segmentos


# --- Fetch principal (idempotente) ---

def fetch(video_id: str, lang: str, role: str) -> dict[str, Any]:
    """
    Descarga un track (lang + role) con fallback en cascada.

    Idempotente:
    - Si los 3 archivos ya existen, no re-descarga.
    - Marca state como done.

    Devuelve dict con info del resultado.
    """
    step = f"fetch_{lang}_{role}"

    # Idempotencia
    if io.track_exists(video_id, lang, role):
        io.mark_step(video_id, step, "done", source="cached")
        return {
            "status": "cached",
            "lang": lang,
            "role": role,
            "path": str(io.track_base(video_id, lang, role)),
        }

    io.ensure_video_dirs(video_id)
    io.mark_step(video_id, step, "running")

    # Intento 1: API
    segmentos = None
    metodo = None
    error_api = None

    try:
        segmentos, idioma = descargar_via_api(video_id, lang)
        metodo = "youtube_transcript_api"
    except Exception as e:
        error_api = str(e)

    # Intento 2: yt-dlp
    if segmentos is None:
        try:
            segmentos, idioma = descargar_via_ytdlp(video_id, lang)
            metodo = "yt-dlp"
        except Exception as e:
            io.mark_step(
                video_id, step, "failed",
                error_api=error_api,
                error_ytdlp=str(e),
            )
            raise RuntimeError(
                f"Fetch fallo para {video_id}/{lang}/{role}.\n"
                f"  API: {error_api}\n"
                f"  yt-dlp: {e}"
            )

    if not segmentos:
        io.mark_step(video_id, step, "failed", error="no_segments")
        raise RuntimeError(f"No se descargaron segmentos de {video_id}")

    # Escribir 3 archivos
    jsonl_path = io.track_jsonl(video_id, lang, role)
    clean_path = io.track_clean(video_id, lang, role)
    ts_path = io.track_timestamped(video_id, lang, role)

    io.write_jsonl(jsonl_path, segmentos)
    io.write_clean(clean_path, segmentos)
    io.write_timestamped(ts_path, segmentos)

    # Metadata del track
    _merge_track_metadata(video_id, lang, role, idioma, metodo, segmentos)

    # Marcar done
    io.mark_step(
        video_id, step, "done",
        source=metodo,
        lang=idioma,
        segments=len(segmentos),
    )

    return {
        "status": "fetched",
        "lang": lang,
        "role": role,
        "language_used": idioma,
        "method": metodo,
        "segments": len(segmentos),
        "path": str(jsonl_path.parent),
    }


def _merge_track_metadata(
    video_id: str,
    lang: str,
    role: str,
    idioma: str,
    metodo: str,
    segmentos: list[dict],
) -> None:
    """Actualiza metadata.json con la info del track."""
    metadata = io.load_metadata(video_id) or {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "retrieved_at": io._now(),
        "tracks": [],
    }

    track_id = io.track_id(lang, role)

    nueva = {
        "track_id": track_id,
        "language_code": idioma,
        "role": role,
        "method": metodo,
        "segments": len(segmentos),
        "duration_seconds": segmentos[-1]["end"] if segmentos else 0,
        "retrieved_at": io._now(),
    }

    # Reemplazar si ya existe
    tracks = metadata.get("tracks", [])
    tracks = [t for t in tracks if t.get("track_id") != track_id]
    tracks.append(nueva)
    metadata["tracks"] = tracks

    io.save_metadata(video_id, metadata)
