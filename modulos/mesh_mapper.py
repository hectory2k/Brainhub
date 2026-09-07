#!/data/data/com.termux/files/usr/bin/python3
"""
Mapeo de lenguaje natural → MeSH para BrainHub.
Traduce frases clínicas a queries booleanas de PubMed.
"""

import json
import os
from typing import List, Dict, Optional


class MeSHMapper:
    """Traduce lenguaje natural a descriptores MeSH."""
    
    # Mapeo local de términos comunes → MeSH
    MESH_LOCAL = {
        'úlceras por presión': 'Pressure Ulcer',
        'ulceras por presion': 'Pressure Ulcer',
        'úlcera por presión': 'Pressure Ulcer',
        'ulcera por presion': 'Pressure Ulcer',
        'pacientes encamados': 'Bedridden Persons',
        'úlceras por presión': 'Pressure Ulcer',
        'ulceras por presion': 'Pressure Ulcer',
        'uci': 'Intensive Care Units',
        'encamados': 'Bedridden Persons',
        'pacientes': 'Patients',
        'tratamiento': 'therapy',
        'diagnóstico': 'diagnosis',
        'diagnostico': 'diagnosis',
        'cirugía': 'surgery',
        'cirugia': 'surgery',
        'cáncer': 'Neoplasms',
        'cancer': 'Neoplasms',
        'diabetes': 'Diabetes Mellitus',
        'hipertensión': 'Hypertension',
        'hipertension': 'Hypertension'
    }
    
    # Subheadings comunes
    SUBHEADINGS = {
        'tratamiento': 'therapy',
        'diagnóstico': 'diagnosis',
        'diagnostico': 'diagnosis',
        'cirugía': 'surgery',
        'cirugia': 'surgery'
    }
    
    def tokenizar(self, frase: str) -> List[str]:
        """Tokeniza frase en conceptos clave, manteniendo frases compuestas."""
        frase_lower = frase.lower()
        
        # Buscar frases compuestas primero
        frases_compuestas = [
            'úlceras por presión', 'ulceras por presion',
            'úlcera por presión', 'ulcera por presion',
            'pacientes encamados', 'unidad de cuidados intensivos'
        ]
        
        conceptos = []
        for compuesta in frases_compuestas:
            if compuesta in frase_lower:
                conceptos.append(compuesta)
                frase_lower = frase_lower.replace(compuesta, '')
        
        # Tokenizar el resto
        conectores = ['en', 'de', 'para', 'con', 'por', 'y', 'o', 'a']
        tokens = frase_lower.split()
        concepto_actual = []
        
        for token in tokens:
            if token in conectores:
                if concepto_actual:
                    conceptos.append(' '.join(concepto_actual))
                    concepto_actual = []
            else:
                concepto_actual.append(token)
        
        if concepto_actual:
            conceptos.append(' '.join(concepto_actual))
        
        return conceptos
    
    def buscar_mesh(self, concepto: str) -> Optional[str]:
        """Busca el término MeSH oficial."""
        concepto_norm = concepto.lower().strip()
        
        # Buscar en mapeo local
        if concepto_norm in self.MESH_LOCAL:
            return self.MESH_LOCAL[concepto_norm]
        
        # Si no existe, usar el término como está (sin subheadings por ahora)
        return concepto_norm.title()
    
    def construir_query(self, frase: str) -> Dict:
        """Construye query booleana desde frase clínica."""
        conceptos = self.tokenizar(frase)
        terminos_mesh = []
        
        for concepto in conceptos:
            termino_mesh = self.buscar_mesh(concepto)
            # Solo incluir si está en el diccionario (no términos crudos en español)
            if termino_mesh and termino_mesh in self.MESH_LOCAL.values():
                terminos_mesh.append(f'"{termino_mesh}"[MeSH]')
        
        query = ' AND '.join(terminos_mesh)
        
        return {
            'query': query,
            'conceptos': [
                {'original': c, 'mesh': self.buscar_mesh(c)}
                for c in conceptos
            ],
            'validada': len(terminos_mesh) > 0
        }
    
    def validar_query(self, query: str) -> bool:
        """Valida que la query esté bien formada."""
        if not query:
            return False
        
        # Verificar que tenga al menos un [MeSH]
        if '[MeSH]' not in query:
            return False
        
        # Verificar operadores booleanos
        if ' AND ' not in query:
            return False
        
        return True


if __name__ == '__main__':
    mapper = MeSHMapper()
    
    frase = "prevención de úlceras por presión en pacientes encamados de UCI"
    
    resultado = mapper.construir_query(frase)
    
    print("📋 MAPEO MeSH")
    print("=" * 50)
    print(f"\nFrase: {frase}")
    print(f"\nConceptos:")
    for c in resultado['conceptos']:
        print(f"   {c['original']} → {c['mesh']}")
    
    print(f"\nQuery: {resultado['query']}")
    print(f"Validada: {resultado['validada']}")
