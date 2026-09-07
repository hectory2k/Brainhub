#!/data/data/com.termux/files/usr/bin/python3
"""
Cliente PubMed E-utilities para BrainHub.
Gratis, con límite de 3 requests/segundo.
"""

import requests
import time
from typing import Dict, List


class PubMedClient:
    """Cliente para NCBI E-utilities."""
    
    BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
    
    def __init__(self):
        self.ultimo_request = 0
    
    def _respetar_rate_limit(self):
        """Mantiene 3 requests/segundo."""
        tiempo_actual = time.time()
        tiempo_desde_ultimo = tiempo_actual - self.ultimo_request
        
        if tiempo_desde_ultimo < 0.34:  # 1/3 de segundo
            time.sleep(0.34 - tiempo_desde_ultimo)
        
        self.ultimo_request = time.time()
    
    def buscar(self, query: str, max_resultados: int = 10) -> List[str]:
        """
        Busca PMIDs en PubMed.
        
        Args:
            query: Query MeSH booleana
            max_resultados: Máximo de PMIDs a retornar
        
        Returns:
            Lista de PMIDs
        """
        self._respetar_rate_limit()
        
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_resultados,
            'retmode': 'json'
        }
        
        r = requests.get(f'{self.BASE_URL}/esearch.fcgi', params=params, timeout=10)
        datos = r.json()
        
        return datos.get('esearchresult', {}).get('idlist', [])
    
    def obtener_metadatos(self, pmid: str) -> Dict:
        """
        Obtiene metadatos de un artículo por PMID.
        
        Returns:
            {'pmid': ..., 'titulo': ..., 'autores': ..., 'revista': ..., 'año': ...}
        """
        self._respetar_rate_limit()
        
        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml'
        }
        
        r = requests.get(f'{self.BASE_URL}/efetch.fcgi', params=params, timeout=10)
        
        # Parseo simple del XML (sin dependencias)
        contenido = r.text
        
        titulo = self._extraer(contenido, '<ArticleTitle>', '</ArticleTitle>')
        revista = self._extraer(contenido, '<Title>', '</Title>')
        año = self._extraer(contenido, '<Year>', '</Year>')
        
        return {
            'pmid': pmid,
            'titulo': titulo,
            'revista': revista,
            'año': int(año) if año.isdigit() else 0,
            'url_pubmed': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
        }
    
    def _extraer(self, texto: str, inicio: str, fin: str) -> str:
        """Extrae texto entre marcadores XML."""
        try:
            idx_inicio = texto.find(inicio) + len(inicio)
            idx_fin = texto.find(fin, idx_inicio)
            return texto[idx_inicio:idx_fin].strip()
        except:
            return ''


if __name__ == '__main__':
    cliente = PubMedClient()
    
    # Test con query simple
    pmids = cliente.buscar('"Pressure Ulcer/prevention and control"[MeSH]', max_resultados=5)
    print(f"📋 PMIDs encontrados: {len(pmids)}")
    
    if pmids:
        metadatos = cliente.obtener_metadatos(pmids[0])
        print(f"\n📄 Primer artículo:")
        print(f"   Título: {metadatos['titulo'][:100]}")
        print(f"   Revista: {metadatos['revista']}")
        print(f"   Año: {metadatos['año']}")
