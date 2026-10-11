"""Test de regresión: retorno temprano de AI_SAFETY.

Bug 2026-09-15: AI_SAFETY >= 3 retornaba sin evaluar CIBERSEGURIDAD.
Fix: eliminar retorno temprano.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.detectar_nicho import detectar_nicho, NICHO_KEYWORDS


def test_ai_safety_no_retorna_temprano():
    """Con AI_SAFETY bajo y CIBERSEGURIDAD alto, gana CIBERSEGURIDAD."""
    # Texto con 1 término de AI_SAFETY + muchos de CIBERSEGURIDAD
    texto = """
    La ciberseguridad industrial es crítica. Los ataques de malware
    y ransomware afectan las plantas. El firewall industrial debe
    proteger contra exploits y vulnerabilidades. Los hackers buscan
    brechas en las redes industriales. SCADA, ICS, OT son objetivos.
    """
    
    nicho = detectar_nicho(texto)
    assert nicho == "CIBERSEGURIDAD", f"Esperado CIBERSEGURIDAD, obtenido {nicho}"


def test_ai_safety_gana_cuando_corresponde():
    """Cuando AI_SAFETY es el tema principal, gana AI_SAFETY."""
    texto = """
    value alignment es fundamental. goal alignment también.
    recursive self-improvement, chain-of-thought, cot monitoring,
    machine intelligence, reasoning models, reasoning process,
    pretraining data, training distribution, supervision pressure.
    """
    
    nicho = detectar_nicho(texto)
    assert nicho == "AI_SAFETY", f"Esperado AI_SAFETY, obtenido {nicho}"


def test_kubernetes_es_tecnologia():
    """No-regresión: Kubernetes sigue siendo TECNOLOGIA."""
    texto = "kubernetes docker aws cloud python api software server"
    nicho = detectar_nicho(texto)
    assert nicho == "TECNOLOGIA", f"Esperado TECNOLOGIA, obtenido {nicho}"


def test_economia_es_finanzas():
    """No-regresión: texto económico sigue siendo FINANZAS."""
    texto = "mora deuda bcra inflación crédito bancario masa salarial"
    nicho = detectar_nicho(texto)
    assert nicho == "FINANZAS", f"Esperado FINANZAS, obtenido {nicho}"


def test_deportes_gana_con_market():
    """No-regresión Bug #9: video de combate no cae en FINANZAS por 'market'."""
    from modulos.detectar_nicho import detectar_nicho

    assert detectar_nicho('ufc fight market') == 'DEPORTES'
    assert detectar_nicho('boxing fight market') == 'DEPORTES'
    assert detectar_nicho('combat sports market') == 'DEPORTES'
    assert detectar_nicho('stock market investment') == 'FINANZAS'
