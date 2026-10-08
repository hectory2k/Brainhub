"""Tests del Extractor de Citas Semánticas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brainhub.citas import ExtractorCitas


def test_texto_vacio():
    """Texto vacío retorna lista vacía."""
    extractor = ExtractorCitas()
    citas = extractor.extraer("", "vid1", [], [], "GENERAL")
    assert citas == []


def test_sin_terminos_clave():
    """Sin términos clave, todas las citas tienen score bajo."""
    extractor = ExtractorCitas()
    texto = "Esta es una oración de prueba. Otra oración más. Y una tercera."
    citas = extractor.extraer(texto, "vid1", [], [], "GENERAL", top_n=5)
    
    assert len(citas) > 0
    # Sin términos clave, señal_densidad debe ser 0
    for cita in citas:
        assert cita['senal_densidad'] == 0.0


def test_cita_con_alta_densidad():
    """Cita con muchos términos clave tiene score alto en densidad."""
    extractor = ExtractorCitas()
    texto = "RAG es retrieval augmented generation. Los embeddings vectoriales son clave. El prompt engineering guía al LLM."
    terminos = ['rag', 'retrieval', 'embedding', 'vector', 'llm', 'prompt']
    
    citas = extractor.extraer(texto, "vid1", terminos, [], "TECNOLOGIA", top_n=5)
    
    assert len(citas) > 0
    # La primera cita debe tener alta densidad
    assert citas[0]['senal_densidad'] > 50.0


def test_cita_con_coocurrencia():
    """Cita con pares co-ocurrentes tiene score en co-ocurrencia."""
    extractor = ExtractorCitas()
    texto = "RAG y retrieval son conceptos relacionados. Embedding y vector también."
    coocurrencias = [(('rag', 'retrieval'), 5), (('embedding', 'vector'), 3)]
    
    citas = extractor.extraer(texto, "vid1", [], coocurrencias, "TECNOLOGIA", top_n=5)
    
    assert len(citas) > 0
    # Al menos una cita debe tener señal_coocurrencia > 0
    assert any(c['senal_coocurrencia'] > 0 for c in citas)


def test_filtro_codigo():
    """Chunks con código son descartados."""
    extractor = ExtractorCitas()
    texto = "Esta es una cita válida. def funcion(): return 42. Otra cita válida."
    
    citas = extractor.extraer(texto, "vid1", [], [], "GENERAL", top_n=10)
    
    # El chunk con 'def' debe ser descartado
    for cita in citas:
        assert 'def ' not in cita['texto']


def test_filtro_metadata():
    """Chunks con metadata son descartados."""
    extractor = ExtractorCitas()
    texto = "Cita válida uno. Cita válida dos. Visita https://ejemplo.com para más info."
    
    citas = extractor.extraer(texto, "vid1", [], [], "GENERAL", top_n=10)
    
    # El chunk con 'https://' debe ser descartado
    for cita in citas:
        assert 'https://' not in cita['texto']


def test_coherencia_con_nicho():
    """Cita con tier=nicho tiene señal_coherencia=100."""
    extractor = ExtractorCitas()
    texto = "RAG es una técnica de retrieval. Los embeddings son vectores."
    
    citas = extractor.extraer(texto, "vid1", [], [], "TECNOLOGIA", top_n=5)
    
    assert len(citas) > 0
    # Todas las citas deben tener tier=TECNOLOGIA (pasado por el chunker)
    for cita in citas:
        assert cita['tier'] == 'TECNOLOGIA'
        assert cita['senal_coherencia'] == 100.0


def test_ranking_por_score():
    """Citas están ordenadas por score descendente."""
    extractor = ExtractorCitas()
    texto = "RAG retrieval embedding vector LLM prompt. Otra oración sin términos. Más texto relevante con RAG y LLM."
    terminos = ['rag', 'llm']
    
    citas = extractor.extraer(texto, "vid1", terminos, [], "TECNOLOGIA", top_n=10)
    
    if len(citas) >= 2:
        # Verificar que están ordenadas por score
        scores = [c['score'] for c in citas]
        assert scores == sorted(scores, reverse=True)
        
        # Verificar que rank es consecutivo
        ranks = [c['rank'] for c in citas]
        assert ranks == list(range(1, len(citas) + 1))


def test_top_n():
    """top_n limita el número de citas retornadas."""
    extractor = ExtractorCitas()
    texto = " ".join([f"Oración número {i}." for i in range(30)])
    
    citas = extractor.extraer(texto, "vid1", [], [], "GENERAL", top_n=3)
    
    assert len(citas) <= 3


def test_a_dict_serializable():
    """Citas son serializables a dict."""
    extractor = ExtractorCitas()
    texto = "RAG es retrieval augmented generation. Los embeddings son vectores."
    
    citas = extractor.extraer(texto, "vid1", ['rag'], [], "TECNOLOGIA", top_n=5)
    
    assert len(citas) > 0
    # Verificar estructura del dict
    cita = citas[0]
    assert 'chunk_id' in cita
    assert 'texto' in cita
    assert 'score' in cita
    assert 'rank' in cita
    assert 'senal_densidad' in cita
