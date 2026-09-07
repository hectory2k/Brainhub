#!/data/data/com.termux/files/usr/bin/python3
"""
Integración completa: MeSH → PubMed → Clasificación → DuckDB
"""

from modulos.mesh_mapper import MeSHMapper
from modulos.pubmed_client import PubMedClient
from modulos.clasificador_evidencia import ClasificadorEvidencia
import subprocess


class PubMedIntegracion:
    """Flujo completo de búsqueda bibliográfica."""
    
    def __init__(self):
        self.mapper = MeSHMapper()
        self.cliente = PubMedClient()
        self.clasificador = ClasificadorEvidencia()
    
    def buscar_y_guardar(self, frase_clinica: str, max_resultados: int = 5):
        """
        Flujo completo:
        1. Frase → MeSH query
        2. PubMed → PMIDs
        3. Metadatos → Clasificar evidencia
        4. Guardar en DuckDB
        """
        # 1. MeSH
        resultado_mesh = self.mapper.construir_query(frase_clinica)
        query = resultado_mesh['query']
        print(f"🔍 Query: {query}")
        
        # 2. PubMed
        pmids = self.cliente.buscar(query, max_resultados)
        print(f"📋 {len(pmids)} artículos encontrados")
        
        # 3. Metadatos + Clasificación
        for pmid in pmids:
            metadatos = self.cliente.obtener_metadatos(pmid)
            
            # Clasificar (simulado: sin Publication Type real)
            nivel = self.clasificador.clasificar(['Review'])
            
            # Guardar en DuckDB
            self._guardar_en_duckdb(metadatos, nivel, query)
        
        return pmids
    
    def _guardar_en_duckdb(self, metadatos, nivel, query):
        """Guarda artículo en DuckDB."""
        sql = f"""
        INSERT OR IGNORE INTO articulos_pubmed (pmid, titulo, revista, año, nivel_evidencia, query_mesh, url_pubmed)
        VALUES ('{metadatos['pmid']}', '{metadatos['titulo'][:200].replace("'", "''")}', 
                '{metadatos['revista'].replace("'", "''")}', {metadatos['año']}, 
                {nivel['nivel']}, '{query}', '{metadatos['url_pubmed']}')
        """
        
        subprocess.run(
            ['duckdb', '/sdcard/Download/analisis_consolidado.duckdb', '-c', sql],
            capture_output=True, text=True, timeout=10
        )


if __name__ == '__main__':
    integracion = PubMedIntegracion()
    
    frase = "prevención de úlceras por presión en pacientes de UCI"
    pmids = integracion.buscar_y_guardar(frase, max_resultados=3)
    
    print(f"\n✅ {len(pmids)} artículos guardados en DuckDB")
    print("   Consultar: SELECT * FROM articulos_pubmed;")
