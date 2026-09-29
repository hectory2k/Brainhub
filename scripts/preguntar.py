#!/data/data/com.termux/files/usr/bin/python3
"""
RAG sobre los resúmenes de BrainHub.

Uso:
    python3 scripts/preguntar.py "tu pregunta" [nicho]

Ejemplos:
    python3 scripts/preguntar.py "¿qué se dijo sobre plantas industriales?"
    python3 scripts/preguntar.py "temas de salud" SALUD
"""
import sys
import logging
import uuid
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "proyectos/nlp"))

from modulos.rag_simple import RAGSimple
from modulos.integrar_duckdb import consultar
from brainhub.llm.ollama_client import OllamaClient


import json

logger = logging.getLogger(__name__)


def cargar_documentos(nicho: str = None):
    """Carga resúmenes + términos agregados desde la DB."""
    sql = """
    WITH terminos_por_video AS (
        SELECT 
            video,
            string_agg(term || ' ' || term || ' ' || term, ' ') AS terminos_str
        FROM terminos_raw
        WHERE frequency >= 5
        GROUP BY video
    )
    SELECT 
        a.filename,
        a.resumen_llm,
        a.nicho,
        COALESCE(t.terminos_str, '') AS terminos_str
    FROM analysis a
    LEFT JOIN terminos_por_video t ON t.video = a.filename
    WHERE a.resumen_llm IS NOT NULL
    """
    if nicho:
        sql += f" AND a.nicho = '{nicho}'"
    
    rows = consultar(sql)
    docs = []
    meta = []
    for r in rows:
        if not r or len(r) < 3 or not r[1]:
            continue
        texto = r[1] + " ||SEP|| " + (r[3] or "")
        docs.append(texto)
        meta.append({"filename": r[0], "nicho": r[2]})
    return docs, meta


def preguntar(pregunta: str, nicho: str = None, top_k: int = 5, modelo: str = "brainhub-llama"):
    """Pipeline RAG completo."""
    trace_id = str(uuid.uuid4())[:8]
    t0 = time.time()
    logger.info(f"[{trace_id}] START pregunta={pregunta!r} nicho={nicho} top_k={top_k} modelo={modelo}")
    # 1. Cargar documentos
    docs, meta = cargar_documentos(nicho)
    logger.info(f"[{trace_id}] docs_cargados={len(docs)}")
    if not docs:
        logger.warning(f"[{trace_id}] ABORT sin documentos")
        return {"error": "Sin documentos", "respuesta": None, "resultados": []}
    
    print(f"📚 Documentos indexados: {len(docs)}")
    
    # 2. Indexar con BM25
    rag = RAGSimple()
    rag.indexar(docs)
    
    # 3. Buscar top_k
    resultados = rag.buscar(pregunta, top_k=top_k)
    top_score = resultados[0]["score"] if resultados else 0
    logger.info(f"[{trace_id}] bm25_resultados={len(resultados)} top_score={top_score}")
    print(f"🔍 Resultados BM25: {len(resultados)}")
    
    if not resultados:
        return {"error": "Sin resultados BM25", "respuesta": None, "resultados": []}
    
    # 4. Armar contexto
    partes = []
    for r in resultados:
        idx = r["posicion"]
        m = meta[idx]
        doc = r["documento"]
        
        # Separar resumen de términos con separador explícito
        if " ||SEP|| " in doc:
            resumen_limpio, terminos_str = doc.split(" ||SEP|| ", 1)
        else:
            resumen_limpio = doc
            terminos_str = ""
        
        # Extraer términos únicos (deduplicar)
        terminos_unicos = []
        if terminos_str:
            palabras = terminos_str.split()
            vista = set()
            for p_word in palabras:
                p_word_clean = p_word.strip(".,;:()[]{}\"'")
                if p_word_clean and p_word_clean not in vista and len(p_word_clean) > 3:
                    vista.add(p_word_clean)
                    terminos_unicos.append(p_word_clean)
            terminos_str = ", ".join(terminos_unicos[:15])
        
        partes.append(
            f"[{m['filename']}] ({m['nicho']})\n"
            f"Resumen: {resumen_limpio}\n"
            f"Términos clave: {terminos_str}"
        )
    contexto = "\n\n".join(partes)
    logger.info(f"[{trace_id}] contexto_chars={len(contexto)}")
    
    # 5. Responder con LLM
    print(f"🤖 Consultando {modelo}...")
    cliente = OllamaClient(model=modelo, num_predict=200)
    respuesta = cliente.responder_con_contexto(pregunta, contexto)
    
    elapsed = time.time() - t0
    logger.info(f"[{trace_id}] respuesta_chars={len(respuesta)} elapsed={elapsed:.2f}s")
    logger.info(f"[{trace_id}] DONE")

    return {"respuesta": respuesta, "resultados": resultados, "meta": meta}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        handlers=[
            logging.FileHandler(str(Path.home() / "proyectos/nlp/logs/rag.log")),
        ],
    )

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    pregunta = sys.argv[1]
    nicho = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"❓ {pregunta}")
    if nicho:
        print(f"🎯 Nicho: {nicho}")
    print()
    
    resultado = preguntar(pregunta, nicho)
    
    if resultado.get("error"):
        print(f"❌ {resultado['error']}")
        sys.exit(1)
    
    print("📄 Top documentos (BM25):")
    for r in resultado["resultados"][:3]:
        m = resultado["meta"][r["posicion"]]
        print(f"  [{r['posicion']}] score={r['score']:.3f}  {m['filename']}  ({m['nicho']})")
    
    print()
    print("💡 Respuesta:")
    print(resultado["respuesta"])
