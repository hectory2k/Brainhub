"""Orquestador de nichos reutilizando módulos existentes.

Reutiliza:
- nicho_multietiqueta.NichoMultietiqueta
- ponderacion_nichos.PonderacionNichos
- coherencia_nichos.CoherenciaNichos

NO reinventa. Solo orquesta.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional


RAIZ = Path(__file__).resolve().parent.parent.parent


class AnalizadorNichos:
    """Analiza texto y devuelve nichos con jerarquía."""

    def __init__(self):
        from modulos.nicho_multietiqueta import NichoMultietiqueta
        from modulos.ponderacion_nichos import PonderacionNichos
        from modulos.coherencia_nichos import CoherenciaNichos

        # Cargar diccionario externo
        ruta = RAIZ / "diccionario_nichos.json"
        with open(ruta) as f:
            dic_raw = json.load(f)
        diccionario = {n: info["terminos"] for n, info in dic_raw.items()}

        self.multi = NichoMultietiqueta()
        self.pond = PonderacionNichos(diccionario)
        self.coh = CoherenciaNichos()

    def es_transcript(self, archivo: str) -> bool:
        """Detecta si es transcripción por nombre del archivo."""
        if not archivo:
            return False
        nombre = os.path.basename(archivo).lower()
        return any(p in nombre for p in ["transcript", "subtitle", "caption"])

    def _filtrar_secundarios_validos(self, secundarios: Dict, scores: Dict) -> Dict:
        """Elimina secundarios con score 0."""
        resultado = {}
        for tipo, nicho in secundarios.items():
            if nicho and scores.get(nicho, 0) > 0:
                resultado[tipo] = nicho
        return resultado

    def analizar(self, texto: str, archivo: Optional[str] = None) -> Dict:
        """Análisis completo de nichos."""

        # 1. Multietiqueta (confianza + híbridos)
        multi = self.multi.analizar(texto)

        # 2. Ponderación (jerarquía)
        pond = self.pond.analizar(texto)

        # 3. Filtrar secundarios con score 0
        pond["secundarios"] = self._filtrar_secundarios_validos(
            pond.get("secundarios", {}),
            pond.get("scores", {}),
        )

        # 4. Coherencia (validar + corregir)
        jerarquia = pond
        coherente = self.coh.validar_jerarquia(jerarquia)
        if not coherente:
            jerarquia = self.coh.corregir_jerarquia(jerarquia, texto)
            coherente = self.coh.validar_jerarquia(jerarquia)

        # 5. Detectar si es habla
        es_habla = self.es_transcript(archivo)

        # 6. Armar lista de nichos para filtrar stopwords
        nichos = [pond.get("nicho_principal", "GENERAL")]
        for tipo, n in pond.get("secundarios", {}).items():
            if n and n not in nichos:
                nichos.append(n)
        if es_habla and "HABLA" not in nichos:
            nichos.append("HABLA")

        return {
            "principal": pond.get("nicho_principal", "GENERAL"),
            "multietiqueta": multi,
            "ponderado": pond,
            "jerarquia": jerarquia,
            "coherente": coherente,
            "es_habla": es_habla,
            "nichos_para_filtrar": nichos,
        }


_default = None


def get_analizador():
    """Singleton del analizador."""
    global _default
    if _default is None:
        _default = AnalizadorNichos()
    return _default


if __name__ == "__main__":
    analizador = get_analizador()
    texto = "El software de diagnóstico para pacientes usa normativa legal"
    resultado = analizador.analizar(texto)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
