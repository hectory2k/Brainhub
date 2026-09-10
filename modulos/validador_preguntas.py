#!/data/data/com.termux/files/usr/bin/python3
"""Validador de preguntas con federación de fuentes de conocimiento.

Filosofía:
    - Los términos genéricos NO deben anclar preguntas
    - Los términos técnicos SÍ pueden anclar preguntas
    - Cada fuente de conocimiento es un plugin intercambiable
    - Agregar fuente nueva = editar JSON, no código

Fuentes federadas:
    Genéricos (filtran):
        - stopwords.json (gramaticales: a, the, y, de)
        - terminos_vacios.json (NUEVO: word, paper, idea)
    Técnicos (validan):
        - diccionario_clinico.json
        - diccionario_nichos.json
        - MeSH (nicho SALUD)
        - Anatomía BodyParts3D (nicho SALUD)
        - detectar_nicho.NICHO_KEYWORDS
"""
import json
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

from modulos.stopwords_manager import get_stopwords_manager
from modulos.diccionario_clinico import DiccionarioClinico


RAIZ = Path(__file__).resolve().parent.parent


class FuenteTerminos:
    """Fuente de términos federada."""

    def __init__(
        self,
        nombre: str,
        loader: Callable[[], Set[str]],
        aplica_a_nichos: Optional[List[str]] = None,
    ):
        self.nombre = nombre
        self._loader = loader
        self.aplica_a_nichos = aplica_a_nichos
        self._terminos: Optional[Set[str]] = None

    def terminos(self) -> Set[str]:
        if self._terminos is None:
            try:
                self._terminos = {str(t).lower().strip() for t in self._loader()}
            except Exception as e:
                print(f"⚠️  Fuente '{self.nombre}' no disponible: {e}")
                self._terminos = set()
        return self._terminos

    def aplica(self, nicho: str) -> bool:
        return self.aplica_a_nichos is None or nicho in self.aplica_a_nichos

    def contiene(self, termino: str) -> bool:
        return termino.lower().strip() in self.terminos()


class ValidadorPreguntas:
    """Valida conceptos de preguntas federando múltiples fuentes."""

    def __init__(self, nicho: str = "GENERAL", lang: str = "es"):
        self.nicho = nicho
        self.lang = lang
        self._stopwords_manager = get_stopwords_manager()
        self._fuentes_genericos: List[FuenteTerminos] = []
        self._fuentes_tecnicos: List[FuenteTerminos] = []
        self._cargar_fuentes()

    def _cargar_fuentes(self):
        # ─── Genéricos ───
        self._fuentes_genericos.append(FuenteTerminos(
            nombre="stopwords_gramaticales",
            loader=lambda: self._stopwords_manager.get_stopwords(self.nicho, self.lang)
        ))
        self._fuentes_genericos.append(FuenteTerminos(
            nombre="stopwords_gramaticales_en",
            loader=lambda: self._stopwords_manager.get_stopwords(self.nicho, "en")
        ))
        self._fuentes_genericos.append(FuenteTerminos(
            nombre="terminos_vacios",
            loader=self._cargar_terminos_vacios
        ))

        # ─── Técnicos ───
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="diccionario_clinico",
            loader=self._cargar_clinico
        ))
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="tecnicos_generales",
            loader=self._cargar_tecnicos_generales
        ))
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="tecnicos_generales",
            loader=self._cargar_tecnicos_generales
        ))
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="nichos",
            loader=self._cargar_nichos
        ))
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="mesh",
            loader=self._cargar_mesh,
            aplica_a_nichos=["SALUD"]
        ))
        self._fuentes_tecnicos.append(FuenteTerminos(
            nombre="anatomia",
            loader=self._cargar_anatomia,
            aplica_a_nichos=["SALUD"]
        ))

    # ─── Loaders ───

    def _cargar_terminos_vacios(self) -> Set[str]:
        ruta = RAIZ / "terminos_vacios.json"
        if not ruta.exists():
            return set()
        data = json.loads(ruta.read_text(encoding="utf-8"))
        terminos = set()
        for lang in ("es", "en"):
            terminos.update(data.get(lang, []))
        return terminos

    def _cargar_clinico(self) -> Set[str]:
        dc = DiccionarioClinico()
        terminos = set(dc._data.keys())
        for info in dc._data.values():
            terminos.update(info.get("sinonimos", []))
        return terminos

    def _cargar_tecnicos_generales(self) -> Set[str]:
        ruta = RAIZ / "terminos_tecnicos.json"
        if not ruta.exists():
            return set()
        data = json.loads(ruta.read_text(encoding="utf-8"))
        terminos = set()
        for lang in ("es", "en"):
            terminos.update(data.get(lang, []))
        return terminos

    def _cargar_tecnicos_generales(self) -> Set[str]:
        ruta = RAIZ / "terminos_tecnicos.json"
        if not ruta.exists():
            return set()
        data = json.loads(ruta.read_text(encoding="utf-8"))
        terminos = set()
        for lang in ("es", "en"):
            terminos.update(data.get(lang, []))
        return terminos

    def _cargar_nichos(self) -> Set[str]:
        try:
            from modulos.detectar_nicho import NICHO_KEYWORDS
            return {t for terms in NICHO_KEYWORDS.values() for t in terms}
        except Exception:
            return set()

    def _cargar_mesh(self) -> Set[str]:
        try:
            from modulos.mesh_parquet import MeSHParquet
            mp = MeSHParquet()
            if hasattr(mp, "listar_terminos"):
                return set(mp.listar_terminos())
            if hasattr(mp, "_df") and mp._df is not None:
                return set(mp._df.iloc[:, 0].astype(str))
        except Exception:
            pass
        return set()

    def _cargar_anatomia(self) -> Set[str]:
        try:
            from modulos.anatomia_parquet import AnatomiaParquet
            ap = AnatomiaParquet()
            if hasattr(ap, "listar_terminos"):
                return set(ap.listar_terminos())
            if hasattr(ap, "_df") and ap._df is not None:
                for col in ("nombre", "name", "term", "termino"):
                    if col in ap._df.columns:
                        return set(ap._df[col].astype(str))
        except Exception:
            pass
        return set()

    # ─── API pública ───

    def es_generico(self, termino: str) -> bool:
        if not termino:
            return True
        t = termino.strip().lower()
        if len(t) < 3:
            return True
        return any(
            f.contiene(t)
            for f in self._fuentes_genericos
            if f.aplica(self.nicho)
        )

    def es_tecnico(self, termino: str) -> bool:
        if not termino:
            return False
        t_original = termino.strip()
        t = t_original.lower()
        # 1. Fuentes federadas
        if any(
            f.contiene(t)
            for f in self._fuentes_tecnicos
            if f.aplica(self.nicho)
        ):
            return True
        # 2. Heurística: palabra compuesta con guion
        if "-" in t and len(t) > 5:
            return True
        # 3. Heurística: siglas (2-6 letras mayúsculas)
        #    FIX: verificar sobre el original, no sobre .lower()
        if t_original.isupper() and 2 <= len(t_original) <= 6:
            return True
        return False

    def validar_conceptos(self, conceptos: List[str]) -> Tuple[bool, str]:
        if not conceptos:
            return False, "sin_conceptos"
        norm = [c.strip().lower() for c in conceptos if c and c.strip()]
        if not norm:
            return False, "sin_conceptos"
        no_genericos = [c for c in norm if not self.es_generico(c)]
        if not no_genericos:
            return False, "solo_terminos_genericos"
        tecnicos = [c for c in no_genericos if self.es_tecnico(c)]
        if not tecnicos:
            return False, "sin_concepto_tecnico"
        return True, "valida"

    def filtrar_terminos(self, terminos: List[str], min_tecnicos: int = 1) -> List[str]:
        if not terminos:
            return []
        no_genericos = [t for t in terminos if not self.es_generico(t)]
        tecnicos = [t for t in no_genericos if self.es_tecnico(t)]
        if len(tecnicos) >= min_tecnicos:
            return no_genericos
        return no_genericos if no_genericos else terminos

    def stats(self) -> dict:
        return {
            "nicho": self.nicho,
            "genericos": {
                f.nombre: len(f.terminos())
                for f in self._fuentes_genericos
                if f.aplica(self.nicho)
            },
            "tecnicos": {
                f.nombre: len(f.terminos())
                for f in self._fuentes_tecnicos
                if f.aplica(self.nicho)
            },
        }


_default: Optional[ValidadorPreguntas] = None

def get_validador(nicho: str = "GENERAL", lang: str = "es") -> ValidadorPreguntas:
    global _default
    if _default is None or _default.nicho != nicho:
        _default = ValidadorPreguntas(nicho, lang)
    return _default


if __name__ == "__main__":
    v = ValidadorPreguntas()
    print("📊 Fuentes federadas:")
    print(json.dumps(v.stats(), indent=2, ensure_ascii=False))
    print()
    print("=== Casos inválidos ===")
    for conceptos in [["word", "paper"], ["idea", "better"], ["cosa", "mejor"]]:
        print(f"  {conceptos} → {v.validar_conceptos(conceptos)}")
    print()
    print("=== Casos válidos ===")
    for conceptos in [["transformer", "attention"], ["self-attention", "token"]]:
        print(f"  {conceptos} → {v.validar_conceptos(conceptos)}")
