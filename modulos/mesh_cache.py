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
    
    def buscar(self, termino: str, contexto: str = '') -> Dict:
        """
        Busca término MeSH con contexto.
        Si hay contexto, usa el bigrama para mejor precisión.
        """
        # Si hay contexto, buscar con bigrama
        if contexto:
            termino_busqueda = f"{contexto} {termino}"
        else:
            termino_busqueda = termino
        
        return self._buscar_interno(termino_busqueda)
    
    def _buscar_interno(self, termino: str) -> Dict:
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
        
        # Obtener nombre oficial del descriptor
        time.sleep(0.34)
        r_nombre = requests.get(
            'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
            params={'db': 'mesh', 'id': mesh_id, 'retmode': 'json'},
            timeout=10
        )
        
        nombre_oficial = termino
        try:
            summary = r_nombre.json()
            if 'result' in summary and mesh_id in summary['result']:
                mesh_info = summary['result'][mesh_id]
                # El nombre oficial está en ds_meshterms[0]
                meshterms = mesh_info.get('ds_meshterms', [])
                if meshterms:
                    nombre_oficial = meshterms[0]
                else:
                    nombre_oficial = mesh_info.get('ds_name', termino)
        except:
            pass
        
        resultado = {
            'termino_busqueda': termino,
            'mesh_id': mesh_id,
            'nombre_oficial': nombre_oficial,
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
