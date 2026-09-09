import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Genera el grafo real de relaciones desde DuckDB.
Versión 2: filtra stopwords y usa secuencia en DuckDB.
"""

import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from modulos.relaciones import RelacionesManager
from modulos.stopwords_manager import StopwordsManager

DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
OUTPUT_DIR = PROJECT_DIR / 'outputs' / 'grafo'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def obtener_stopwords():
    """Obtiene stopwords combinadas del ecosistema."""
    try:
        manager = StopwordsManager()
        stopwords = set()
        for lang in ['es', 'en']:
            sw = manager.get_stopwords('GENERAL', lang)
            if isinstance(sw, set):
                stopwords.update(sw)
            elif isinstance(sw, list):
                stopwords.update(sw)
        return stopwords
    except Exception:
        return set()


def obtener_terminos_por_video(stopwords):
    """Obtiene términos filtrados por video desde DuckDB."""
    sql = """
    SELECT video, term, SUM(frequency) as freq
    FROM terminos_raw
    GROUP BY video, term
    ORDER BY video, freq DESC;
    """
    
    resultado = subprocess.run(
        ['duckdb', DB_PATH, '-csv', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    
    if resultado.returncode != 0:
        print(f"❌ Error: {resultado.stderr}")
        return {}
    
    videos = defaultdict(list)
    lineas = resultado.stdout.strip().split('\n')
    
    for linea in lineas[1:]:
        partes = linea.split(',')
        if len(partes) >= 3:
            video = partes[0]
            termino = partes[1].strip('"').lower()
            frecuencia = int(partes[2])
            
            # Filtrar stopwords
            if termino not in stopwords and len(termino) > 3:
                videos[video].append((termino, frecuencia))
    
    return videos


def generar_relaciones_coocurrencia(videos_terminos, top_n=15):
    """Genera relaciones por co-ocurrencia con filtro de stopwords."""
    relaciones = defaultdict(lambda: {'peso': 0.0, 'videos': set()})
    
    for video, terminos in videos_terminos.items():
        top_terminos = [t for t, _ in sorted(terminos, key=lambda x: x[1], reverse=True)[:top_n]]
        
        for i, term1 in enumerate(top_terminos):
            for term2 in top_terminos[i+1:]:
                clave = (term1, term2)
                relaciones[clave]['peso'] += 1.0
                relaciones[clave]['videos'].add(video)
    
    resultado = []
    for (origen, destino), datos in relaciones.items():
        if datos['peso'] >= 2:
            resultado.append({
                'origen': origen,
                'destino': destino,
                'tipo': 'coocurrencia',
                'peso': round(datos['peso'], 2),
                'videos': len(datos['videos'])
            })
    
    return sorted(resultado, key=lambda x: x['peso'], reverse=True)


def guardar_resultados(relaciones):
    """Guarda en Cypher, GEXF, JSON y DuckDB."""
    manager = RelacionesManager()
    
    # Cypher
    cypher = manager.exportar_cypher(relaciones)
    (OUTPUT_DIR / 'grafo_ecosistema.cypher').write_text(cypher, encoding='utf-8')
    print(f"✅ Cypher: {len(relaciones)} relaciones")
    
    # GEXF
    gexf = manager.exportar_gexf(relaciones)
    (OUTPUT_DIR / 'grafo_ecosistema.gexf').write_text(gexf, encoding='utf-8')
    print(f"✅ GEXF generado")
    
    # JSON
    json_grafo = manager.exportar_json_grafo(relaciones)
    json_grafo['metadata'] = {
        'total_nodos': len(json_grafo['nodos']),
        'total_relaciones': len(relaciones),
        'fecha_generacion': __import__('datetime').datetime.now().isoformat()
    }
    (OUTPUT_DIR / 'grafo_ecosistema.json').write_text(
        json.dumps(json_grafo, ensure_ascii=False, indent=2), 
        encoding='utf-8'
    )
    print(f"✅ JSON generado")
    
    # DuckDB (sin ID explícito, usa secuencia)
    inserts = []
    for rel in relaciones:
        inserts.append(f"""
        INSERT INTO relaciones_grafo (origen, destino, tipo, peso, videos)
        VALUES ('{rel['origen']}', '{rel['destino']}', '{rel['tipo']}', 
                {rel['peso']}, {rel.get('videos', 1)});
        """)
    
    delete_sql = "DELETE FROM relaciones_grafo;"
    sql_completo = delete_sql + '\n'.join(inserts)
    
    try:
        resultado = subprocess.run(
            ['duckdb', DB_PATH],
            input=sql_completo,
            capture_output=True,
            text=True,
            timeout=60
        )
        if resultado.returncode == 0:
            print(f"✅ DuckDB: {len(relaciones)} relaciones guardadas")
        else:
            print(f"⚠️ DuckDB: {resultado.stderr[:200]}")
    except Exception as e:
        print(f"⚠️ Error DuckDB: {e}")
    
    return json_grafo


def mostrar_resumen(json_grafo):
    """Muestra resumen del grafo filtrado."""
    grados = defaultdict(int)
    for arista in json_grafo['aristas']:
        grados[arista['origen']] += 1
        grados[arista['destino']] += 1
    
    top_nodos = sorted(grados.items(), key=lambda x: x[1], reverse=True)[:15]
    
    print(f"\n📊 RESUMEN DEL GRAFO FILTRADO")
    print(f"{'='*50}")
    print(f"   Nodos: {len(json_grafo['nodos'])}")
    print(f"   Relaciones: {len(json_grafo['aristas'])}")
    
    print(f"\n🏆 TOP 15 TÉRMINOS POR CONEXIONES:")
    for i, (nodo, grado) in enumerate(top_nodos, 1):
        barra = '█' * min(grado, 20)
        print(f"   {i:2}. {nodo}: {grado} {barra}")
    
    top_relaciones = sorted(json_grafo['aristas'], key=lambda x: x['peso'], reverse=True)[:15]
    
    print(f"\n🔗 TOP 15 RELACIONES:")
    for i, rel in enumerate(top_relaciones, 1):
        print(f"   {i:2}. {rel['origen']} ↔ {rel['destino']} (peso: {rel['peso']})")


def main():
    print("🚀 GENERANDO GRAFO REAL FILTRADO")
    print(f"{'='*50}")
    
    # Cargar stopwords
    print("\n📋 Cargando stopwords...")
    stopwords = obtener_stopwords()
    print(f"   Stopwords: {len(stopwords)}")
    
    # Obtener términos filtrados
    print("\n📊 Extrayendo términos de DuckDB...")
    videos_terminos = obtener_terminos_por_video(stopwords)
    print(f"   Videos: {len(videos_terminos)}")
    
    # Generar relaciones
    print("\n🔗 Generando relaciones...")
    relaciones = generar_relaciones_coocurrencia(videos_terminos, top_n=15)
    print(f"   Relaciones: {len(relaciones)}")
    
    # Guardar
    print("\n💾 Guardando...")
    json_grafo = guardar_resultados(relaciones)
    
    # Mostrar resumen
    mostrar_resumen(json_grafo)
    
    print(f"\n✅ Grafo filtrado generado")
    print(f"📁 {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
