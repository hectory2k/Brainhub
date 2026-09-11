"""Test de regresión: análisis de texto económico (informe_deudores).

Captura 3 bugs detectados en 2026-09-09 al procesar informe_deudores.txt:
1. Nicho mal clasificado: TECNOLOGIA (debería ser ECONOMIA o al menos FINANZAS)
2. "años" → "anos" (bug de normalización ñ) ← RESUELTO 2026-09-10
3. "deuda"/"deudores" fragmentados (falta lematización)

Estado actual (post fix de ñ):
- Ñ: resuelta (años se preserva)
- Nicho: mejoró de TECNOLOGIA → FINANZAS, pendiente ECONOMIA
- Lematización: pendiente
"""
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "regresion_economia"


def test_fixture_existe():
    """Verifica que el fixture está completo."""
    assert FIXTURES.exists(), f"Falta fixture: {FIXTURES}"
    assert (FIXTURES / "texto_original.txt").exists()
    assert (FIXTURES / "output_bugueado.csv").exists()
    assert (FIXTURES / "reporte_bugueado.md").exists()


def test_evidencia_bug_nicho():
    """Captura el bug #1: nicho mal clasificado."""
    reporte = (FIXTURES / "reporte_bugueado.md").read_text(encoding="utf-8")
    assert "TECNOLOGIA" in reporte, "Fixture no capturó bug de nicho TECNOLOGIA"


def test_evidencia_bug_enie():
    """Captura el bug #2: ñ rota en términos."""
    csv = (FIXTURES / "output_bugueado.csv").read_text(encoding="utf-8")
    assert "anos" in csv or "anos" in csv, "Fixture no capturó bug de ñ"


def test_evidencia_bug_lematizacion():
    """Captura el bug #3: deuda/deudores fragmentados."""
    csv = (FIXTURES / "output_bugueado.csv").read_text(encoding="utf-8")
    assert "deudores" in csv, "Fixture no capturó deudores"


def test_fix_enie_aplicado():
    """Verifica que el fix de ñ funciona en el normalizador actual."""
    import sys
    sys.path.insert(0, str(FIXTURES.parent.parent.parent))
    from brainhub.texto.normalizar import normalizar_preservando_enie

    texto = (FIXTURES / "texto_original.txt").read_text(encoding="utf-8")
    normalizado = normalizar_preservando_enie(texto)

    # El fix garantiza que "años" se preserva
    assert "años" in normalizado, "El fix de ñ no se está aplicando"


def test_fix_nicho_correcto():
    """Fix 2026-09-10: nicho debe ser FINANZAS (no TECNOLOGIA).
    
    Bug corregido: 'ia' matcheaba dentro de 'economia' por substring.
    Bug corregido: TECNOLOGIA ganaba empates por orden de dict.
    """
    import sys
    sys.path.insert(0, str(FIXTURES.parent.parent.parent))
    from modulos.detectar_nicho import detectar_nicho

    texto = (FIXTURES / "texto_original.txt").read_text(encoding="utf-8")
    nicho = detectar_nicho(texto)
    
    # El fix garantiza que NO sea TECNOLOGIA (era el bug)
    assert nicho != "TECNOLOGIA", f"Aún da TECNOLOGIA (bug de substring)"
    # Y que sea FINANZAS (o ECONOMIA si se agrega después)
    assert nicho in ("FINANZAS", "ECONOMIA"), f"Nicho inesperado: {nicho}"


def test_fix_lematizacion():
    """Fix 2026-09-11: deuda/deudores/deudoras bajo mismo lema.
    
    Verifica que el validador federado lematice correctamente.
    """
    import sys
    sys.path.insert(0, str(FIXTURES.parent.parent.parent))
    from modulos.validador_preguntas import ValidadorPreguntas
    
    v = ValidadorPreguntas()
    
    # Todas las variantes → mismo lema
    assert v.lematizar('deuda') == v.lematizar('deudas')
    assert v.lematizar('deudores') in ('deuda', 'deudor')
    assert v.lematizar('deudoras') in ('deuda', 'deudor')
    
    # Años (bug histórico)
    assert v.lematizar('años') == 'año' 
