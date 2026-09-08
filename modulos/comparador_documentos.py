#!/data/data/com.termux/files/usr/bin/python3
"""Comparador de documentos para BrainHub."""

from typing import Dict, List
import json


class ComparadorDocumentos:
    """Compara dos documentos analizados."""
    
    def comparar(self, doc1: Dict, doc2: Dict) -> Dict:
        """
        Compara dos análisis.
        
        Returns:
            {'comunes': [...], 'solo_doc1': [...], 'solo_doc2': [...]}
        """
        terminos1 = set(t[0] for t in doc1.get('terminos_clave', []))
        terminos2 = set(t[0] for t in doc2.get('terminos_clave', []))
        
        comunes = terminos1 & terminos2
        solo_doc1 = terminos1 - terminos2
        solo_doc2 = terminos2 - terminos1
        
        return {
            'doc1_nicho': doc1.get('nicho', 'GENERAL'),
            'doc2_nicho': doc2.get('nicho', 'GENERAL'),
            'comunes': sorted(comunes),
            'solo_doc1': sorted(solo_doc1),
            'solo_doc2': sorted(solo_doc2),
            'total_doc1': len(terminos1),
            'total_doc2': len(terminos2)
        }


if __name__ == '__main__':
    comparador = ComparadorDocumentos()
    
    # Test
    doc1 = {'nicho': 'EDUCACION', 'terminos_clave': [('educacion', 10), ('matematica', 8)]}
    doc2 = {'nicho': 'EDUCACION', 'terminos_clave': [('educacion', 12), ('lectura', 7)]}
    
    resultado = comparador.comparar(doc1, doc2)
    print("📊 COMPARACIÓN")
    print(f"Comunes: {resultado['comunes']}")
    print(f"Solo doc1: {resultado['solo_doc1']}")
    print(f"Solo doc2: {resultado['solo_doc2']}")
