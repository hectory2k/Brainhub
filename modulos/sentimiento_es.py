#!/data/data/com.termux/files/usr/bin/python3
"""
Analisis de sentimiento en espanol con lexico local curado.

Reemplaza TextBlob (que solo analiza ingles) por un lexico espanol
construido a partir de:
- Curaduria manual medica (~210 terminos clave)
- SentiWordNet + OMW 1.4 + WordNet (para base general)
- Filtrado de ruido + expansion morfologica

Categorias:
- positivo: palabras con carga positiva
- negativo: palabras con carga negativa
- sesgo: terminos que indican cautela/evasion en papers
"""

import json
from pathlib import Path
from typing import Dict, Optional


class AnalizadorSentimientoES:
    """Analiza sentimiento + sesgo epistemico en textos espanoles."""

    def __init__(self, ruta_lexico: Optional[str] = None):
        if ruta_lexico is None:
            raiz = Path(__file__).resolve().parent.parent
            ruta_lexico = raiz / 'lexico_sentimiento_es.json'
        with open(ruta_lexico, encoding='utf-8') as f:
            self.lexico = json.load(f)
        self._cache = {}

    def _limpiar(self, palabra: str) -> str:
        """Elimina puntuacion de los bordes."""
        return palabra.strip('.,;:!?¡¿"\'()[]{}…—–«»')

    def analizar(self, texto: str) -> Dict:
        """
        Analiza un texto.

        Returns:
            {
                'polaridad': float,          # pos - neg, bruto
                'polaridad_norm': float,     # normalizado por matches
                'positivo': float,
                'negativo': float,
                'sesgo': float,              # sesgo epistemico
                'matches': int,              # palabras matcheadas
                'n_palabras': int,           # total palabras
                'densidad': float,           # matches / n_palabras
            }
        """
        palabras = texto.lower().split()
        pos = neg = sesgo = 0.0
        matches = 0
        n = len(palabras)

        for p in palabras:
            p_limpia = self._limpiar(p)
            if not p_limpia:
                continue
            if p_limpia in self.lexico:
                s = self.lexico[p_limpia]
                pos += s.get('pos', 0)
                neg += s.get('neg', 0)
                sesgo += s.get('sesgo', 0)
                matches += 1

        neto = pos - neg
        return {
            'polaridad': round(neto, 3),
            'polaridad_norm': round(neto / matches, 3) if matches > 0 else 0.0,
            'positivo': round(pos, 3),
            'negativo': round(neg, 3),
            'sesgo': round(sesgo, 3),
            'subjetividad': round(sesgo, 3),  # alias compat
            'matches': matches,
            'n_palabras': n,
            'densidad': round(matches / n, 3) if n > 0 else 0.0,
        }


# Singleton
_default: Optional[AnalizadorSentimientoES] = None


def get_analizador() -> AnalizadorSentimientoES:
    """Devuelve la instancia singleton del analizador."""
    global _default
    if _default is None:
        _default = AnalizadorSentimientoES()
    return _default


if __name__ == '__main__':
    a = get_analizador()
    casos = [
        'El tratamiento fue excelente y los pacientes estan felices',
        'Los efectos adversos fueron graves con alta mortalidad',
        'El equipo juega el partido manana',
        'El farmaco mostro eficacia significativa aunque con efectos adversos graves',
    ]
    for t in casos:
        r = a.analizar(t)
        print(f'  pol={r["polaridad"]:+6.2f}  sesgo={r["sesgo"]:.2f}  '
              f'm={r["matches"]}/{r["n_palabras"]}  {t[:60]}')
