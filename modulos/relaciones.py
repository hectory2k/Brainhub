import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Extracción de relaciones entre entidades para construcción de grafos.
Integra con entidades.py y prepara exportación a Neo4j.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict

try:
    from modulos.entidades import EntidadesManager
except ImportError:
    EntidadesManager = None


class RelacionesManager:
    """Extrae y gestiona relaciones entre entidades."""
    
    PATRONES_ES = {
        'usa': [
            r'(\w+)\s+(?:usa|utiliza|emplea|implementa con|trabaja con)\s+(\w+)',
            r'(\w+)\s+est[aá]\s+(?:basado|construido|desarrollado)\s+(?:en|con)\s+(\w+)'
        ],
        'mejora': [
            r'(\w+)\s+(?:mejora|optimiza|potencia|fortalece)\s+(?:el|la|los|las)?\s*(\w+)',
            r'(\w+)\s+permite\s+(?:mejorar|optimizar)\s+(\w+)'
        ],
        'relacionado_con': [
            r'(\w+)\s+(?:se relaciona|est[aá] relacionado|conecta)\s+(?:con|a)\s+(\w+)',
            r'(\w+)\s+y\s+(\w+)\s+(?:son|est[aá]n)\s+(?:relacionados|conectados)'
        ],
        'causa': [
            r'(\w+)\s+(?:causa|provoca|genera|produce)\s+(\w+)',
            r'(\w+)\s+(?:lleva|conduce)\s+a\s+(\w+)'
        ],
        'parte_de': [
            r'(\w+)\s+(?:es parte|forma parte|pertenece)\s+(?:de|al)\s+(\w+)',
            r'(\w+)\s+incluye\s+(\w+)'
        ]
    }
    
    PATRONES_EN = {
        'usa': [
            r'(\w+)\s+(?:uses|utilizes|employs)\s+(\w+)',
            r'(\w+)\s+is\s+(?:based|built)\s+(?:on|with)\s+(\w+)'
        ],
        'improves': [
            r'(\w+)\s+(?:improves|enhances|optimizes)\s+(\w+)'
        ],
        'related_to': [
            r'(\w+)\s+(?:relates|connects)\s+to\s+(\w+)'
        ],
        'causes': [
            r'(\w+)\s+(?:causes|leads to|results in)\s+(\w+)'
        ]
    }
    
    def __init__(self, idioma='es'):
        self.idioma = idioma
        self.patrones = self.PATRONES_ES if idioma == 'es' else self.PATRONES_EN
        self.relaciones = []
    
    def extraer_de_texto(self, texto: str, entidades: List[str] = None) -> List[Dict]:
        """Extrae relaciones de un texto."""
        relaciones = []
        texto_lower = texto.lower()
        
        # Normalizar entidades a minúsculas
        entidades_set = set()
        if entidades:
            entidades_set = {e.lower() for e in entidades}
        
        for tipo_relacion, patrones in self.patrones.items():
            for patron in patrones:
                matches = re.findall(patron, texto_lower)
                for origen, destino in matches:
                    if entidades_set:
                        if origen.lower() not in entidades_set and destino.lower() not in entidades_set:
                            continue
                    
                    relaciones.append({
                        'origen': origen,
                        'destino': destino,
                        'tipo': tipo_relacion,
                        'peso': 1.0
                    })
        
        return relaciones
    
    def extraer_de_segmentos(self, segmentos: List[Dict]) -> List[Dict]:
        """Extrae relaciones de múltiples segmentos con entidades."""
        todas_relaciones = []
        
        for segmento in segmentos:
            texto = segmento.get('texto', '')
            entidades = segmento.get('entidades', [])
            relaciones = self.extraer_de_texto(texto, entidades)
            todas_relaciones.extend(relaciones)
        
        return self.consolidar_relaciones(todas_relaciones)
    
    def consolidar_relaciones(self, relaciones: List[Dict]) -> List[Dict]:
        """Consolida relaciones duplicadas sumando pesos."""
        consolidadas = defaultdict(lambda: {'peso': 0.0, 'count': 0})
        
        for rel in relaciones:
            clave = (rel['origen'], rel['destino'], rel['tipo'])
            consolidadas[clave]['peso'] += rel.get('peso', 1.0)
            consolidadas[clave]['count'] += 1
        
        resultado = []
        for (origen, destino, tipo), datos in consolidadas.items():
            resultado.append({
                'origen': origen,
                'destino': destino,
                'tipo': tipo,
                'peso': round(datos['peso'], 3),
                'frecuencia': datos['count']
            })
        
        return sorted(resultado, key=lambda x: x['peso'], reverse=True)
    
    def exportar_cypher(self, relaciones: List[Dict], entidades: List[Dict] = None) -> str:
        """Exporta relaciones a Cypher para Neo4j."""
        lineas = []
        nodos = set()
        
        for rel in relaciones:
            nodos.add(rel['origen'])
            nodos.add(rel['destino'])
        
        for nodo in nodos:
            lineas.append(
                f"MERGE (n:{self._sanitizar_label(nodo)} {{nombre: '{self._sanitizar(nodo)}'}});"
            )
        
        for rel in relaciones:
            origen = self._sanitizar(rel['origen'])
            destino = self._sanitizar(rel['destino'])
            tipo = self._sanitizar_label(rel['tipo'])
            peso = rel['peso']
            
            lineas.append(
                f"MATCH (a {{nombre: '{origen}'}}), (b {{nombre: '{destino}'}}) "
                f"MERGE (a)-[:{tipo} {{peso: {peso}}}]->(b);"
            )
        
        return '\n'.join(lineas)
    
    def exportar_gexf(self, relaciones: List[Dict], entidades: List[Dict] = None) -> str:
        """Exporta a GEXF para Gephi."""
        nodos = set()
        for rel in relaciones:
            nodos.add(rel['origen'])
            nodos.add(rel['destino'])
        
        gexf = ['<?xml version="1.0" encoding="UTF-8"?>']
        gexf.append('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">')
        gexf.append('<graph mode="static" defaultedgetype="directed">')
        
        gexf.append('<nodes>')
        for i, nodo in enumerate(nodos, 1):
            gexf.append(f'<node id="{i}" label="{self._sanitizar_xml(nodo)}" />')
        gexf.append('</nodes>')
        
        nodo_ids = {nodo: i for i, nodo in enumerate(nodos, 1)}
        
        gexf.append('<edges>')
        for i, rel in enumerate(relaciones, 1):
            origen_id = nodo_ids[rel['origen']]
            destino_id = nodo_ids[rel['destino']]
            gexf.append(
                f'<edge id="{i}" source="{origen_id}" target="{destino_id}" '
                f'label="{self._sanitizar_xml(rel["tipo"])}" weight="{rel["peso"]}" />'
            )
        gexf.append('</edges>')
        
        gexf.append('</graph>')
        gexf.append('</gexf>')
        
        return '\n'.join(gexf)
    
    def exportar_json_grafo(self, relaciones: List[Dict], entidades: List[Dict] = None) -> Dict:
        """Exporta a formato JSON para visualización."""
        nodos = set()
        for rel in relaciones:
            nodos.add(rel['origen'])
            nodos.add(rel['destino'])
        
        return {
            'nodos': [{'id': n, 'label': n} for n in nodos],
            'aristas': [
                {
                    'origen': rel['origen'],
                    'destino': rel['destino'],
                    'tipo': rel['tipo'],
                    'peso': rel['peso']
                }
                for rel in relaciones
            ]
        }
    
    def _sanitizar(self, texto: str) -> str:
        return texto.replace("'", "\\'").replace('"', '\\"')
    
    def _sanitizar_label(self, texto: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_]', '_', texto)
    
    def _sanitizar_xml(self, texto: str) -> str:
        return (texto.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;'))


class IntegradorRelaciones:
    """Integra relaciones con el pipeline existente."""
    
    def __init__(self, db_path=os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')):
        self.db_path = db_path
        self.manager = RelacionesManager()
    
    def extraer_de_duckdb(self, content_id: str) -> List[Dict]:
        """Extrae relaciones desde datos en DuckDB."""
        import subprocess
        
        sql_entidades = f"""
        SELECT nombre, tipo, frecuencia
        FROM entidades
        WHERE content_id = '{content_id}';
        """
        
        try:
            resultado = subprocess.run(
                ['duckdb', self.db_path, '-csv', '-c', sql_entidades],
                capture_output=True, text=True, timeout=30
            )
            
            if resultado.returncode != 0:
                return []
            
            lineas = resultado.stdout.strip().split('\n')
            entidades = []
            for linea in lineas[1:]:
                partes = linea.split(',')
                if len(partes) >= 2:
                    entidades.append(partes[0])
            
            relaciones = []
            for i, ent1 in enumerate(entidades):
                for ent2 in entidades[i+1:]:
                    relaciones.append({
                        'origen': ent1,
                        'destino': ent2,
                        'tipo': 'coocurrencia',
                        'peso': 1.0
                    })
            
            return relaciones
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return []
    
    def guardar_en_duckdb(self, content_id: str, relaciones: List[Dict]) -> bool:
        """Guarda relaciones en DuckDB."""
        import subprocess
        
        if not relaciones:
            return False
        
        schema = """
        CREATE TABLE IF NOT EXISTS relaciones_grafo (
            id INTEGER PRIMARY KEY,
            content_id VARCHAR,
            origen VARCHAR,
            destino VARCHAR,
            tipo VARCHAR,
            peso FLOAT,
            frecuencia INTEGER
        );
        """
        
        inserts = []
        for rel in relaciones:
            inserts.append(f"""
            INSERT INTO relaciones_grafo (content_id, origen, destino, tipo, peso, frecuencia)
            VALUES ('{content_id}', '{rel['origen']}', '{rel['destino']}', 
                    '{rel['tipo']}', {rel['peso']}, {rel.get('frecuencia', 1)});
            """)
        
        sql_completo = schema + '\n'.join(inserts)
        
        try:
            resultado = subprocess.run(
                ['duckdb', self.db_path],
                input=sql_completo,
                capture_output=True,
                text=True,
                timeout=30
            )
            return resultado.returncode == 0
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return False


if __name__ == '__main__':
    manager = RelacionesManager()
    
    texto_prueba = """
    PyTorch usa tensores para deep learning.
    El modelo mejora la precisión del diagnóstico.
    Python se relaciona con machine learning.
    """
    
    entidades = ['PyTorch', 'Python', 'tensores', 'modelo', 'deep learning']
    
    relaciones = manager.extraer_de_texto(texto_prueba, entidades)
    print(f"✅ Relaciones encontradas: {len(relaciones)}")
    for rel in relaciones:
        print(f"   {rel['origen']} -[{rel['tipo']}]-> {rel['destino']}")
    
    cypher = manager.exportar_cypher(relaciones)
    print(f"\n📝 Cypher generado ({len(cypher.splitlines())} líneas)")
