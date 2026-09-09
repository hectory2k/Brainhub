import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Sugerente de búsquedas anatómicas.
Combina anatomía BodyParts3D + diccionario clínico + MeSH.
"""

import subprocess
from typing import Dict, List


class SugerenteAnatomia:
    """Sugiere búsquedas médicas desde conceptos anatómicos."""
    
    DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
    
    def buscar_anatomia(self, termino: str) -> List[Dict]:
        """Busca concepto anatómico en DuckDB."""
        sql = f"""
        SELECT concepto_id, nombre_en, elementos
        FROM anatomia
        WHERE LOWER(nombre_en) LIKE '%{termino.lower()}%'
        LIMIT 10;
        """
        
        resultado = subprocess.run(
            ['duckdb', self.DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=10
        )
        
        import csv
        import io
        reader = csv.reader(io.StringIO(resultado.stdout))
        next(reader, None)
        
        return [
            {'concepto_id': fila[0], 'nombre': fila[1], 'elementos': int(fila[2])}
            for fila in reader if fila
        ]
    
    def sugerir_busqueda(self, termino: str) -> Dict:
        """
        Sugiere búsqueda PubMed basada en anatomía.
        
        Returns:
            {'anatomia': [...], 'query_sugerida': '...', 'mesh': '...'}
        """
        # 1. Buscar en anatomía
        conceptos = self.buscar_anatomia(termino)
        
        if not conceptos:
            return {'error': f'No se encontró "{termino}" en anatomía'}
        
        # 2. Construir query MeSH sugerida
        nombre_principal = conceptos[0]['nombre']
        mesh_sugerido = nombre_principal.replace(' ', ' AND ')
        
        query = f'"{nombre_principal}"[MeSH]'
        
        # 3. Buscar en diccionario clínico si hay alias
        from modulos.diccionario_clinico import DiccionarioClinico
        dc = DiccionarioClinico()
        alias = dc.get_alias_mesh(termino)
        
        if alias:
            mesh_sugerido = alias
            query = f'"{alias}"[MeSH]'
        
        return {
            'anatomia': conceptos[:5],
            'mesh_sugerido': mesh_sugerido,
            'query_sugerida': query,
            'total_conceptos': len(conceptos)
        }
    
    def sugerir_relacionados(self, termino: str) -> List[str]:
        """Sugiere conceptos relacionados por sistema."""
        sql = f"""
        SELECT DISTINCT nombre_en
        FROM anatomia
        WHERE LOWER(nombre_en) LIKE '%{termino.lower()}%'
           OR LOWER(nombre_en) LIKE '%{termino.lower().replace(" ", "%")}%'
        LIMIT 10;
        """
        
        resultado = subprocess.run(
            ['duckdb', self.DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=10
        )
        
        return [linea for linea in resultado.stdout.strip().split('\n')[1:] if linea]


if __name__ == '__main__':
    sugerente = SugerenteAnatomia()
    
    # Test: buscar ligamento
    resultado = sugerente.sugerir_busqueda('ligament')
    
    print("🧠 SUGERENTE ANATOMÍA")
    print("=" * 50)
    print(f"\nAnatomía encontrada: {resultado.get('total_conceptos', 0)} conceptos")
    print(f"MeSH sugerido: {resultado.get('mesh_sugerido')}")
    print(f"Query PubMed: {resultado.get('query_sugerida')}")
    
    print("\nConceptos:")
    for c in resultado.get('anatomia', []):
        print(f"   {c['nombre']} ({c['elementos']} meshes)")
    
    # Test: buscar knee
    print("\n\n🔍 KNEE:")
    resultado2 = sugerente.sugerir_busqueda('knee')
    print(f"MeSH: {resultado2.get('mesh_sugerido')}")
    print(f"Query: {resultado2.get('query_sugerida')}")
