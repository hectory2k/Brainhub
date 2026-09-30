"""Chunker vitaminado — Annotator pattern.

Divide texto en chunks con metadata de provenance.
Serialización explícita vía a_dict() (consistente con timestamps.py).

Decisiones de diseño (2026-09-30):
- Estrategia default: por_oraciones (max_oraciones=10)
- Overlap: 0 (evidencia del video MCP: sin beneficio medible)
- chunk_id: {video}_{pos:04d}_{sha256(texto)[:8]} -> idempotente
- tier: default 'desconocido', refinar cuando el pipeline lo alimente
- Tokenizador: regex default (empata con NLTK en transcripts), NLTK opcional
"""
from dataclasses import dataclass, field
from typing import List, Dict, Callable
import hashlib
import re

_PATRON_ORACION = re.compile(r'(?<=[.!?])\s+')
_PATRON_PARRAFO = re.compile(r'\n\s*\n')


@dataclass
class Chunk:
    """Unidad de texto con metadata de provenance.

    Consistente con timestamps.SegmentoTemporal: campos explícitos,
    a_dict() método, sin magia de __dict__.
    """
    chunk_id: str
    video: str
    posicion: int
    texto: str
    start_char: int
    end_char: int
    n_oraciones: int
    estrategia: str
    tier: str = 'desconocido'
    metadata: Dict = field(default_factory=dict)

    def a_dict(self) -> Dict:
        """Serialización explícita. Compatible con json.dumps."""
        return {
            'chunk_id': self.chunk_id,
            'video': self.video,
            'posicion': self.posicion,
            'texto': self.texto,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'n_oraciones': self.n_oraciones,
            'estrategia': self.estrategia,
            'tier': self.tier,
            'metadata': self.metadata,
        }


class Chunker:
    """Divide texto en chunks con metadata.

    Estrategias: 'oraciones' (default), 'parrafos', 'caracteres'.
    Tokenizador: 'regex' (default), 'nltk' (opcional).
    """

    def __init__(self, estrategia: str = 'oraciones',
                 tokenizer: str = 'regex', **params):
        self.estrategia = estrategia
        self.tokenizer = tokenizer
        self.params = params
        self._tokenizadores: Dict[str, Callable[[str], List[str]]] = {
            'regex': self._tokenizar_regex,
            'nltk': self._tokenizar_nltk,
        }
        if tokenizer not in self._tokenizadores:
            raise ValueError(
                f"tokenizer invalido: {tokenizer}. "
                f"Opciones: {list(self._tokenizadores.keys())}"
            )

    def _tokenizar_regex(self, texto: str) -> List[str]:
        oraciones = _PATRON_ORACION.split(texto)
        return [s.strip() for s in oraciones if s.strip()]

    def _tokenizar_nltk(self, texto: str) -> List[str]:
        try:
            from nltk.tokenize import sent_tokenize
        except ImportError as e:
            raise ImportError(
                "NLTK no disponible. Instalar: pip install nltk"
            ) from e
        return sent_tokenize(texto)

    def _generar_chunk_id(self, video: str, pos: int, texto: str) -> str:
        h = hashlib.sha256(texto.encode('utf-8')).hexdigest()[:8]
        return f"{video}_{pos:04d}_{h}"

    def _buscar_offset(self, texto_original: str, subtexto: str,
                       desde: int = 0) -> int:
        return texto_original.find(subtexto, desde)

    def _construir_metadata(self, texto: str) -> Dict:
        return {
            'n_chars': len(texto),
            'n_palabras': len(texto.split()),
        }

    def _por_oraciones(self, texto: str, video: str, tier: str) -> List[Chunk]:
        max_oraciones = self.params.get('max_oraciones', 10)
        tokenizar = self._tokenizadores[self.tokenizer]
        oraciones = tokenizar(texto)

        chunks = []
        pos = 0
        offset = 0
        for i in range(0, len(oraciones), max_oraciones):
            grupo = oraciones[i:i + max_oraciones]
            texto_chunk = ' '.join(grupo)

            start = self._buscar_offset(texto, grupo[0], offset)
            if start < 0:
                start = offset
            end = start + len(texto_chunk)
            offset = max(offset, end)

            chunks.append(Chunk(
                chunk_id=self._generar_chunk_id(video, pos, texto_chunk),
                video=video,
                posicion=pos,
                texto=texto_chunk,
                start_char=start,
                end_char=end,
                n_oraciones=len(grupo),
                estrategia='oraciones',
                tier=tier,
                metadata=self._construir_metadata(texto_chunk),
            ))
            pos += 1
        return chunks

    def _por_parrafos(self, texto: str, video: str, tier: str) -> List[Chunk]:
        max_parrafos = self.params.get('max_parrafos', 3)
        parrafos = [p.strip() for p in _PATRON_PARRAFO.split(texto) if p.strip()]

        chunks = []
        pos = 0
        offset = 0
        for i in range(0, len(parrafos), max_parrafos):
            grupo = parrafos[i:i + max_parrafos]
            texto_chunk = '\n\n'.join(grupo)

            start = self._buscar_offset(texto, grupo[0], offset)
            if start < 0:
                start = offset
            end = start + len(texto_chunk)
            offset = max(offset, end)

            chunks.append(Chunk(
                chunk_id=self._generar_chunk_id(video, pos, texto_chunk),
                video=video,
                posicion=pos,
                texto=texto_chunk,
                start_char=start,
                end_char=end,
                n_oraciones=0,
                estrategia='parrafos',
                tier=tier,
                metadata=self._construir_metadata(texto_chunk),
            ))
            pos += 1
        return chunks

    def _por_caracteres(self, texto: str, video: str, tier: str) -> List[Chunk]:
        max_chars = self.params.get('max_chars', 2000)
        overlap = self.params.get('overlap', 0)
        paso = max_chars - overlap
        if paso <= 0:
            raise ValueError(
                f"overlap ({overlap}) debe ser < max_chars ({max_chars})"
            )

        chunks = []
        pos = 0
        for start in range(0, len(texto), paso):
            end = min(start + max_chars, len(texto))
            texto_chunk = texto[start:end]
            if not texto_chunk.strip():
                continue

            chunks.append(Chunk(
                chunk_id=self._generar_chunk_id(video, pos, texto_chunk),
                video=video,
                posicion=pos,
                texto=texto_chunk,
                start_char=start,
                end_char=end,
                n_oraciones=0,
                estrategia='caracteres',
                tier=tier,
                metadata=self._construir_metadata(texto_chunk),
            ))
            pos += 1
            if end >= len(texto):
                break
        return chunks

    def chunkear(self, texto: str, video: str,
                 tier: str = 'desconocido') -> List[Chunk]:
        if not texto or not texto.strip():
            return []

        estrategias = {
            'oraciones': self._por_oraciones,
            'parrafos': self._por_parrafos,
            'caracteres': self._por_caracteres,
        }
        if self.estrategia not in estrategias:
            raise ValueError(
                f"estrategia invalida: {self.estrategia}. "
                f"Opciones: {list(estrategias.keys())}"
            )
        return estrategias[self.estrategia](texto, video, tier)
