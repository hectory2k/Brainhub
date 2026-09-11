"""Exploración con K-Means casero (sin sklearn).

Reutiliza:
- ValidadorPreguntas (federación de 5 fuentes)
  - es_generico() filtra stopwords
  - es_tecnico() mantiene técnicos
  - lematizar() agrupa variantes
- detectar_nicho (para comparar clusters vs nichos)

Filosofía: no reinventar. Los módulos ya existen.
"""
import json
import subprocess
import os
import sys
from pathlib import Path
from collections import Counter
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ))

DB_PATH = os.environ.get(
    'BRAINHUB_DB',
    str(RAIZ / "data" / "analisis_consolidado.duckdb")
)


def cargar_documentos():
    """Carga términos por documento desde DuckDB.
    
    FIX 2026-09-11: 
    - Deduplicar (los análisis se ejecutaron múltiples veces e insertaron
      filas duplicadas sin borrar las anteriores).
    - Usar MAX en vez de SUM/AVG para evitar inflación artificial.
    
    El bug afecta al 54% de las filas (1,062 de 1,951).
    """
    sql = """
    SELECT video as doc, term, MAX(frequency) as freq
    FROM terminos_raw
    GROUP BY video, term
    ORDER BY doc, freq DESC
    """
    result = subprocess.run(
        ['duckdb', DB_PATH, '-json', '-c', sql],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def vectorizar_con_validador(filas, usar_lematizacion=True):
    """Vectoriza usando ValidadorPreguntas federado.
    
    Filtra:
    - es_generico() → términos vacíos (word, paper, the, that)
    
    Mantiene:
    - es_tecnico() → términos técnicos (transformer, mora, BCRA)
    
    Opcionalmente lematiza para agrupar variantes.
    """
    # 1. Cargar validador federado (5 fuentes)
    from modulos.validador_preguntas import ValidadorPreguntas
    validador = ValidadorPreguntas()
    stats = validador.stats()
    
    n_gen = sum(stats.get('genericos', {}).values())
    n_tec = sum(stats.get('tecnicos', {}).values())
    print(f"   🌐 Validador federado: {n_gen} genéricos, {n_tec} técnicos")
    
    # 2. Filtrar + agrupar por lema
    docs = {}
    descartados_genericos = 0
    descartados_no_tecnicos = 0
    lematizados = 0
    
    for fila in filas:
        doc = fila['doc']
        term = fila['term']
        freq = fila['freq']
        
        # 2a. Filtrar genéricos (stopwords, términos vacíos)
        if validador.es_generico(term):
            descartados_genericos += 1
            continue
        
        # 2b. Solo mantener técnicos
        if not validador.es_tecnico(term):
            descartados_no_tecnicos += 1
            continue
        
        # 2c. Lematizar (agrupa variantes)
        term_procesado = term
        if usar_lematizacion:
            term_lema = validador.lematizar(term)
            if term_lema != term:
                lematizados += 1
            term_procesado = term_lema
        
        docs.setdefault(doc, Counter())[term_procesado] = (
            docs.setdefault(doc, Counter()).get(term_procesado, 0) + int(freq)
        )
    
    print(f"   🧹 Filtrados: {descartados_genericos} genéricos, {descartados_no_tecnicos} no-técnicos")
    if usar_lematizacion and lematizados:
        print(f"   🔤 Lematizados: {lematizados} términos agrupados")
    
    # 3. Filtrar docs vacíos
    docs = {d: t for d, t in docs.items() if t}
    
    if not docs:
        return [], np.array([]), {}
    
    # 4. Construir vocabulario
    doc_ids = list(docs.keys())
    n_docs = len(doc_ids)
    
    vocab = {}
    df = Counter()
    for d in docs.values():
        for term in d:
            df[term] += 1
            if term not in vocab:
                vocab[term] = len(vocab)
    
    # 5. Matriz TF-IDF
    n_terms = len(vocab)
    X = np.zeros((n_docs, n_terms))
    
    for i, doc_id in enumerate(doc_ids):
        for term, freq in docs[doc_id].items():
            j = vocab[term]
            tf = 1 + np.log(freq)
            idf = np.log(n_docs / (1 + df[term]))
            X[i, j] = tf * idf
    
    # 6. Normalizar L2
    normas = np.linalg.norm(X, axis=1, keepdims=True)
    normas[normas == 0] = 1
    X = X / normas
    
    # 7. Invertir vocab para lookup
    inv_vocab = {v: k for k, v in vocab.items()}
    
    return doc_ids, X, inv_vocab


def kmeans_casero(X, k, max_iter=100, seed=42):
    """K-Means implementado con numpy."""
    np.random.seed(seed)
    n_docs = X.shape[0]
    
    idx = np.random.choice(n_docs, k, replace=False)
    centroides = X[idx].copy()
    
    labels_prev = None
    iter_final = 0
    for it in range(max_iter):
        distancias = np.linalg.norm(
            X[:, None, :] - centroides[None, :, :], axis=2
        )
        labels = np.argmin(distancias, axis=1)
        
        if labels_prev is not None and np.array_equal(labels, labels_prev):
            iter_final = it + 1
            break
        labels_prev = labels.copy()
        
        for i in range(k):
            mask = labels == i
            if mask.any():
                centroides[i] = X[mask].mean(axis=0)
    
    inercia = sum(
        np.linalg.norm(X[j] - centroides[labels[j]])**2
        for j in range(n_docs)
    )
    
    return labels, centroides, inercia, iter_final


def silhouette_casero(X, labels):
    """Silhouette score."""
    n = len(X)
    if len(set(labels)) < 2:
        return 0.0
    
    dist = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    
    sil = []
    for i in range(n):
        mismo = (labels == labels[i])
        mismo[i] = False
        a = dist[i][mismo].mean() if mismo.any() else 0
        
        b = float('inf')
        for c in set(labels):
            if c == labels[i]:
                continue
            otros = (labels == c)
            if otros.any():
                b = min(b, dist[i][otros].mean())
        
        if max(a, b) > 0:
            sil.append((b - a) / max(a, b))
    
    return np.mean(sil) if sil else 0.0


def top_terminos_por_cluster(centroides, inv_vocab, labels, doc_ids, top_n=8):
    """Top términos por cluster + ejemplos de docs."""
    resultado = {}
    k = centroides.shape[0]
    for i in range(k):
        top_idx = centroides[i].argsort()[::-1][:top_n]
        terminos = [inv_vocab.get(int(j), '?') for j in top_idx]
        mask = labels == i
        n_docs = int(mask.sum())
        ejemplos = [doc_ids[j] for j in range(len(labels)) if labels[j] == i][:3]
        resultado[i] = {
            'n_docs': n_docs,
            'terminos': terminos,
            'ejemplos': ejemplos,
        }
    return resultado


def comparar_con_nichos(doc_ids, labels, docs_originales=None):
    """Compara clusters con detectar_nicho.
    
    FIX 2026-09-11: usar contenido de términos del doc, no el nombre.
    """
    from modulos.detectar_nicho import detectar_nicho
    
    print("\n🎯 Comparando clusters vs detectar_nicho...")
    
    if not docs_originales:
        print("   ⚠️  Sin docs originales para comparar")
        return
    
    for i, doc_id in enumerate(doc_ids[:10]):
        if i >= len(labels):
            break
        # FIX: usar términos del doc, no el nombre del archivo
        terminos_doc = docs_originales.get(doc_id, {})
        # Construir "texto" desde términos
        texto_doc = ' '.join(terminos_doc.keys())
        
        nicho = detectar_nicho(texto_doc)
        print(f"   {doc_id[:40]:42} → nicho={nicho:15} cluster={labels[i]}")


def explorar(k=8, usar_lematizacion=True):
    print(f"📊 Cargando documentos de: {DB_PATH}")
    filas = cargar_documentos()
    print(f"   {len(filas)} filas")
    print()
    
    doc_ids, X, inv_vocab = vectorizar_con_validador(
        filas, usar_lematizacion=usar_lematizacion
    )
    
    # Guardar docs originales para comparar
    docs_por_doc = {}
    for fila in filas:
        docs_por_doc.setdefault(fila['doc'], Counter())[fila['term']] = int(fila['freq'])
    
    if len(doc_ids) == 0:
        print("❌ Sin documentos después de filtrar")
        return
    
    print()
    print(f"📐 Matriz: {X.shape[0]} docs × {X.shape[1]} términos")
    print()
    
    print(f"🔍 Ejecutando K-Means (k={k})...")
    labels, centroides, inercia, iter_final = kmeans_casero(X, k)
    print(f"   Convergió en iteración {iter_final}")
    print(f"   Inercia: {inercia:.3f}")
    print()
    
    sil = silhouette_casero(X, labels)
    print(f"📈 Silhouette score: {sil:.3f}")
    if sil > 0.5:
        print(f"   ✅ Clusters bien separados")
    elif sil > 0.25:
        print(f"   🟡 Separación moderada")
    else:
        print(f"   ⚠️  Clusters solapados")
    print()
    
    print(f"🎯 Top términos por cluster:")
    terminos = top_terminos_por_cluster(
        centroides, inv_vocab, labels, doc_ids
    )
    for i, info in terminos.items():
        print(f"\n  Cluster {i} ({info['n_docs']} docs):")
        print(f"    {', '.join(info['terminos'])}")
        print(f"    Ejemplos: {', '.join(d[:30] for d in info['ejemplos'])}")
    
    print()
    print(f"📊 Distribución:")
    for c, n in sorted(Counter(labels).items()):
        print(f"   Cluster {c}: {n} docs")
    
    # Comparación con nichos
    comparar_con_nichos(doc_ids, labels, docs_por_doc)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--k', type=int, default=8)
    parser.add_argument('--no-lematizar', action='store_true')
    args = parser.parse_args()
    
    explorar(args.k, usar_lematizacion=not args.no_lematizar)
