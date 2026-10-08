"""Extractor de citas con peso semántico.

Usa Chunker para dividir texto en bloques coherentes,
luego rankea por score semántico (densidad + co-ocurrencia + polaridad + coherencia).
"""
from .extractor import ExtractorCitas

__all__ = ['ExtractorCitas']
