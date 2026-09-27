"""
yt_lib/io.py

Gestion de archivos para transcripts:
- Estructura de directorios
- Lectura/escritura de JSONL, clean.txt, timestamped.txt
- Metadata del video
- State del pipeline (idempotencia + resume)
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Directorio base del corpus
CORPUS_BASE = Path(
    os.environ.get("YTT_CORPUS", "/sdcard/Download/corpus")
)

# Formato de tiempo
def formato_tiempo(segundos: float) -> str:
    """Convierte segundos a MM:SS o HH:MM:SS."""
    total = int(segundos)
    horas, resto = divmod(total, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    return f"{minutos:02d}:{segundos:02d}"


# Rutas del video
def video_dir(video_id: str) -> Path:
    """Directorio base del video."""
    return CORPUS_BASE / video_id


def transcripts_dir(video_id: str) -> Path:
    """Directorio de transcripts."""
    return video_dir(video_id) / "transcripts"


def metadata_path(video_id: str) -> Path:
    """Path del metadata.json."""
    return video_dir(video_id) / "metadata.json"


def state_path(video_id: str) -> Path:
    """Path del .state.json (para resume)."""
    return video_dir(video_id) / ".state.json"


def track_base(video_id: str, lang: str, role: str) -> Path:
    """Path base de un track (sin extension)."""
    return transcripts_dir(video_id) / f"{lang}.{role}"


def track_jsonl(video_id: str, lang: str, role: str) -> Path:
    return transcripts_dir(video_id) / f"{lang}.{role}.jsonl"


def track_clean(video_id: str, lang: str, role: str) -> Path:
    return transcripts_dir(video_id) / f"{lang}.{role}.clean.txt"


def track_timestamped(video_id: str, lang: str, role: str) -> Path:
    return transcripts_dir(video_id) / f"{lang}.{role}.timestamped.txt"


def track_id(lang: str, role: str) -> str:
    """ID canonico del track, ej: 'en_source'."""
    return f"{lang}_{role}"


# Crear estructura
def ensure_video_dirs(video_id: str) -> Path:
    """Crea los directorios necesarios. Idempotente."""
    transcripts_dir(video_id).mkdir(parents=True, exist_ok=True)
    return video_dir(video_id)


# --- State ---

def load_state(video_id: str) -> dict[str, Any]:
    """Carga el state o devuelve uno vacio."""
    path = state_path(video_id)
    if not path.exists():
        return {
            "video_id": video_id,
            "started_at": _now(),
            "last_updated": _now(),
            "steps": {},
        }

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "video_id": video_id,
            "started_at": _now(),
            "last_updated": _now(),
            "steps": {},
        }


def save_state(video_id: str, state: dict[str, Any]) -> None:
    """Guarda el state de forma atomica."""
    ensure_video_dirs(video_id)
    state["last_updated"] = _now()
    _atomic_write_json(state_path(video_id), state)


def mark_step(video_id: str, step: str, status: str, **extra) -> None:
    """Marca un paso del pipeline con su estado."""
    state = load_state(video_id)
    state["steps"][step] = {
        "status": status,
        "at": _now(),
        **extra,
    }
    save_state(video_id, state)


def is_step_done(video_id: str, step: str) -> bool:
    """Verifica si un paso ya se completo."""
    state = load_state(video_id)
    return state["steps"].get(step, {}).get("status") == "done"


# --- Metadata ---

def load_metadata(video_id: str) -> dict[str, Any] | None:
    """Carga el metadata o None si no existe."""
    path = metadata_path(video_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_metadata(video_id: str, metadata: dict[str, Any]) -> None:
    """Guarda el metadata de forma atomica."""
    ensure_video_dirs(video_id)
    _atomic_write_json(metadata_path(video_id), metadata)


# --- Segmentos (JSONL) ---

def write_jsonl(path: Path, segmentos: list[dict[str, Any]]) -> None:
    """Escribe segmentos como JSONL (una linea por segmento)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        for seg in segmentos:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

    tmp.replace(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Lee segmentos desde JSONL."""
    if not path.exists():
        return []
    segmentos = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                segmentos.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return segmentos


def write_clean(path: Path, segmentos: list[dict[str, Any]]) -> None:
    """Escribe texto limpio (solo el texto, sin timestamps)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        for seg in segmentos:
            f.write(seg["text"] + "\n")
        f.flush()
        os.fsync(f.fileno())

    tmp.replace(path)


def write_timestamped(path: Path, segmentos: list[dict[str, Any]]) -> None:
    """Escribe texto con timestamps [MM:SS] al inicio."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        for seg in segmentos:
            marca = formato_tiempo(seg["start"])
            f.write(f"[{marca}] {seg['text']}\n")
        f.flush()
        os.fsync(f.fileno())

    tmp.replace(path)


# --- Helpers ---

def _now() -> str:
    """Timestamp ISO en UTC."""
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: Any) -> None:
    """Escritura atomica de JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

    tmp.replace(path)


def track_exists(video_id: str, lang: str, role: str) -> bool:
    """Verifica si un track ya esta descargado (los 3 archivos)."""
    return (
        track_jsonl(video_id, lang, role).exists()
        and track_clean(video_id, lang, role).exists()
        and track_timestamped(video_id, lang, role).exists()
    )
