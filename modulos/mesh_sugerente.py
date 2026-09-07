#!/data/data/com.termux/files/usr/bin/python3
"""
MeSH Sugerente: sugiere búsquedas cuando la evidencia es baja.
Integra MeSH + Clasificador de evidencia + PubMed.
"""

from typing import Dict, List


class MeSHSugerente:
    """Sugiere búsquedas MeSH cuando evidencia es baja."""
    
    UMBRAL_EVIDENCIA_BAJA = 3  # Nivel 3-4 = evidencia débil
    
    def __init__(self):
        self.sugerencias = []
    
    def analizar_evidencia(self, nivel: int, terminos: List[str]) -> Dict:
        """
        Si la evidencia es baja, sugiere búsqueda MeSH.
        
        Args:
            nivel: Nivel de evidencia (1-4)
            terminos: Términos clave del documento
        
        Returns:
            {'sugerencia': '...', 'query_mesh': '...', 'accion': 'buscar'}
        """
        if nivel < self.UMBRAL_EVIDENCIA_BAJA:
            return {
                'accion': 'evidencia_suficiente',
                'mensaje': f'Nivel {nivel}: evidencia adecuada'
            }
        
        # Evidencia baja: construir query MeSH
        from modulos.mesh_mapper import MeSHMapper
        
        mapper = MeSHMapper()
        frase = ' '.join(terminos[:3])
        query = mapper.construir_query(frase)
        
        sugerencia = {
            'accion': 'buscar',
            'mensaje': f'Nivel {nivel}: evidencia baja. Buscar meta-análisis.',
            'query_mesh': query['query'],
            'terminos_sugeridos': terminos[:3]
        }
        
        self.sugerencias.append(sugerencia)
        return sugerencia
    
    def sugerir_para_documento(self, analisis: Dict) -> Dict:
        """
        Analiza un documento completo y sugiere si es necesario.
        """
        nivel = analisis.get('nivel_evidencia', 4)
        terminos = analisis.get('terminos_clave', [])
        
        return self.analizar_evidencia(nivel, terminos)


if __name__ == '__main__':
    sugerente = MeSHSugerente()
    
    # Test: evidencia baja
    resultado = sugerente.analizar_evidencia(
        nivel=3,
        terminos=['úlceras por presión', 'UCI', 'prevención']
    )
    
    print("🧠 MESH SUGERENTE")
    print("=" * 50)
    print(f"\nAcción: {resultado['accion']}")
    print(f"Mensaje: {resultado['mensaje']}")
    print(f"Query: {resultado['query_mesh']}")
    
    # Test: evidencia alta
    resultado2 = sugerente.analizar_evidencia(
        nivel=1,
        terminos=['úlceras por presión']
    )
    print(f"\nAcción: {resultado2['accion']}")
    print(f"Mensaje: {resultado2['mensaje']}")
