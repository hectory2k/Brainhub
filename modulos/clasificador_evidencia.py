#!/data/data/com.termux/files/usr/bin/python3
"""
Clasificador de evidencia para BrainHub.
Clasifica artículos por nivel de evidencia científica.
"""

from typing import Dict, List


class ClasificadorEvidencia:
    """Clasifica artículos por nivel de evidencia."""
    
    # Reglas de clasificación
    REGLAS_NIVEL = [
        {
            'nivel': 1,
            'tipos': ['Meta-Analysis', 'Systematic Review'],
            'descripcion': 'Máxima evidencia'
        },
        {
            'nivel': 2,
            'tipos': ['Randomized Controlled Trial', 'Clinical Trial'],
            'descripcion': 'Evidencia alta'
        },
        {
            'nivel': 3,
            'tipos': ['Observational Study', 'Review'],
            'descripcion': 'Evidencia moderada'
        },
        {
            'nivel': 4,
            'tipos': ['Editorial', 'Opinion', 'Comment'],
            'descripcion': 'Evidencia baja'
        }
    ]
    
    def clasificar(self, publication_types: List[str]) -> Dict:
        """
        Clasifica por nivel de evidencia.
        
        Args:
            publication_types: Lista de tipos de publicación
            
        Returns:
            {'nivel': 1, 'descripcion': 'Máxima evidencia'}
        """
        publication_types = [pt.lower() for pt in publication_types]
        
        for regla in self.REGLAS_NIVEL:
            for tipo in regla['tipos']:
                if tipo.lower() in ' '.join(publication_types):
                    return {
                        'nivel': regla['nivel'],
                        'descripcion': regla['descripcion']
                    }
        
        return {
            'nivel': 4,
            'descripcion': 'Opinión/Editorial (sin clasificar)'
        }
    
    def clasificar_articulo(self, articulo: Dict) -> Dict:
        """
        Clasifica un artículo completo.
        
        Args:
            articulo: {'titulo': '...', 'publication_types': [...]}
        """
        nivel = self.clasificar(articulo.get('publication_types', []))
        articulo['nivel_evidencia'] = nivel['nivel']
        articulo['descripcion_evidencia'] = nivel['descripcion']
        return articulo
    
    def ordenar_por_evidencia(self, articulos: List[Dict]) -> List[Dict]:
        """Ordena por nivel (mayor primero) y luego por fecha."""
        return sorted(
            articulos,
            key=lambda x: (
                x.get('nivel_evidencia', 4),
                x.get('fecha_publicacion', '0000-00-00')
            )
        )


if __name__ == '__main__':
    clasificador = ClasificadorEvidencia()
    
    # Test con diferentes tipos
    tests = [
        {'titulo': 'Meta-análisis de úlceras', 'publication_types': ['Meta-Analysis']},
        {'titulo': 'Ensayo clínico aleatorizado', 'publication_types': ['Randomized Controlled Trial']},
        {'titulo': 'Estudio observacional', 'publication_types': ['Observational Study']},
        {'titulo': 'Editorial de opinión', 'publication_types': ['Editorial']}
    ]
    
    print("🔬 CLASIFICACIÓN DE EVIDENCIA")
    print("=" * 50)
    
    clasificados = [clasificador.clasificar_articulo(t) for t in tests]
    ordenados = clasificador.ordenar_por_evidencia(clasificados)
    
    for art in ordenados:
        print(f"\n   Nivel {art['nivel_evidencia']}: {art['titulo']}")
        print(f"   → {art['descripcion_evidencia']}")
