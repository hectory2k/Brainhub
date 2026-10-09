"""Extractor de citas con peso semántico.

Filosofía: reutilizar Chunker para obtener bloques coherentes,
luego aplicar scoring multidimensional sin reinventar segmentación.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
from brainhub.chunking import Chunker, Chunk


# Pesos aislados para ajuste fino (Fase 3)
PESO_DENSIDAD = 0.40
PESO_COOCURRENCIA = 0.25
PESO_POLARIDAD = 0.20
PESO_COHERENCIA = 0.15

# Filtros
LONGITUD_MINIMA = 30
PATRONES_CODIGO = ['def ', 'class ', 'import ', '{', '}', 'lambda ', 'return ', 'if ', 'for ', 'while ']
PATRONES_METADATA = ['http://', 'https://', '[música]', 'timestamp', 'WEBVTT', '---', '...']


@dataclass
class CitaSemantica:
    """Cita rankeada por score semántico."""
    chunk_id: str
    texto: str
    score: float
    rank: int
    start_char: int
    end_char: int
    polaridad: float
    tier: str
    senal_densidad: float
    senal_coocurrencia: float
    senal_polaridad: float
    senal_coherencia: float

    def a_dict(self) -> Dict:
        """Serialización explícita."""
        return {
            'chunk_id': self.chunk_id,
            'texto': self.texto,
            'score': self.score,
            'rank': self.rank,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'polaridad': self.polaridad,
            'tier': self.tier,
            'senal_densidad': self.senal_densidad,
            'senal_coocurrencia': self.senal_coocurrencia,
            'senal_polaridad': self.senal_polaridad,
            'senal_coherencia': self.senal_coherencia,
        }


class ExtractorCitas:
    """Extrae citas rankeadas por score semántico usando Chunker."""

    def __init__(self, max_oraciones: int = 3):
        self.chunker = Chunker(estrategia='oraciones', max_oraciones=max_oraciones)

    def extraer(
        self,
        texto_limpio: str,
        video_id: str,
        terminos_clave: List[str],
        coocurrencias: List[Tuple[Tuple[str, str], int]],
        nicho: str,
        top_n: int = 10
    ) -> List[Dict]:
        """Extrae citas rankeadas por score semántico.

        Args:
            texto_limpio: Texto saneado del pipeline
            video_id: ID del video/documento
            terminos_clave: Lista de términos clave (ya normalizados)
            coocurrencias: Lista de ((t1, t2), freq) del pipeline
            nicho: Nicho detectado (ej. 'TECNOLOGIA')
            top_n: Número de citas a retornar

        Returns:
            Lista de dicts con citas rankeadas (top_n)
        """
        if not texto_limpio or not texto_limpio.strip():
            return []

        # 1. Chunkear
        chunks = self.chunker.chunkear(texto_limpio, video_id, tier=nicho)

        # 2. Calcular polaridad de cada chunk (necesario para scoring)
        try:
            from modulos.sentimiento_es import get_analizador
            analizador = get_analizador()
        except ImportError:
            analizador = None

        # 3. Filtrar y scorear
        candidatas = []
        for chunk in chunks:
            if not self._es_valido(chunk):
                continue

            # Calcular polaridad del chunk
            polaridad = 0.0
            if analizador:
                try:
                    sentimiento = analizador.analizar(chunk.texto)
                    polaridad = sentimiento.get('polaridad_norm', 0.0)
                except Exception:
                    pass

            # Calcular score
            s1 = self._senal_densidad(chunk, terminos_clave)
            s2 = self._senal_coocurrencia(chunk, coocurrencias)
            s3 = self._senal_polaridad(polaridad)
            s4 = self._senal_coherencia(chunk, nicho)

            score = (s1 * PESO_DENSIDAD) + (s2 * PESO_COOCURRENCIA) + \
                    (s3 * PESO_POLARIDAD) + (s4 * PESO_COHERENCIA)

            candidatas.append({
                'chunk': chunk,
                'polaridad': polaridad,
                'score': score,
                's1': s1,
                's2': s2,
                's3': s3,
                's4': s4,
            })

        # 3.5 Deduplicar por texto normalizado (fix bug #15)
        vistos = set()
        candidatas_unicas = []
        for c in candidatas:
            clave = c["chunk"].texto.strip().lower()
            if clave not in vistos:
                vistos.add(clave)
                candidatas_unicas.append(c)
        candidatas = candidatas_unicas

        # 4. Rankear
        candidatas.sort(key=lambda x: -x['score'])
        top = candidatas[:top_n]

        # 5. Construir output
        citas = []
        for rank, c in enumerate(top, 1):
            cita = CitaSemantica(
                chunk_id=c['chunk'].chunk_id,
                texto=c['chunk'].texto,
                score=round(c['score'], 2),
                rank=rank,
                start_char=c['chunk'].start_char,
                end_char=c['chunk'].end_char,
                polaridad=round(c['polaridad'], 3),
                tier=c['chunk'].tier,
                senal_densidad=round(c['s1'], 2),
                senal_coocurrencia=round(c['s2'], 2),
                senal_polaridad=round(c['s3'], 2),
                senal_coherencia=round(c['s4'], 2),
            )
            citas.append(cita.a_dict())

        return citas

    def _es_valido(self, chunk: Chunk) -> bool:
        """Aplica filtros de validez."""
        # Longitud mínima
        if len(chunk.texto) < LONGITUD_MINIMA:
            return False

        # Descartar código
        if any(p in chunk.texto for p in PATRONES_CODIGO):
            return False

        # Descartar metadata
        if any(p in chunk.texto for p in PATRONES_METADATA):
            return False

        return True

    def _senal_densidad(self, chunk: Chunk, terminos_clave: List[str]) -> float:
        """Señal 1: densidad de términos clave (0-100)."""
        if not terminos_clave:
            return 0.0

        texto_lower = chunk.texto.lower()
        presentes = sum(1 for t in terminos_clave if t.lower() in texto_lower)
        total = len(terminos_clave)

        return (presentes / total) * 100

    def _senal_coocurrencia(self, chunk: Chunk, coocurrencias: List[Tuple]) -> float:
        """Señal 2: co-ocurrencia temática (0-100)."""
        if not coocurrencias:
            return 0.0

        texto_lower = chunk.texto.lower()
        pares_presentes = sum(
            1 for (t1, t2), _ in coocurrencias
            if t1.lower() in texto_lower and t2.lower() in texto_lower
        )
        total_pares = len(coocurrencias)

        return (pares_presentes / total_pares) * 100

    def _senal_polaridad(self, polaridad: float) -> float:
        """Señal 3: polaridad extrema (0-100)."""
        return min(abs(polaridad), 1.0) * 100  # clamp

    def _senal_coherencia(self, chunk: Chunk, nicho: str) -> float:
        """Señal 4: coherencia con nicho (0-100)."""
        if chunk.tier == nicho:
            return 100.0
        elif chunk.tier == 'desconocido':
            return 50.0
        else:
            return 0.0
