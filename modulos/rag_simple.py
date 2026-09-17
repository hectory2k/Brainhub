#!/data/data/com.termux/files/usr/bin/python3
"""
RAG simple para BrainHub.
Búsqueda semántica con TF-IDF + ranking BM25.
Sin LLMs, sin vector DB externa.
"""

import math
from collections import Counter
from typing import List, Dict, Tuple


class RAGSimple:
    """Retrieval Augmented Generation simple."""
    
    def __init__(self):
        self.documentos = []
        self.idf = {}
        self.doc_freq = Counter()
        self.total_docs = 0
    
    def indexar(self, documentos: List[str]):
        """Indexa documentos y calcula IDF."""
        self.documentos = documentos
        self.total_docs = len(documentos)
        
        # Calcular document frequency
        for doc in documentos:
            tokens = set(self._tokenizar(doc))
            for token in tokens:
                self.doc_freq[token] += 1
        
        # Calcular IDF
        for token, freq in self.doc_freq.items():
            self.idf[token] = math.log((1 + self.total_docs) / (1 + freq)) + 1
    
    def _tokenizar(self, texto: str) -> List[str]:
        """Tokeniza texto simple con normalización de plurales."""
        tokens = []
        for t in texto.lower().split():
            # Quitar puntuación
            t = t.strip(".,;:!?¡¿()[]{}\"'")
            if len(t) < 2:
                continue
            # Singularizar plurales simples (español + inglés)
            if t.endswith("es") and len(t) > 4:
                t = t[:-2]
            elif t.endswith("s") and len(t) > 3:
                t = t[:-1]
            tokens.append(t)
        return tokens
    
    def _tf(self, termino: str, doc: str) -> float:
        """Frecuencia de término en documento."""
        tokens = self._tokenizar(doc)
        count = tokens.count(termino)
        if count == 0:
            return 0
        return 1 + math.log(count)
    
    def _bm25_score(self, consulta: str, doc: str, k1: float = 1.5, b: float = 0.75) -> float:
        """Calcula BM25 score."""
        doc_tokens = self._tokenizar(doc)
        doc_len = len(doc_tokens)
        avg_len = sum(len(self._tokenizar(d)) for d in self.documentos) / max(self.total_docs, 1)
        
        score = 0
        for termino in self._tokenizar(consulta):
            if termino not in self.idf:
                continue
            
            tf = self._tf(termino, doc)
            idf = self.idf[termino]
            
            # BM25 formula
            numerador = tf * (k1 + 1)
            denominador = tf + k1 * (1 - b + b * doc_len / avg_len)
            score += idf * numerador / denominador
        
        return score
    
    def buscar(self, consulta: str, top_k: int = 5) -> List[Dict]:
        """
        Busca documentos relevantes por BM25.
        
        Returns:
            Lista de {'documento': '...', 'score': 0.85, 'posicion': 1}
        """
        resultados = []
        
        for i, doc in enumerate(self.documentos):
            score = self._bm25_score(consulta, doc)
            if score > 0:
                resultados.append({
                    'documento': doc[:200],
                    'score': round(score, 3),
                    'posicion': i
                })
        
        # Ordenar por score
        resultados.sort(key=lambda x: x['score'], reverse=True)
        return resultados[:top_k]
    
    def evaluar_recall(self, consulta: str, relevantes: List[int], top_k: int = 5) -> float:
        """
        Calcula Recall@K.
        
        Args:
            consulta: Consulta de búsqueda
            relevantes: Lista de posiciones relevantes
            top_k: K para evaluar
        """
        resultados = self.buscar(consulta, top_k)
        posiciones_retornadas = {r['posicion'] for r in resultados}
        relevantes_set = set(relevantes)
        
        if not relevantes_set:
            return 0.0
        
        recuperados = posiciones_retornadas & relevantes_set
        return len(recuperados) / len(relevantes_set)
    
    def evaluar_mrr(self, consulta: str, relevantes: List[int], top_k: int = 5) -> float:
        """Calcula Mean Reciprocal Rank."""
        resultados = self.buscar(consulta, top_k)
        
        for i, resultado in enumerate(resultados, 1):
            if resultado['posicion'] in relevantes:
                return 1.0 / i
        
        return 0.0


if __name__ == '__main__':
    # Test con documentos de ejemplo
    documentos = [
        "RAG retrieval augmented generation vector database",
        "machine learning deep learning neural networks",
        "retrieval query vector index evidence",
        "python programacion codigo datos",
        "salud paciente diagnostico tratamiento"
    ]
    
    rag = RAGSimple()
    rag.indexar(documentos)
    
    print("🔍 Búsqueda: 'retrieval vector'")
    resultados = rag.buscar('retrieval vector', top_k=3)
    for i, r in enumerate(resultados, 1):
        print(f"   {i}. {r['documento'][:50]}... (score: {r['score']})")
    
    print(f"\n📊 Recall@3: {rag.evaluar_recall('retrieval vector', [0, 2], 3)}")
    print(f"📊 MRR: {rag.evaluar_mrr('retrieval vector', [0, 2], 3)}")
