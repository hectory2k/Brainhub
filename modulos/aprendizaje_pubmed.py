#!/data/data/com.termux/files/usr/bin/python3
"""
Aprendizaje desde resultados PubMed para BrainHub.
Extrae MeSH terms y enriquece el diccionario clínico.
"""

import json
import subprocess
from typing import Dict, List


class AprendizajePubMed:
    """Aprende de cada búsqueda bibliográfica."""
    
    def __init__(self):
        self.ruta_diccionario = '/data/data/com.termux/files/home/proyectos/nlp/diccionario_clinico.json'
        self.ruta_mesh = '/data/data/com.termux/files/home/proyectos/nlp/mesh_local.json'
    
    def extraer_mesh_terms(self, pmids: List[str]) -> List[str]:
        """Extrae MeSH terms de artículos."""
        from modulos.pubmed_client import PubMedClient
        
        cliente = PubMedClient()
        mesh_terms = []
        
        for pmid in pmids[:3]:  # Limitar a 3 por rate limit
            metadatos = cliente.obtener_metadatos(pmid)
            # Los MeSH terms vienen en el XML (simplificado: usamos título)
            mesh_terms.extend(metadatos['titulo'].split()[:10])
        
        return mesh_terms
    
    def actualizar_diccionario(self, nuevos_terminos: List[str]):
        """Agrega términos nuevos al diccionario clínico."""
        try:
            with open(self.ruta_diccionario, 'r') as f:
                diccionario = json.load(f)
        except FileNotFoundError:
            diccionario = {}
        
        # Filtrar términos relevantes (>3 letras, no stopwords)
        relevantes = set()
        for termino in nuevos_terminos:
            termino_limpio = termino.lower().strip('.,;:()[]')
            if len(termino_limpio) > 3:
                relevantes.add(termino_limpio)
        
        # Agregar al concepto de salud
        if 'salud_publica' not in diccionario:
            diccionario['salud_publica'] = {'sinonimos': []}
        
        diccionario['salud_publica']['sinonimos'].extend(relevantes)
        diccionario['salud_publica']['sinonimos'] = list(set(diccionario['salud_publica']['sinonimos']))
        
        with open(self.ruta_diccionario, 'w') as f:
            json.dump(diccionario, f, indent=2, ensure_ascii=False)
        
        return len(relevantes)
    
    def aprender_de_busqueda(self, frase: str, pmids: List[str]) -> Dict:
        """
        Aprende de una búsqueda completa.
        
        Returns:
            {'terminos_aprendidos': int, 'total_diccionario': int}
        """
        print(f"🧠 Aprendiendo de {len(pmids)} artículos...")
        
        # Extraer términos
        mesh_terms = self.extraer_mesh_terms(pmids)
        
        # Actualizar diccionario
        aprendidos = self.actualizar_diccionario(mesh_terms)
        
        print(f"   ✅ {aprendidos} términos nuevos agregados")
        
        return {
            'terminos_aprendidos': aprendidos,
            'total_diccionario': self._contar_diccionario()
        }
    
    def _contar_diccionario(self) -> int:
        """Cuenta total de términos en diccionario."""
        try:
            with open(self.ruta_diccionario, 'r') as f:
                diccionario = json.load(f)
            total = 0
            for concepto in diccionario.values():
                if isinstance(concepto, dict) and 'sinonimos' in concepto:
                    total += len(concepto['sinonimos'])
            return total
        except:
            return 0


if __name__ == '__main__':
    aprendiz = AprendizajePubMed()
    
    # Simular aprendizaje con los 3 artículos que ya tenemos
    pmids = ['38420873', '38386834', '38147064']
    
    resultado = aprendiz.aprender_de_busqueda(
        "úlceras por presión en UCI",
        pmids
    )
    
    print(f"\n📊 Resultado:")
    print(f"   Términos aprendidos: {resultado['terminos_aprendidos']}")
    print(f"   Total diccionario: {resultado['total_diccionario']}")
