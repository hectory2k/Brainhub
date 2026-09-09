import os
#!/data/data/com.termux/files/usr/bin/python3
"""
Paginación para consultas DuckDB en BrainHub.
Cursor pagination para datasets que se actualizan.
"""

from typing import List, Dict, Optional


class PaginacionDuckDB:
    """Paginación para consultas grandes."""
    
    def __init__(self, db_path=os.environ.get('BRAINHUB_DB', 'data/analisis_consolidado.duckdb')):
        self.db_path = db_path
        self.por_pagina = 20
    
    def consultar_paginado(
        self,
        sql_base: str,
        pagina: int = 1,
        por_pagina: int = 20
    ) -> Dict:
        """
        Consulta paginada.
        
        Returns:
            {'datos': [...], 'pagina': 1, 'total_paginas': 5, 'hay_mas': True}
        """
        import subprocess
        import csv
        import io
        
        offset = (pagina - 1) * por_pagina
        
        # Consulta de datos
        sql_datos = f"{sql_base} LIMIT {por_pagina} OFFSET {offset}"
        
        resultado = subprocess.run(
            ['duckdb', self.db_path, '-csv', '-c', sql_datos],
            capture_output=True, text=True, timeout=30
        )
        
        if resultado.returncode != 0:
            return {'datos': [], 'pagina': pagina, 'error': resultado.stderr}
        
        reader = csv.reader(io.StringIO(resultado.stdout))
        headers = next(reader, [])
        datos = [dict(zip(headers, fila)) for fila in reader if fila]
        
        # Consulta total
        sql_total = f"SELECT COUNT(*) FROM ({sql_base}) t"
        resultado_total = subprocess.run(
            ['duckdb', self.db_path, '-csv', '-c', sql_total],
            capture_output=True, text=True, timeout=30
        )
        
        total = int(resultado_total.stdout.strip().split('\n')[-1])
        total_paginas = (total + por_pagina - 1) // por_pagina
        
        return {
            'datos': datos,
            'pagina': pagina,
            'total': total,
            'total_paginas': total_paginas,
            'hay_mas': pagina < total_paginas
        }


if __name__ == '__main__':
    paginador = PaginacionDuckDB()
    
    # Test con términos
    resultado = paginador.consultar_paginado(
        "SELECT term, frequency FROM terminos_raw ORDER BY frequency DESC",
        pagina=1,
        por_pagina=5
    )
    
    print(f"📄 Página {resultado['pagina']} de {resultado['total_paginas']}")
    print(f"   Total: {resultado['total']} términos")
    print(f"   Hay más: {resultado['hay_mas']}")
    
    for dato in resultado['datos'][:5]:
        print(f"   {dato.get('term', '')}: {dato.get('frequency', '')}")
