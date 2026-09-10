#!/data/data/com.termux/files/usr/bin/python3
"""Tests del validador federado de preguntas.

Verifica que:
- Los términos genéricos (word, paper, idea) son rechazados
- Los términos técnicos (transformer, self-attention) son aceptados
- La federación de fuentes funciona correctamente
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos.validador_preguntas import (
    ValidadorPreguntas,
    get_validador,
)


# ─── Casos de validar_conceptos ───

CASOS_INVALIDOS = [
    pytest.param({"word", "paper"}, (False, "solo_terminos_genericos"), id="word-paper"),
    pytest.param({"idea", "better"}, (False, "solo_terminos_genericos"), id="idea-better"),
    pytest.param({"paper", "researchers"}, (False, "solo_terminos_genericos"), id="paper-researchers"),
    pytest.param({"cosa", "mejor"}, (False, "solo_terminos_genericos"), id="es-genericos"),
    pytest.param({"palabra", "estudio"}, (False, "solo_terminos_genericos"), id="es-palabra-estudio"),
    pytest.param({"word"}, (False, "solo_terminos_genericos"), id="solo-word"),
    pytest.param(set(), (False, "sin_conceptos"), id="vacio"),
    pytest.param({"x"}, (False, "solo_terminos_genericos"), id="muy-corto"),
]

CASOS_VALIDOS = [
    pytest.param({"transformer", "attention"}, (True, "valida"), id="transformer-attention"),
    pytest.param({"self-attention", "token"}, (True, "valida"), id="self-attention-token"),
    pytest.param({"transformer", "paper"}, (True, "valida"), id="transformer-con-generico"),
    pytest.param({"deuda", "morosidad"}, (True, "valida"), id="economia-terminos"),
    pytest.param({"paciente", "diagnostico"}, (True, "valida"), id="salud-clinico"),
]


@pytest.mark.parametrize("conceptos, esperado", CASOS_INVALIDOS)
def test_rechaza_conceptos_genericos(conceptos, esperado):
    v = ValidadorPreguntas()
    assert v.validar_conceptos(conceptos) == esperado


@pytest.mark.parametrize("conceptos, esperado", CASOS_VALIDOS)
def test_acepta_conceptos_tecnicos(conceptos, esperado):
    v = ValidadorPreguntas()
    assert v.validar_conceptos(conceptos) == esperado


# ─── Casos de es_generico ───

@pytest.mark.parametrize("termino", [
    "word", "paper", "idea", "thing",
    "cosa", "mejor", "estudio", "palabra",
    "PAPER", "Word", "IDEA",
])
def test_detecta_genericos(termino):
    v = ValidadorPreguntas()
    assert v.es_generico(termino), f"{termino!r} debería ser genérico"


@pytest.mark.parametrize("termino", [
    "transformer", "self-attention", "mora", "BCRA",
    "deuda", "paciente",
])
def test_no_detecta_genericos(termino):
    v = ValidadorPreguntas()
    assert not v.es_generico(termino), f"{termino!r} NO debería ser genérico"


# ─── Casos de es_tecnico ───

@pytest.mark.parametrize("termino", [
    "transformer", "self-attention", "token",
    "BCRA", "SRE",
])
def test_detecta_tecnicos(termino):
    v = ValidadorPreguntas()
    assert v.es_tecnico(termino), f"{termino!r} debería ser técnico"


@pytest.mark.parametrize("termino", [
    "paper", "word", "cosa", "mejor",
])
def test_no_detecta_tecnicos(termino):
    v = ValidadorPreguntas()
    assert not v.es_tecnico(termino), f"{termino!r} NO debería ser técnico"


# ─── Casos de filtrar_terminos ───

def test_filtra_genericos():
    v = ValidadorPreguntas()
    terminos = ["word", "paper", "transformer", "attention", "idea"]
    filtrados = v.filtrar_terminos(terminos)
    assert "word" not in filtrados
    assert "paper" not in filtrados
    assert "idea" not in filtrados
    assert "transformer" in filtrados
    assert "attention" in filtrados


def test_filtro_preserva_orden():
    v = ValidadorPreguntas()
    terminos = ["transformer", "word", "attention", "paper", "self-attention"]
    filtrados = v.filtrar_terminos(terminos)
    # Orden original preservado
    assert filtrados == ["transformer", "attention", "self-attention"]


def test_filtro_vacio():
    v = ValidadorPreguntas()
    assert v.filtrar_terminos([]) == []


# ─── Casos de federación ───

def test_federacion_carga_fuentes():
    v = ValidadorPreguntas()
    stats = v.stats()
    assert stats["nicho"] == "GENERAL"
    assert stats["genericos"]["stopwords_gramaticales"] > 100
    assert stats["genericos"]["terminos_vacios"] > 100
    assert stats["tecnicos"]["diccionario_clinico"] > 0
    assert stats["tecnicos"]["nichos"] > 0


def test_federacion_por_nicho():
    """SALUD carga MeSH y anatomía."""
    v = ValidadorPreguntas(nicho="SALUD")
    stats = v.stats()
    assert "mesh" in stats["tecnicos"]
    assert "anatomia" in stats["tecnicos"]


def test_singleton():
    v1 = get_validador("GENERAL")
    v2 = get_validador("GENERAL")
    assert v1 is v2
