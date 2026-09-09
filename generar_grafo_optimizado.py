#!/data/data/com.termux/files/usr/bin/python3
"""
Grafo optimizado - Versión 3
Correcciones:
- Parseo CSV robusto con librería csv
- splines suaves (no ortho)
- Grafo no dirigido para coocurrencia
"""

import json
import subprocess
import sys
import os
import csv
import io
from pathlib import Path
from collections import defaultdict

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from modulos.stopwords_manager import StopwordsManager
from modulos.relaciones import RelacionesManager

DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
OUTPUT_DIR = PROJECT_DIR / 'outputs' / 'grafo'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UMBRAL_PESO = 1.5
TOP_N = 8
FRECUENCIA_MINIMA = 5


def obtener_stopwords():
    manager = StopwordsManager()
    stopwords = set()
    
    for lang in ['es', 'en']:
        sw = manager.get_stopwords('GENERAL', lang)
        if isinstance(sw, set):
            stopwords.update(sw)
        elif isinstance(sw, list):
            stopwords.update(sw)
    
    # Muletillas de transcripciones habladas
    MULETILLAS = {
        'tenemos', 'bien', 'mas', 'más', 'vamos', 'hacer', 'aqui', 'aquí',
        'entonces', 'luego', 'solo', 'sólo', 'como', 'cómo', 'cuando',
        'donde', 'dónde', 'nada', 'todo', 'todos', 'puede', 'pueden',
        'ser', 'hay', 'hace', 'hacen', 'dice', 'dicen', 'va', 'van'
    }
    stopwords.update(MULETILLAS)
    
    return stopwords


def obtener_terminos_filtrados(stopwords):
    """Parseo CSV robusto con librería csv."""
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
        print(f"❌ Error DuckDB: {resultado.stderr[:200]}")
        return {}
    
    videos = defaultdict(list)
    reader = csv.reader(io.StringIO(resultado.stdout))
    next(reader, None)  # Saltar cabecera
    
    for fila in reader:
        if len(fila) >= 3:
            video = fila[0]
            termino = fila[1].strip().lower()
            frecuencia = int(fila[2])
            
            if termino not in stopwords and len(termino) >= 2 and frecuencia >= FRECUENCIA_MINIMA:
                videos[video].append((termino, frecuencia))
    
    return videos


def generar_relaciones(videos_terminos):
    """Genera co-ocurrencias con peso proporcional a frecuencia."""
    manager = RelacionesManager()
    relaciones_crudas = []
    
    for video, terminos in videos_terminos.items():
        # Top N con frecuencia real
        top = sorted(terminos, key=lambda x: x[1], reverse=True)[:TOP_N]
        
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                term1, freq1 = top[i]
                term2, freq2 = top[j]
                
                # Peso proporcional a la presencia de ambos términos
                peso_relacion = round(min(freq1, freq2) / 10.0, 2)
                
                # Agregar una sola arista (grafo no dirigido)
                relaciones_crudas.append({
                    'origen': term1,
                    'destino': term2,
                    'tipo': 'coocurrencia',
                    'peso': peso_relacion
                })
    
    # Consolidar
    consolidadas = manager.consolidar_relaciones(relaciones_crudas)
    
    # Filtrar por umbral
    filtradas = [r for r in consolidadas if r['peso'] >= UMBRAL_PESO]
    
    return filtradas


def integrar_grounding_temporal(relaciones, video_id=None):
    """Agrega grounding temporal a las relaciones del grafo."""
    try:
        from modulos.timestamps import TimestampsDB
        
        db = TimestampsDB()
        
        for rel in relaciones:
            # Buscar timestamps para cada término
            origen = rel.get('origen', '')
            destino = rel.get('destino', '')
            
            if video_id:
                # Buscar en video específico
                ts_origen = db.buscar_en_video(video_id, origen)
                ts_destino = db.buscar_en_video(video_id, destino)
                
                if ts_origen:
                    rel['grounding_origen'] = ts_origen[0].get('inicio', '')
                if ts_destino:
                    rel['grounding_destino'] = ts_destino[0].get('inicio', '')
            else:
                # Buscar en todos los videos
                ts_origen = db.buscar_en_todos(origen)
                ts_destino = db.buscar_en_todos(destino)
                
                if ts_origen:
                    rel['grounding_origen'] = f"{ts_origen[0].get('video_id', '')}:{ts_origen[0].get('inicio', '')}"
                if ts_destino:
                    rel['grounding_destino'] = f"{ts_destino[0].get('video_id', '')}:{ts_destino[0].get('inicio', '')}"
        
        return relaciones
    except ImportError:
        return relaciones
    except Exception as e:
        print(f"⚠️ No se pudo integrar grounding: {e}")
        return relaciones


def generar_dot(relaciones, ruta_salida):
    """Genera DOT no dirigido con splines suaves."""
    dot = ['graph G {']  # graph en vez de digraph
    dot.append('  layout=neato;')  # Mejor para grafos no dirigidos
    dot.append('  splines=true;')  # Curvas suaves
    dot.append('  overlap=false;')
    dot.append('  node [shape=box, style=rounded, fontname="Helvetica", fontsize=11];')
    dot.append('  edge [fontname="Helvetica", fontsize=9];')
    
    grados = defaultdict(int)
    for rel in relaciones:
        grados[rel['origen']] += 1
        grados[rel['destino']] += 1
    
    for nodo, grado in grados.items():
        fontsize = 10 + min(grado, 10) * 1.5
        dot.append(f'  "{nodo}" [fontsize={fontsize}];')
    
    # Sin label en aristas para evitar conflicto con splines
    for rel in relaciones:
        origen = rel['origen'].replace('"', '\\"')
        destino = rel['destino'].replace('"', '\\"')
        penwidth = min(rel['peso'], 6)
        dot.append(f'  "{origen}" -- "{destino}" [penwidth={penwidth}];')
    
    dot.append('}')
    
    with open(ruta_salida, 'w') as f:
        f.write('\n'.join(dot))


def main():
    print("🚀 GRAFO OPTIMIZADO V3")
    print("=" * 50)
    
    print("\n📋 Stopwords...")
    stopwords = obtener_stopwords()
    print(f"   {len(stopwords)} stopwords")
    
    print("\n📊 Términos...")
    videos_terminos = obtener_terminos_filtrados(stopwords)
    print(f"   {len(videos_terminos)} videos")
    
    print("\n🔗 Relaciones...")
    relaciones = generar_relaciones(videos_terminos)
    print(f"   {len(relaciones)} relaciones")

    # Integrar grounding temporal
    print("\n⏱️ Grounding temporal...")
    relaciones = integrar_grounding_temporal(relaciones)
    print(f"   {len(relaciones)} relaciones con grounding")
    
    # JSON
    manager = RelacionesManager()
    json_grafo = manager.exportar_json_grafo(relaciones)
    json_grafo['metadata'] = {
        'total_nodos': len(json_grafo['nodos']),
        'total_relaciones': len(relaciones),
        'umbral_peso': UMBRAL_PESO,
        'fecha': __import__('datetime').datetime.now().isoformat()
    }
    
    ruta_json = OUTPUT_DIR / 'grafo_optimizado.json'
    ruta_json.write_text(json.dumps(json_grafo, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n✅ JSON: {ruta_json}")
    
    # DOT y PNG
    ruta_dot = os.path.expanduser('~/tmp/grafo_optimizado.dot')
    generar_dot(relaciones, ruta_dot)
    print(f"✅ DOT: {ruta_dot}")
    
    ruta_png = Path('/sdcard/Download/grafo_nlp/grafo_optimizado.png')
    subprocess.run(['dot', '-Tpng', ruta_dot, '-o', str(ruta_png)], 
                   capture_output=True, text=True)
    
    if ruta_png.exists():
        print(f"✅ PNG: {ruta_png}")
        print(f"   Tamaño: {ruta_png.stat().st_size} bytes")
    
    # Resumen
    grados = defaultdict(int)
    for rel in relaciones:
        grados[rel['origen']] += 1
        grados[rel['destino']] += 1
    
    top = sorted(grados.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print(f"\n📊 RESUMEN")
    print(f"   Nodos: {len(json_grafo['nodos'])}")
    print(f"   Relaciones: {len(relaciones)}")
    print(f"\n🏆 TOP:")
    for nodo, grado in top:
        print(f"   {nodo}: {grado}")


if __name__ == '__main__':
    main()
