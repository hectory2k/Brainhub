#!/data/data/com.termux/files/usr/bin/python3
"""
MeSH on-demand con cache en DuckDB.
Consulta NCBI solo la primera vez, luego usa cache local.
"""

import requests
import time
import subprocess
from typing import Optional, Dict


class MeSHCache:
    """Consulta MeSH con cache local."""
    
    DB_PATH = '/sdcard/Download/analisis_consolidado.duckdb'
    
    def __init__(self):
        self._crear_tabla_cache()
    
    def _crear_tabla_cache(self):
        """Crea tabla cache_mesh en DuckDB."""
        sql = """
        CREATE TABLE IF NOT EXISTS cache_mesh (
            termino_busqueda VARCHAR PRIMARY KEY,
            mesh_id VARCHAR,
            traduccion VARCHAR,
            fecha_cache TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql], 
                      capture_output=True, text=True)
    
    def buscar(self, termino: str) -> Dict:
        """
        Busca término en cache, si no está consulta NCBI.
        """
        # 1. Verificar cache
        cache = self._buscar_en_cache(termino)
        if cache:
            return {'fuente': 'cache', **cache}
        
        # 2. Consultar NCBI
        time.sleep(0.34)  # Rate limit
        r = requests.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            params={'db': 'mesh', 'term': termino, 'retmode': 'json'},
            timeout=10
        )
        
        datos = r.json()
        idlist = datos.get('esearchresult', {}).get('idlist', [])
        traduccion = datos.get('esearchresult', {}).get('querytranslation', '')
        
        if not idlist:
            return {'fuente': 'no_encontrado', 'termino': termino}
        
        mesh_id = idlist[0]
        resultado = {
            'termino_busqueda': termino,
            'mesh_id': mesh_id,
            'traduccion': traduccion
        }
        
        # 3. Guardar en cache
        self._guardar_en_cache(resultado)
        
        return {'fuente': 'ncbi', **resultado}
    
    def _buscar_en_cache(self, termino: str) -> Optional[Dict]:
        sql = f"""
        SELECT mesh_id, traduccion
        FROM cache_mesh
        WHERE termino_busqueda = '{termino}'
        """
        resultado = subprocess.run(
            ['duckdb', self.DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=5
        )
        
        lineas = resultado.stdout.strip().split('\n')
        if len(lineas) > 1:
            mesh_id, traduccion = lineas[1].split(',', 1)
            return {'mesh_id': mesh_id, 'traduccion': traduccion}
        return None
    
    def _guardar_en_cache(self, resultado: Dict):
        sql = f"""
        INSERT OR REPLACE INTO cache_mesh (termino_busqueda, mesh_id, traduccion)
        VALUES ('{resultado['termino_busqueda']}', '{resultado['mesh_id']}', 
                '{resultado['traduccion'][:200].replace("'", "''")}')
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql],
                      capture_output=True, text=True, timeout=5)


if __name__ == '__main__':
    mesh = MeSHCache()
    
    # Primera búsqueda (va a NCBI)
    resultado = mesh.buscar('Pressure Ulcer')
    print(f"Fuente: {resultado['fuente']}")
    print(f"MeSH ID: {resultado.get('mesh_id')}")
    
    # Segunda búsqueda (va a cache)
    resultado2 = mesh.buscar('Pressure Ulcer')
    print(f"\nSegunda búsqueda:")
    print(f"Fuente: {resultado2['fuente']} (debería ser cache)")
