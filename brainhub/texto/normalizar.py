"""Normalización de texto preservando ñ/Ñ.

Bug histórico: 'años' → 'anos' por NFD + eliminación de Mn.
Solución: proteger ñ/Ñ con placeholders únicos ANTES de NFD.

Ver: guardias/normalizacion.sh (22 casos verificados)
"""
import re
import unicodedata

_PLACEHOLDER_LOWER = "XYZPLACEHOLDERLOWERXYZ"
_PLACEHOLDER_UPPER = "XYZPLACEHOLDERUPPERXYZ"


def normalizar_preservando_enie(texto: str) -> str:
    """
    Normaliza acentos pero PRESERVA ñ/Ñ.
    
    Ejemplos:
        "años"    → "años"    (ñ preservada)
        "acción"  → "accion"  (acento cae)
        "AÑO"     → "AÑO"     (Ñ mayúscula preservada)
        "ñandú"   → "ñandu"   (tilde cae, ñ queda)
        "café"    → "cafe"    (acento cae)
    
    Args:
        texto: Texto a normalizar
    
    Returns:
        Texto normalizado sin acentos excepto ñ/Ñ
    """
    if not texto:
        return texto
    
    # 1. Proteger ñ/Ñ con placeholders distintos
    texto = texto.replace("ñ", _PLACEHOLDER_LOWER)
    texto = texto.replace("Ñ", _PLACEHOLDER_UPPER)
    
    # 2. NFD descompone ó → o + ´ (marca combinante)
    texto = unicodedata.normalize("NFD", texto)
    
    # 3. Eliminar marcas de acento (Mn = Mark, nonspacing)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    
    # 4. Restaurar ñ/Ñ
    texto = texto.replace(_PLACEHOLDER_LOWER, "ñ")
    texto = texto.replace(_PLACEHOLDER_UPPER, "Ñ")
    
    # 5. Normalizar espacios
    texto = re.sub(r"\s+", " ", texto).strip()
    
    return texto


def normalizar_termino(termino: str) -> str:
    """Normaliza un término individual (alias corto)."""
    return normalizar_preservando_enie(termino)


if __name__ == "__main__":
    # Test rápido
    casos = {
        "años": "años",
        "acción": "accion",
        "AÑO": "AÑO",
        "ñandú": "ñandu",
        "café": "cafe",
        "España": "España",
    }
    for entrada, esperado in casos.items():
        resultado = normalizar_preservando_enie(entrada)
        estado = "✅" if resultado == esperado else "❌"
        print(f"{estado} {entrada!r:12} → {resultado!r:12} (esperado {esperado!r})")
