"""Chunker vitaminado — Annotator pattern.

Divide texto en chunks con metadata de provenance.
Consistente con timestamps.SegmentoTemporal (a_dict explícito).
"""
from .chunker import Chunk, Chunker

__all__ = ['Chunk', 'Chunker']
