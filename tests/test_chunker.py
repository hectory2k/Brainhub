"""Tests del Chunker vitaminado."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brainhub.chunking import Chunk, Chunker


def test_texto_vacio():
    c = Chunker()
    assert c.chunkear("", "vid1") == []
    assert c.chunkear("   \n  ", "vid1") == []


def test_una_oracion():
    c = Chunker()
    chunks = c.chunkear("Hola mundo.", "vid1")
    assert len(chunks) == 1
    assert chunks[0].n_oraciones == 1
    assert chunks[0].texto == "Hola mundo."
    assert chunks[0].posicion == 0
    assert chunks[0].estrategia == 'oraciones'


def test_grupos_de_diez():
    c = Chunker()
    texto = ' '.join(f"Oración número {i}." for i in range(25))
    chunks = c.chunkear(texto, "vid1")
    assert len(chunks) == 3
    assert chunks[0].n_oraciones == 10
    assert chunks[1].n_oraciones == 10
    assert chunks[2].n_oraciones == 5


def test_idempotencia():
    c = Chunker()
    texto = "Primera. Segunda. Tercera."
    chunks_a = c.chunkear(texto, "vid1")
    chunks_b = c.chunkear(texto, "vid1")
    ids_a = [ch.chunk_id for ch in chunks_a]
    ids_b = [ch.chunk_id for ch in chunks_b]
    assert ids_a == ids_b


def test_a_dict_json_serializable():
    c = Chunker()
    chunks = c.chunkear("Primera. Segunda.", "vid1")
    d = [ch.a_dict() for ch in chunks]
    json_str = json.dumps(d)
    assert json_str
    d2 = json.loads(json_str)
    assert d2[0]['video'] == 'vid1'
    assert d2[0]['estrategia'] == 'oraciones'


def test_start_end_char_consistentes():
    c = Chunker()
    texto = "Primera oración. Segunda oración. Tercera oración."
    chunks = c.chunkear(texto, "vid1")
    for ch in chunks:
        assert ch.texto in texto
        assert 0 <= ch.start_char < len(texto)
        assert ch.start_char < ch.end_char <= len(texto)


def test_estrategia_parrafos():
    c = Chunker(estrategia='parrafos', max_parrafos=2)
    texto = "Párrafo uno.\n\nPárrafo dos.\n\nPárrafo tres.\n\nPárrafo cuatro."
    chunks = c.chunkear(texto, "vid1")
    assert len(chunks) == 2
    assert chunks[0].estrategia == 'parrafos'
    assert chunks[0].n_oraciones == 0


def test_estrategia_caracteres():
    c = Chunker(estrategia='caracteres', max_chars=20, overlap=0)
    texto = "a" * 100
    chunks = c.chunkear(texto, "vid1")
    assert len(chunks) == 5
    assert chunks[0].estrategia == 'caracteres'
    assert chunks[0].end_char - chunks[0].start_char == 20


def test_tokenizer_invalido():
    try:
        Chunker(tokenizer='no_existe')
        assert False, "debería haber lanzado ValueError"
    except ValueError as e:
        assert 'tokenizer invalido' in str(e)


def test_estrategia_invalida():
    c = Chunker(estrategia='no_existe')
    try:
        c.chunkear("texto.", "vid1")
        assert False, "debería haber lanzado ValueError"
    except ValueError as e:
        assert 'estrategia invalida' in str(e)


def test_a_dict_serializable_para_integracion():
    """Verifica que el shape de salida sirve para datos_analisis['chunks']."""
    c = Chunker(estrategia='oraciones', max_oraciones=10)
    texto = ' '.join(f"Frase {i} del video sobre trauma." for i in range(25))
    chunks = c.chunkear(texto, "video_test", tier="SALUD")
    serializados = [ch.a_dict() for ch in chunks]

    assert len(serializados) == 3
    assert all(ch['tier'] == 'SALUD' for ch in serializados)
    assert all(ch['video'] == 'video_test' for ch in serializados)
    assert all('chunk_id' in ch and 'texto' in ch for ch in serializados)

    # Sobrevive ida y vuelta por JSON (como en el pipeline real)
    json_str = json.dumps(serializados, ensure_ascii=False)
    reconstruido = json.loads(json_str)
    assert reconstruido == serializados
