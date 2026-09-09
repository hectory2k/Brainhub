import os
#!/data/data/com.termux/files/usr/bin/python3
"""
MeSH Database en Parquet para consultas locales con DuckDB.
"""

import subprocess
from typing import List, Dict


class MeSHParquet:
    """Consulta MeSH localmente desde DuckDB."""
    
    DB_PATH = os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')
    
    def crear_tabla_mesh(self):
        """Crea tabla mesh_terms en DuckDB."""
        sql = """
        CREATE TABLE IF NOT EXISTS mesh_terms (
            termino VARCHAR,
            mesh_id VARCHAR,
            sinonimos VARCHAR,
            categoria VARCHAR
        );
        """
        subprocess.run(['duckdb', self.DB_PATH, '-c', sql], 
                      capture_output=True, text=True)
        print("✅ Tabla mesh_terms creada")
    
    def buscar_termino(self, termino: str) -> List[Dict]:
        """Busca un término en MeSH local."""
        sql = f"""
        SELECT termino, sinonimos, categoria
        FROM mesh_terms
        WHERE LOWER(termino) LIKE '%{termino.lower()}%'
           OR LOWER(sinonimos) LIKE '%{termino.lower()}%'
        LIMIT 5;
        """
        
        resultado = subprocess.run(
            ['duckdb', self.DB_PATH, '-csv', '-c', sql],
            capture_output=True, text=True, timeout=10
        )
        
        # Parsear CSV
        import csv
        import io
        reader = csv.reader(io.StringIO(resultado.stdout))
        next(reader, None)
        
        return [
            {'termino': fila[0], 'sinonimos': fila[1], 'categoria': fila[2]}
            for fila in reader if fila
        ]


if __name__ == '__main__':
    mesh = MeSHParquet()
    mesh.crear_tabla_mesh()
    
    # Test (tabla vacía por ahora)
    resultados = mesh.buscar_termino('Pressure Ulcer')
    print(f"Resultados: {len(resultados)}")
